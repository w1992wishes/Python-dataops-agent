"""
表结构生成Agent
使用LangGraph固定工作流，返回包含message字段的结构化结果
"""
from typing import Dict, Any, Optional
import traceback
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models.core.table import TableOperationResult, TableInfo, TableRequestAnalysis, LevelType, TableType, TableProp, Column, ColProp, DataType, ColType
from tools import query_table, get_metric_domains
from tools.metric_tools import query_metric_by_name_zh
from config.table_prompts import TABLE_REQUEST_ANALYSIS_PROMPT, TABLE_STRUCTURE_PROMPT
from config.logging_config import get_logger
from typing import List
from langchain_core.output_parsers import PydanticOutputParser
import asyncio
import json
import traceback


def create_table_info_safe(data: Dict[str, Any]) -> TableInfo:
    """安全创建TableInfo对象，处理缺失字段的情况"""
    if not data:
        # 如果数据为空，返回一个默认的TableInfo
        return TableInfo(
            name="",
            nameZh="",
            businessDomainId="",
            daName="",
            levelType=LevelType.SUB,
            type=TableType.IAT,
            tableProp=TableProp.NORMAL,
            particleSize="",
            itOwner="",
            itGroup="",
            businessOwner="",
            businessGroup="",
            cols=[]
        )

    # 提取所有可能的字段，如果不存在或为None则使用默认值
    return TableInfo(
        id=data.get("id"),
        name=data.get("name") or "unknown_table",
        nameZh=data.get("nameZh") or "未知表",
        businessDomainId=data.get("businessDomainId") or "unknown_domain",
        daName=data.get("daName") or "unknown_db",
        levelType=data.get("levelType") or LevelType.SUB,
        type=data.get("type") or TableType.IAT,
        tableProp=data.get("tableProp") or TableProp.NORMAL,
        particleSize=data.get("particleSize") or "unknown",
        itOwner=data.get("itOwner") or "system",
        itGroup=data.get("itGroup") or "system",
        businessOwner=data.get("businessOwner") or "待指定",
        businessGroup=data.get("businessGroup") or "待指定",
        cols=data.get("cols") or []
    )


