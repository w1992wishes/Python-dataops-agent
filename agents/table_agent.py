"""
表结构生成Agent - 极简版本
超简化流程：解析请求 → 查询表 → 查询指标 → 生成表信息 → 结束
"""
from typing import Dict, List, Any, Optional
import asyncio
import json
import re
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models import TableInfo
from tools import query_table, query_metric_by_name_zh


# LLM输出解析模型
class TableRequestAnalysisModel(BaseModel):
    """表请求分析结果模型"""
    operation_type: str = Field(
        description="操作类型：create/update/query，根据用户意图判断",
        examples=["create", "update", "query"]
    )
    db_name: Optional[str] = Field(default=None, description="数据库名，如果用户明确指定")
    table_name: Optional[str] = Field(default=None, description="表名，如果用户明确指定")
    metric_name_zh_list: List[str] = Field(default_factory=list, description="指标中文名称列表，从用户描述中提取的指标词汇")
    table_purpose: str = Field(default="", description="表的用途和业务场景描述")

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation_type": "create",
                "db_name": "warehouse",
                "table_name": "user_order_fact",
                "metric_name_zh_list": ["订单金额", "用户活跃度", "转化率"],
                "table_purpose": "用户订单事实表，包含订单相关指标和用户维度信息"
            }
        }
    }


