"""
表结构生成Agent - 参考metric_agent重构
使用LangGraph固定工作流，返回包含message字段的结构化结果
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import traceback
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models.table_schemas import TableOperationResult, TableAnalysisResult
from models import TableInfo
from models.table import LevelType, TableType, TableProp
from tools import query_table, query_metric_by_name_zh, get_metric_domains
from config.table_prompts import TABLE_ANALYSIS_PROMPT


def create_table_info_safe(data: Dict[str, Any]) -> TableInfo:
    """安全创建TableInfo对象，处理缺失字段的情况"""
    if not data:
        # 如果数据为空，返回一个默认的TableInfo
        return TableInfo(
            name="unknown_table",
            nameZh="未知表",
            businessDomainId="unknown_domain",
            daName="unknown_db",
            levelType=LevelType.SUB,
            type=TableType.IAT,
            tableProp=TableProp.NORMAL,
            particleSize="unknown",
            itOwner="system",
            itGroup="system",
            businessOwner="WANQINFENG063",
            businessGroup="待指定",
            cols=[]
        )

    # 提取所有可能的字段，如果不存在则使用默认值
    return TableInfo(
        id=data.get("id"),
        name=data.get("name", "unknown_table"),
        nameZh=data.get("nameZh", "未知表"),
        businessDomainId=data.get("businessDomainId", "unknown_domain"),
        daName=data.get("daName", "unknown_db"),
        levelType=data.get("levelType", LevelType.SUB),
        type=data.get("type", TableType.IAT),
        tableProp=data.get("tableProp", TableProp.NORMAL),
        particleSize=data.get("particleSize", "unknown"),
        itOwner=data.get("itOwner", "system"),
        itGroup=data.get("itGroup", "system"),
        businessOwner=data.get("businessOwner", "待指定"),
        businessGroup=data.get("businessGroup", "待指定"),
        cols=data.get("cols", [])
    )


class TableManagementAgent(BaseAgent):
    """表管理Agent - 使用LangGraph固定工作流"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("📊 初始化表管理LangGraph Agent...")

        # 创建输出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=TableAnalysisResult)

        # 创建LangGraph工作流
        self.graph = self._create_workflow()
        self._logger.info("✅ 表管理LangGraph Agent初始化完成")

    def _create_workflow(self):
        """创建LangGraph固定工作流"""
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
            user_input: str
            analysis_result: Optional[Dict[str, Any]]
            existing_table: Optional[Dict[str, Any]]
            final_result: Optional[TableOperationResult]
            success: bool

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("query_table", self._query_table)
        workflow.add_node("execute_operation", self._execute_operation)

        # 添加边
        workflow.add_edge(START, "analyze_request")
        workflow.add_edge("analyze_request", "query_table")
        workflow.add_edge("query_table", "execute_operation")
        workflow.add_edge("execute_operation", END)

        return workflow.compile()

    async def _analyze_request(self, state) -> Dict[str, Any]:
        """分析用户需求节点 - 直接输出TableAnalysisResult格式"""
        user_input = state["user_input"]
        self._logger.info("🔍 [分析请求节点] 开始分析用户需求")

        try:
            # 获取业务域信息（用于表的数据库选择）
            domains = await get_metric_domains()
            domains_text = "\n".join([f"- {domain.get('id', '')}: {domain.get('nameZh', '')}" for domain in domains]) if domains else "无可用业务域"

            # 使用配置文件中的提示词和格式化指令
            format_instructions = self.analysis_parser.get_format_instructions()
            prompt = ChatPromptTemplate.from_template(TABLE_ANALYSIS_PROMPT)

            chain = prompt | self.llm | self.analysis_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "format_instructions": format_instructions
            })

            self._logger.info(f"✅ [分析请求节点] 分析完成: {result.operation_type} - {result.table_name_zh}")
            state["analysis_result"] = result.model_dump()

        except Exception as e:
            self._logger.error(f"❌ [分析请求节点] 分析失败: {str(e)}")
            self._logger.error(f"❌ [分析请求节点] 异常链路: {traceback.format_exc()}")
            # 提供默认的分析结果
            default_result = TableAnalysisResult(
                operation_type="create",
                table_name_zh="未知表",
                table_purpose=f"基于用户需求分析: {user_input}"
            )
            state["analysis_result"] = default_result.model_dump()

        return state

    async def _query_table(self, state) -> Dict[str, Any]:
        """查询已存在的表信息节点"""
        analysis_data = state.get("analysis_result", {})
        db_name = analysis_data.get("db_name")
        table_name = analysis_data.get("table_name")

        self._logger.info(f"📋 [查询表节点] 查询表信息: {db_name}.{table_name}")

        try:
            if db_name and table_name:
                result = await query_table(db_name, table_name)
                state["existing_table"] = result

                if result:
                    self._logger.info(f"✅ [查询表节点] 找到已存在的表: {result.get('nameZh', 'N/A')}")
                else:
                    self._logger.info("ℹ️ [查询表节点] 未找到已存在的表")
            else:
                self._logger.info("⚠️ [查询表节点] 缺少数据库名或表名，跳过查询")
                state["existing_table"] = None

        except Exception as e:
            self._logger.error(f"❌ [查询表节点] 查询表失败: {str(e)}")
            self._logger.error(f"❌ [查询表节点] 异常链路: {traceback.format_exc()}")
            state["existing_table"] = None

        return state

    async def _execute_operation(self, state) -> Dict[str, Any]:
        """执行表操作节点"""
        user_input = state["user_input"]
        analysis_data = state.get("analysis_result", {})
        existing_table = state.get("existing_table")

        operation_type = analysis_data.get("operation_type", "create")
        table_name_zh = analysis_data.get("table_name_zh", "未知表")
        table_name = analysis_data.get("table_name", "unknown_table")
        db_name = analysis_data.get("db_name", "warehouse")
        table_purpose = analysis_data.get("table_purpose", "")

        self._logger.info(f"🔄 [执行操作节点] 执行表操作 - {operation_type}")

        try:
            # 根据操作类型和查询结果执行相应逻辑
            if operation_type == "create":
                if existing_table:
                    # 表已存在
                    existing_table_info = create_table_info_safe(existing_table)
                    final_result = TableOperationResult(
                        operation_type="create",
                        status="exist",
                        message=f"表 '{existing_table_info.nameZh}' 已存在，无需重复创建。请使用修改操作来更新表结构。",
                        table_info=None,
                        existing_table=existing_table_info
                    )
                else:
                    # 创建新表 - 生成基本的表信息
                    new_table_info = TableInfo(
                        name=table_name or "generated_table",
                        nameZh=table_name_zh,
                        businessDomainId="default_domain",
                        daName=db_name,
                        levelType=LevelType.SUB,
                        type=TableType.IAT,
                        tableProp=TableProp.NORMAL,
                        particleSize="明细",
                        itOwner="system",
                        itGroup="data_team",
                        businessOwner="待指定",
                        businessGroup="待指定",
                        cols=[]  # 实际字段需要根据业务需求生成
                    )

                    final_result = TableOperationResult(
                        operation_type="create",
                        status="success",
                        message=f"表 '{new_table_info.nameZh}' 创建成功！",
                        table_info=new_table_info,
                        existing_table=None
                    )

            elif operation_type == "update":
                if not existing_table:
                    # 表不存在，无法修改
                    final_result = TableOperationResult(
                        operation_type="update",
                        status="not_exist",
                        message=f"表 '{table_name_zh}' 不存在，无法修改。请先创建该表。",
                        table_info=None,
                        existing_table=None
                    )
                else:
                    # 修改已存在的表
                    existing_table_info = create_table_info_safe(existing_table)
                    # 更新表信息
                    if table_name_zh:
                        existing_table_info.nameZh = table_name_zh
                    if table_purpose:
                        existing_table_info.tableComment = f"{existing_table_info.tableComment}。更新需求: {user_input}"

                    final_result = TableOperationResult(
                        operation_type="update",
                        status="success",
                        message=f"表 '{existing_table_info.nameZh}' 更新成功！",
                        table_info=existing_table_info,
                        existing_table=None
                    )

            elif operation_type == "query":
                if not existing_table:
                    # 表不存在
                    final_result = TableOperationResult(
                        operation_type="query",
                        status="not_exist",
                        message=f"表 '{table_name_zh}' 不存在。",
                        table_info=None,
                        existing_table=None
                    )
                else:
                    # 表存在，返回查询结果
                    existing_table_info = create_table_info_safe(existing_table)
                    final_result = TableOperationResult(
                        operation_type="query",
                        status="success",
                        message=f"表 '{existing_table_info.nameZh}' 查询成功！",
                        table_info=existing_table_info,
                        existing_table=existing_table_info
                    )
            else:
                # 未知操作类型
                final_result = TableOperationResult(
                    operation_type="unknown",
                    status="error",
                    message=f"不支持的操作类型: {operation_type}",
                    table_info=None,
                    existing_table=None
                )


            state["final_result"] = final_result
            state["success"] = True
            self._logger.info(f"✅ [执行操作节点] 操作完成: {final_result.status} - {final_result.message}")

        except Exception as e:
            self._logger.error(f"❌ [执行操作节点] 执行表操作失败: {str(e)}")
            self._logger.error(f"❌ [执行操作节点] 异常链路: {traceback.format_exc()}")
            error_result = TableOperationResult(
                operation_type=operation_type,
                status="error",
                message=f"操作执行失败: {str(e)}",
                table_info=None,
                existing_table=None
            )
            state["final_result"] = error_result
            state["success"] = False

        return state

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法"""
        self._logger.info("🚀 开始执行表管理工作流")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "analysis_result": None,
            "existing_table": None,
            "final_result": None,
            "success": False
        }

        try:
            result = await self.graph.ainvoke(initial_state)

            if result.get("success"):
                final_result = result.get("final_result")
                self._logger.info(f"🎉 表管理工作流执行成功!")
                self._logger.info(f"🔄 操作类型: {final_result.operation_type}")
                self._logger.info(f"📊 操作状态: {final_result.status}")
                self._logger.info(f"💬 结果消息: {final_result.message}")

                return AgentResponse(
                    success=True,
                    data={
                        "operation_result": final_result.model_dump(),
                        "analysis": result.get("analysis_result", {})
                    }
                )
            else:
                final_result = result.get("final_result")
                return AgentResponse(
                    success=False,
                    error=final_result.message if final_result else "表操作失败"
                )

        except Exception as e:
            self._logger.error(f"💥 表管理工作流出现异常: {str(e)}")
            self._logger.error(f"💥 表管理工作流异常链路: {traceback.format_exc()}")
            return AgentResponse(
                success=False,
                error=f"表操作异常: {str(e)}"
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

    registry.register("table_management", factory, default_table_config, {
        "category": "data_modeling",
        "capabilities": ["table_creation", "table_update", "table_query", "schema_design"],
        "agent_type": "langgraph_workflow"
    })