class TableManagementAgent(BaseAgent):
    """表管理Agent - 使用LangGraph固定工作流"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger = get_logger("table_agent")
        self._logger.info("📊 初始化表管理LangGraph Agent...")

        # 创建输出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=TableRequestAnalysis)
        self.table_parser = PydanticOutputParser(pydantic_object=TableInfo)

        # 创建LangGraph工作流
        self.graph = self._create_workflow()
        self._logger.info("✅ 表管理LangGraph Agent初始化完成")

    def _create_workflow(self):
        """创建LangGraph固定工作流"""
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
            user_input: str
            table_name: Optional[str]  # 表名参数
            operation_type: Optional[str]
            db_name: Optional[str]
            metric_name_zh_list: List[str]
            table_purpose: str
            existing_table: Optional[Dict[str, Any]]
            metric_ids: List[str]
            final_table_info: Optional[TableInfo]
            final_result: Optional[TableOperationResult]
            success: bool

        workflow = StateGraph(AgentState)

        # 添加节点
        # 添加节点 - 四步工作流：解析输入→查询表→查询指标→生成表
        workflow.add_node("parse_input", self._parse_input)
        workflow.add_node("query_table", self._query_table)
        workflow.add_node("query_metrics", self._query_metrics)
        workflow.add_node("generate_table", self._generate_table)

        # 添加边
        workflow.add_edge(START, "parse_input")
        workflow.add_edge("parse_input", "query_table")
        workflow.add_edge("query_table", "query_metrics")
        workflow.add_edge("query_metrics", "generate_table")
        workflow.add_edge("generate_table", END)

        return workflow.compile()

    async def _parse_input(self, state) -> Dict[str, Any]:
        """解析用户输入，提取表请求关键信息"""
        user_input = state["user_input"]
        self._logger.info("🔍 第1步：解析用户输入")

        prompt = ChatPromptTemplate.from_template(TABLE_REQUEST_ANALYSIS_PROMPT)

        try:
            # 调用大模型解析输入
            chain = prompt | self.llm | self.analysis_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "format_instructions": self.analysis_parser.get_format_instructions()
            })

            parsed_data = result.dict()

            # 更新状态
            state["operation_type"] = parsed_data.get("operation_type", "create")
            state["db_name"] = parsed_data.get("db_name")
            state["table_name"] = parsed_data.get("table_name") or state.get("table_name")
            state["metric_name_zh_list"] = parsed_data.get("metric_name_zh_list", [])
            state["table_purpose"] = parsed_data.get("table_purpose", "")

            self._logger.info(f"✅ 解析成功 - 操作类型: {state['operation_type']}")
            self._logger.info(f"📊 识别指标数: {len(state['metric_name_zh_list'])}")

        except Exception as e:
            self._logger.error(f"❌ 解析失败: {str(e)}")
            self._logger.error(f"❌ 解析异常链路: {traceback.format_exc()}")
            # 异常时设置默认值
            state.update({
                "operation_type": "create",
                "db_name": None,
                "table_name": state.get("table_name"),
                "metric_name_zh_list": [],
                "table_purpose": ""
            })

        return state

    async def _query_table(self, state) -> Dict[str, Any]:
        """查询已存在的表信息"""
        table_name = state.get("table_name")
        self._logger.info("📦 第2步：查询已存在表")

        if table_name:
            try:
                result = await query_table(table_name)
                state["existing_table"] = result
                msg = f"✅ 找到表: {result.get('nameZh', 'N/A')}" if result else "ℹ️ 未找到表，将新建"
                self._logger.info(msg)
            except Exception as e:
                self._logger.error(f"❌ 查询表失败: {str(e)}")
                self._logger.error(f"❌ 查询表异常链路: {traceback.format_exc()}")
                state["existing_table"] = None
        else:
            self._logger.info("⚠️ 缺少表名，跳过查询")
            state["existing_table"] = None

        return state

    async def _query_metrics(self, state) -> Dict[str, Any]:
        """并行查询关联指标ID"""
        metric_name_zh_list = state.get("metric_name_zh_list", [])
        metric_ids = []
        self._logger.info("📊 第3步：查询关联指标")
        self._logger.info(f"🔍 待查指标: {metric_name_zh_list}")

        if metric_name_zh_list:
            # 构建并行查询任务
            tasks = []
            for name in metric_name_zh_list:
                if name.strip():
                    # query_metric_by_name_zh需要user_um参数，我们用默认值
                    tasks.append(query_metric_by_name_zh(name.strip(), "system"))

            if tasks:
                self._logger.info(f"🚀 并行查询 {len(tasks)} 个指标")
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for idx, result in enumerate(results):
                        name = metric_name_zh_list[idx].strip()
                        if isinstance(result, dict) and result:
                            metric_ids.append(result.get("id", ""))
                            self._logger.info(f"✅ 找到指标: {name}")
                        elif isinstance(result, Exception):
                            self._logger.warning(f"⚠️ 指标查询异常: {name}")
                        else:
                            self._logger.info(f"🔍 未找到指标: {name}")
                except Exception as e:
                    self._logger.error(f"❌ 指标查询失败: {str(e)}")
                    self._logger.error(f"❌ 指标查询异常链路: {traceback.format_exc()}")

        # 构建格式化的指标信息键值对
            metrics_info = ""
            for i, name in enumerate(metric_name_zh_list):
                metric_id = metric_ids[i] if i < len(metric_ids) else "N/A"
                if metrics_info:
                    metrics_info += "; "
                metrics_info += f"{name}:{metric_id}"

            state["metric_ids"] = metric_ids
            state["metrics_info"] = metrics_info
            self._logger.info(f"📊 共找到指标数: {len(metric_ids)}")
            if metrics_info:
                self._logger.info(f"📋 指标信息: {metrics_info}")

        return state

    async def _generate_table(self, state) -> Dict[str, Any]:
        """生成最终表结构信息"""
        user_input = state["user_input"]
        operation_type = state.get("operation_type", "create")
        existing_table = state.get("existing_table")
        table_purpose = state.get("table_purpose", "")
        metrics_info = state.get("metrics_info", "")
        self._logger.info("📝 第4步：生成表结构")

        try:
            # 获取业务域信息
            domains = get_metric_domains()
            domains_text = "\n".join([f"- {domain.get('id', '')}: {domain.get('nameZh', '')}" for domain in domains]) if domains else "无可用业务域"

            # 构建现有表信息
            existing_info = f"已存在表信息：\n{json.dumps(existing_table, ensure_ascii=False, indent=2)}" if existing_table else "无已存在表"

            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_template(TABLE_STRUCTURE_PROMPT)

            chain = prompt | self.llm | self.table_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "table_purpose": table_purpose,
                "operation_type": operation_type,
                "existing_info": existing_info,
                "metrics_info": metrics_info,
                "domains_text": domains_text,
                "format_instructions": self.table_parser.get_format_instructions()
            })

            table_info = result
            state["final_table_info"] = table_info

            # 生成操作结果
            if operation_type == "create" and existing_table:
                # 表已存在
                final_result = TableOperationResult(
                    operation_type="create",
                    status="exist",
                    message=f"表 '{existing_table.get('nameZh', 'N/A')}' 已存在，无需重复创建",
                    table_info=None,
                    existing_table=await create_table_info_safe(existing_table)
                )
            elif operation_type == "update" and not existing_table:
                # 表不存在
                final_result = TableOperationResult(
                    operation_type="update",
                    status="not_exist",
                    message=f"表 '{table_info.nameZh}' 不存在，无法修改",
                    table_info=None,
                    existing_table=None
                )
            else:
                # 成功
                final_result = TableOperationResult(
                    operation_type=operation_type,
                    status="success",
                    message=f"表 '{table_info.nameZh}' {operation_type}成功",
                    table_info=table_info,
                    existing_table=await create_table_info_safe(existing_table) if existing_table else None
                )

            state["final_result"] = final_result
            state["success"] = True

            self._logger.info(f"✅ 表生成成功 - 表名: {table_info.nameZh}")
            self._logger.info(f"📊 字段数: {len(table_info.cols)}")

        except Exception as e:
            self._logger.error(f"❌ 表生成失败: {str(e)}")
            self._logger.error(f"❌ 表生成异常链路: {traceback.format_exc()}")
            state["final_table_info"] = None
            state["final_result"] = TableOperationResult(
                operation_type=operation_type,
                status="error",
                message=f"表生成失败: {str(e)}",
                table_info=None,
                existing_table=None
            )
            state["success"] = False

        return state

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法"""
        self._logger.info("🚀 启动表生成工作流")

        table_name = kwargs.get("table_name")
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "table_name": table_name,
            "operation_type": None,
            "db_name": None,
            "metric_name_zh_list": [],
            "table_purpose": "",
            "existing_table": None,
            "metric_ids": [],
            "final_table_info": None,
            "final_result": None,
            "success": False
        }

        try:
            result = await self.graph.ainvoke(initial_state)

            if result.get("success"):
                final_result = result.get("final_result")
                table_info = result.get("final_table_info")

                if final_result and final_result.status == "success":
                    self._logger.info(f"✅ 工作流执行成功: {final_result.operation_type}")
                    return AgentResponse(
                        success=True,
                        data={
                            "operation_result": final_result.model_dump(),
                            "table_info": table_info.model_dump() if table_info else None,
                            "analysis": {}
                        }
                    )
                else:
                    return AgentResponse(
                        success=False,
                        error=final_result.message if final_result else "表操作失败"
                    )
            else:
                return AgentResponse(
                    success=False,
                    error="工作流执行失败"
                )

        except Exception as e:
            self._logger.error(f"❌ 工作流异常: {str(e)}")
            self._logger.error(f"❌ 工作流异常链路: {traceback.format_exc()}")
            return AgentResponse(
                success=False,
                error=f"表生成异常: {str(e)}"
            )


# 注册TableManagementAgent
from .registry import get_registry

def register_table_agent():
    """注册表管理Agent"""
    registry = get_registry()

    default_table_config = AgentConfig(
        name="table_management",
        version="3.0.0",
        description="表管理Agent，提供基于LangGraph的表创建、更新和查询功能",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(TableManagementAgent)

    registry.register("table_generation", factory, default_table_config, {
        "category": "data_modeling",
        "capabilities": ["table_creation", "table_update", "table_query", "schema_design"],
        "agent_type": "langgraph_workflow"
    })