class TableGenerationAgent(BaseAgent):
    """表结构生成Agent - 极简版本"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("📊 初始化表结构生成Agent...")

        # 初始化工具
        self.query_table_tool = query_table
        self.query_metric_tool = query_metric_by_name_zh

        # 创建输出解析器
        self.input_parser = PydanticOutputParser(pydantic_object=TableRequestAnalysisModel)
        self.table_parser = PydanticOutputParser(pydantic_object=TableInfo)

        # 创建工作流
        self.graph = self._create_workflow()
        self._logger.info("✅ 表结构生成Agent初始化完成")

    def _create_workflow(self):
        """创建极简的表生成工作流"""
        from langgraph.graph import StateGraph, START, END
        from typing_extensions import TypedDict

        class AgentState(TypedDict):
            messages: List[Any]
            user_input: str
            operation_type: str
            db_name: Optional[str]
            table_name: Optional[str]
            metric_name_zh_list: List[str]
            table_purpose: str
            existing_table: Optional[Dict[str, Any]]
            metric_ids: List[str]
            final_table_info: Optional[Dict[str, Any]]
            error_message: Optional[str]

        workflow = StateGraph(AgentState)

        # 添加节点 - 极简化为4个步骤
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
        """解析用户输入"""
        user_input = state["user_input"]
        self._logger.info("🔍 第1步: 解析用户输入")

        prompt = ChatPromptTemplate.from_template("""
        你是一个数据架构师，请从用户的表结构描述中提取关键信息。

        用户描述：{user_input}

        请仔细分析用户描述，提取以下信息：
        1. operation_type: 操作类型（create/update/query），根据用户意图判断
           - 包含"创建"、"新建"、"生成"、"建立一个"等词汇 → create
           - 包含"修改"、"更新"、"变更"、"调整"等词汇 → update
           - 包含"查询"、"查看"、"搜索"、"找一下"、"获取"等词汇 → query
        2. db_name: 如果用户明确提到了数据库名称，请提取；如果没有明确指定则为null
        3. table_name: 如果用户明确提到了表名，请提取；如果没有明确指定则为null
        4. metric_name_zh_list: 从用户描述中识别出所有与指标相关的中文名称，形成一个列表
        5. table_purpose: 根据用户描述，总结这个表的用途和业务场景

        注意事项：
        - 操作类型要根据用户的明确意图判断，这是后续处理的关键
        - 只有在用户非常明确地指定数据库名和表名时才提取，不要凭空推测
        - 指标列表要尽可能完整，包括所有可能相关的指标词汇
        - 表用途要简洁明了，说明表的核心作用

        {format_instructions}
        """)

        try:
            chain = prompt | self.llm | self.input_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "format_instructions": self.input_parser.get_format_instructions()
            })

            # 转换为字典格式
            parsed_data = result.dict()

            # 智能操作类型映射（类似 metric_agent）
            operation_map = {
                "创建": "create", "新建": "create", "生成": "create", "建立一个": "create",
                "修改": "update", "更新": "update", "变更": "update", "调整": "update",
                "查询": "query", "查看": "query", "搜索": "query", "找一下": "query", "获取": "query"
            }

            operation_text = parsed_data.get("operation_type", "create")
            operation_type = operation_map.get(operation_text, "create")

            state["operation_type"] = operation_type
            state["db_name"] = parsed_data.get("db_name")
            state["table_name"] = parsed_data.get("table_name")
            state["metric_name_zh_list"] = parsed_data.get("metric_name_zh_list", [])
            state["table_purpose"] = parsed_data.get("table_purpose", "")

            self._logger.info(f"✅ 解析成功 - 操作类型: {operation_type}, 数据库: {state['db_name']}, 表: {state['table_name']}")
            self._logger.info(f"📊 识别到指标数量: {len(state['metric_name_zh_list'])}")
            self._logger.info(f"🎯 指标列表: {state['metric_name_zh_list']}")
            self._logger.info(f"📝 表用途: {state['table_purpose']}")

        except Exception as e:
            self._logger.error(f"❌ 解析输入失败: {e}")
            state["operation_type"] = "create"  # 默认操作类型
            state["db_name"] = None
            state["table_name"] = None
            state["metric_name_zh_list"] = []
            state["table_purpose"] = ""

        return state

    async def _query_table(self, state) -> Dict[str, Any]:
        """查询已存在的表信息"""
        db_name = state.get("db_name")
        table_name = state.get("table_name")

        self._logger.info("📋 第2步: 查询已存在的表信息")

        if db_name and table_name:
            try:
                result = await self.query_table_tool(db_name, table_name)
                state["existing_table"] = result

                if result:
                    self._logger.info(f"✅ 找到已存在的表: {result.get('nameZh', 'N/A')}")
                else:
                    self._logger.info("ℹ️ 未找到已存在的表，将创建新表")

            except Exception as e:
                self._logger.error(f"❌ 查询表信息失败: {e}")
                state["existing_table"] = None
        else:
            self._logger.info("⚠️ 缺少数据库名或表名，跳过查询")
            state["existing_table"] = None

        return state

    async def _query_metrics(self, state) -> Dict[str, Any]:
        """查询关联的指标"""
        metric_name_zh_list = state.get("metric_name_zh_list", [])
        metric_ids = []

        self._logger.info("📈 第3步: 查询关联指标")
        self._logger.info(f"🎯 待查询指标列表: {metric_name_zh_list}")

        # 优先使用解析出的指标中文名称列表进行查询
        if metric_name_zh_list:
            # 创建并行查询任务
            metric_query_tasks = []

            for metric_name_zh in metric_name_zh_list:
                if metric_name_zh.strip():
                    metric_query_tasks.append(self.query_metric_tool(metric_name_zh.strip()))

            # 并行查询所有指标
            if metric_query_tasks:
                self._logger.info(f"🚀 并行查询 {len(metric_query_tasks)} 个指标...")
                try:
                    results = await asyncio.gather(*metric_query_tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        metric_name_zh = metric_name_zh_list[i].strip()
                        if isinstance(result, dict) and result:  # 找到指标
                            metric_ids.append(result.get("id"))
                            self._logger.info(f"✅ 找到指标: {metric_name_zh} -> {result.get('nameZh', 'N/A')} ({result.get('id', 'N/A')})")
                        elif isinstance(result, Exception):
                            self._logger.warning(f"⚠️ 指标查询异常: {metric_name_zh} -> {result}")
                        else:
                            self._logger.info(f"ℹ️ 未找到指标: {metric_name_zh}")

                except Exception as e:
                    self._logger.error(f"❌ 并行查询指标失败: {e}")

        state["metric_ids"] = metric_ids
        self._logger.info(f"📊 总共找到指标数量: {len(metric_ids)}")

        return state

    async def _generate_table(self, state) -> Dict[str, Any]:
        """生成用户需求的表信息"""
        user_input = state["user_input"]
        existing_table = state.get("existing_table")
        table_purpose = state.get("table_purpose", "")
        metric_name_zh_list = state.get("metric_name_zh_list", [])
        metric_ids = state.get("metric_ids", [])

        self._logger.info("🏗️ 第4步: 生成用户需求的表信息")

        try:
            # 构建现有表信息
            existing_info = ""
            if existing_table:
                self._logger.info(f"📋 发现已存在表: {existing_table.get('nameZh', 'N/A')}")
                existing_info = f"""
                已存在的表信息如下，请在此基础上进行更新和补充：
                {json.dumps(existing_table, ensure_ascii=False, indent=2)}
                """

            # 构建指标信息
            metrics_info = ""
            if metric_name_zh_list:
                metrics_info = f"""
                用户描述中提到的指标包括：{', '.join(metric_name_zh_list)}
                找到的指标ID：{', '.join(metric_ids) if metric_ids else '无'}
                请在表字段设计中为这些指标创建对应的字段（如果适用）。
                """

            prompt = ChatPromptTemplate.from_template("""
            你是一个专业的数据架构师，需要根据用户描述生成符合规范的完整表信息。

            用户需求：{user_input}

            表的用途和业务场景：{table_purpose}

            已存在表信息：
            {existing_info}

            相关指标信息：
            {metrics_info}

            重要注意事项：
            - 如果是创建新表，所有字段的 tableId 应该设置为空字符串 ""
            - 如果是更新现有表，请保留原有字段的 tableId 或根据需要设置
            - 字段的 colProp 可以是 "DIM"（维度）、"METRIC"（指标）或 "NORMAL"（普通）
            - 字段的 dataType 可以是 "string"、"date" 或 "float"
            - 字段的 colType 通常是 0（普通字段）或 2（分区键）

            请生成包含以下信息的表结构：
            {format_instructions}
            """)

            chain = prompt | self.llm | self.table_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "table_purpose": table_purpose,
                "existing_info": existing_info,
                "metrics_info": metrics_info,
                "format_instructions": self.table_parser.get_format_instructions()
            })

            # 转换为字典格式
            table_data = result.dict()
            state["final_table_info"] = table_data

            table_name = table_data.get('name', 'N/A')
            table_name_zh = table_data.get('nameZh', 'N/A')
            cols_count = len(table_data.get('cols', []))
            self._logger.info(f"✅ 表信息生成成功")
            self._logger.info(f"📊 表名: {table_name} ({table_name_zh})")
            self._logger.info(f"📋 字段数量: {cols_count}")

        except Exception as e:
            self._logger.error(f"❌ 生成表信息失败: {e}")
            state["final_table_info"] = None

        return state

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法"""
        self._logger.info("🚀 开始执行表生成工作流")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "operation_type": "create",  # 默认操作类型
            "db_name": None,
            "table_name": None,
            "metric_name_zh_list": [],
            "table_purpose": "",
            "existing_table": None,
            "metric_ids": [],
            "final_table_info": None,
            "error_message": None
        }

        try:
            result = await self.graph.ainvoke(initial_state)

            table_info = result.get("final_table_info")
            operation_type = result.get("operation_type", "create")

            if table_info:
                table_name = table_info.get('name', 'N/A')
                table_name_zh = table_info.get('nameZh', 'N/A')
                self._logger.info(f"🎉 表生成工作流执行成功!")
                self._logger.info(f"📊 生成表名: {table_name} ({table_name_zh})")
                self._logger.info(f"🔄 操作类型: {operation_type}")

                return AgentResponse(
                    success=True,
                    data={
                        "table_info": table_info,
                        "analysis": {"operation_type": operation_type}
                    }
                )
            else:
                return AgentResponse(
                    success=False,
                    error="表生成失败"
                )

        except Exception as e:
            self._logger.error(f"💥 表生成工作流出现异常: {e}")
            return AgentResponse(
                success=False,
                error=f"表生成异常: {str(e)}"
            )


# 注册TableGenerationAgent
from .registry import get_registry
from .base_agent import AgentConfig

def register_table_agent():
    """注册表结构生成Agent"""
    registry = get_registry()

    default_table_config = AgentConfig(
        name="table_generation",
        version="3.0.0",
        description="智能表结构生成Agent - 根据自然语言描述生成数据库表结构",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(TableGenerationAgent)

    registry.register("table_generation", factory, default_table_config, {
        "category": "data_modeling",
        "capabilities": ["table_generation", "schema_design"]
    })