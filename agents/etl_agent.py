"""
ETL开发Agent - 基于DDL变动的智能ETL代码修改
三步工作流：直接参数传递 → 并行工具调用 → LLM生成ETL代码
"""
from typing import Dict, Any, Optional
import traceback
import time
import asyncio
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models.core.etl import ETLOperationResult
from tools.etl_tools import get_etl_script
from tools.table_tools import query_table_ddl
from config.etl_prompts import ETL_MODIFICATION_PROMPT, ETL_CREATION_PROMPT


class ETLManagementAgent(BaseAgent):
    """ETL管理Agent - 三步工作流，高效简洁"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("🔧 初始化ETL管理LangGraph Agent（三步工作流）...")

        # 创建输出解析器
        self.result_parser = PydanticOutputParser(pydantic_object=ETLOperationResult)

        # 创建LangGraph工作流
        self.graph = self._create_workflow()
        self._logger.info("✅ ETL管理LangGraph Agent初始化完成")

    def _create_workflow(self):
        """创建三步LangGraph工作流"""
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
            table_name: str
            user_input: str
            etl_info: Optional[Dict[str, Any]]
            ddl_content: Optional[str]
            final_result: Optional[ETLOperationResult]
            success: bool

        workflow = StateGraph(AgentState)

        # 添加三个节点
        workflow.add_node("query_tools", self._query_tools)
        workflow.add_node("generate_etl", self._generate_etl)

        # 添加边
        workflow.add_edge(START, "query_tools")
        workflow.add_edge("query_tools", "generate_etl")
        workflow.add_edge("generate_etl", END)

        return workflow.compile()

    async def _query_tools(self, state) -> Dict[str, Any]:
        """并行调用工具获取ETL修改所需信息"""
        table_name = state["table_name"]

        self._logger.info(f"🔍 [查询工具节点] 开始并行查询: {table_name}")

        try:
            start_time = time.time()

            # 并行调用两个工具
            etl_task = get_etl_script(table_name)
            ddl_task = query_table_ddl(table_name)

            # 等待两个工具完成
            etl_info, ddl_content = await asyncio.gather(
                etl_task, ddl_task, return_exceptions=True
            )

            # 处理ETL查询结果
            if isinstance(etl_info, dict):
                state["etl_info"] = etl_info
                self._logger.info(f"📊 [查询工具节点] 找到etl脚本")
            elif isinstance(etl_info, Exception):
                self._logger.warning(f"⚠️ [查询工具节点] ETL查询异常: {str(etl_info)}")
                state["etl_info"] = None
            else:
                self._logger.info(f"ℹ️ [查询工具节点] 未找到ETL脚本")
                state["etl_info"] = None

            # 处理DDL内容结果
            if isinstance(ddl_content, str):
                state["ddl_content"] = ddl_content
                self._logger.info(f"✅ [查询工具节点] 获取DDL内容成功: {len(ddl_content)} 字符")
                self._logger.info(f"📋 [查询工具节点] DDL预览: {ddl_content[:100]}...")
            elif isinstance(ddl_content, Exception):
                self._logger.warning(f"⚠️ [查询工具节点] DDL查询异常: {str(ddl_content)}")
                state["ddl_content"] = None
            else:
                self._logger.info(f"ℹ️ [查询工具节点] DDL查询无结果")
                state["ddl_content"] = None

            query_time = time.time() - start_time
            self._logger.info(f"⏱️ [查询工具节点] 工具查询完成，耗时: {query_time:.2f}秒")

        except Exception as e:
            self._logger.error(f"❌ [查询工具节点] 工具查询失败: {str(e)}")
            self._logger.error(f"❌ [查询工具节点] 异常链路: {traceback.format_exc()}")
            state["etl_info"] = None
            state["ddl_content"] = None

        return state

    async def _generate_etl(self, state) -> Dict[str, Any]:
        """使用LLM生成/修改ETL代码"""
        start_time = time.time()
        table_name = state["table_name"]
        user_input = state["user_input"]
        etl_info = state.get("etl_info")
        ddl_content = state.get("ddl_content")

        # 提前判断操作类型，确保在异常处理中也能使用
        operation_type = "update" if etl_info else "create"

        self._logger.info(f"🔄 [生成ETL节点] 开始生成ETL代码")

        try:
            if operation_type == "update":
                # 修改现有ETL代码
                self._logger.info("✏️ [生成ETL节点] 修改现有ETL代码")

                format_instructions = self.result_parser.get_format_instructions()
                prompt = ChatPromptTemplate.from_template(ETL_MODIFICATION_PROMPT)

                chain = prompt | self.llm | self.result_parser
                result = await chain.ainvoke({
                    "user_input": user_input,
                    "table_name": table_name,
                    "operation_type": operation_type,
                    "user_requirements": [user_input],  # 直接使用用户输入作为需求
                    "original_etl_code": etl_info.get("etl_code", ""),
                    "ddl_content": ddl_content or "无DDL信息",
                    "format_instructions": format_instructions
                })

            else:
                # 创建新ETL代码
                self._logger.info("🆕 [生成ETL节点] 创建新ETL代码")

                format_instructions = self.result_parser.get_format_instructions()
                prompt = ChatPromptTemplate.from_template(ETL_CREATION_PROMPT)

                chain = prompt | self.llm | self.result_parser
                result = await chain.ainvoke({
                    "user_input": user_input,
                    "table_name": table_name,
                    "operation_type": operation_type,
                    "user_requirements": [user_input],  # 直接使用用户输入作为需求
                    "ddl_content": ddl_content or "无DDL信息",
                    "format_instructions": format_instructions
                })

            execution_time = time.time() - start_time
            self._logger.info(f"✅ [生成ETL节点] ETL生成完成，耗时: {execution_time:.2f}秒")
            self._logger.info(f"📊 [生成ETL节点] 操作类型: {result.operation_type}, 状态: {result.status}")

            state["final_result"] = result
            state["success"] = True

        except Exception as e:
            self._logger.error(f"❌ [生成ETL节点] ETL生成失败: {str(e)}")
            self._logger.error(f"❌ [生成ETL节点] 异常链路: {traceback.format_exc()}")

            error_result = ETLOperationResult(
                operation_type=operation_type,
                status="error",
                message=f"ETL生成失败: {str(e)}",
                table_name=table_name,
                modified_etl_code=None,
                changes_summary=None
            )
            state["final_result"] = error_result
            state["success"] = False

        return state

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法 - 从kwargs中提取table_name参数"""
        # 从kwargs中提取table_name参数
        table_name = kwargs.get("table_name")
        if not table_name:
            return AgentResponse(
                success=False,
                error="ETL处理缺少必需的table_name参数",
                agent_name=self.name
            )

        self._logger.info("🚀 开始执行ETL管理工作流（三步）")
        self._logger.info(f"📊 目标表: {table_name}")
        self._logger.info(f"📝 用户需求: {user_input}")

        initial_state = {
            "messages": [],
            "table_name": table_name,
            "user_input": user_input,
            "etl_info": None,
            "ddl_content": None,
            "final_result": None,
            "success": False
        }

        try:
            result = await self.graph.ainvoke(initial_state)

            if result.get("success"):
                final_result = result.get("final_result")
                etl_info = result.get("etl_info")

                self._logger.info(f"🎉 ETL管理工作流执行成功!")
                self._logger.info(f"🔄 操作类型: {final_result.operation_type}")
                self._logger.info(f"📊 操作状态: {final_result.status}")
                self._logger.info(f"💬 结果消息: {final_result.message}")

                # 构建完整返回数据
                response_data = {
                    "operation_result": final_result.model_dump()
                }

                # 添加ETL工具查询的完整信息
                if etl_info:
                    response_data["etl_info"] = etl_info
                    self._logger.info(f"📄 ETL信息: rel_id={etl_info.get('rel_id')}, target_table={etl_info.get('target_table')}")

                return AgentResponse(
                    success=True,
                    data=response_data
                )
            else:
                final_result = result.get("final_result")
                return AgentResponse(
                    success=False,
                    error=final_result.message if final_result else "ETL操作失败"
                )

        except Exception as e:
            self._logger.error(f"💥 ETL管理工作流出现异常: {str(e)}")
            self._logger.error(f"💥 ETL管理工作流异常链路: {traceback.format_exc()}")
            return AgentResponse(
                success=False,
                error=f"ETL操作异常: {str(e)}"
            )


# 注册ETLManagementAgent
from .registry import get_registry

def register_etl_agent():
    """注册ETL管理Agent"""
    registry = get_registry()

    default_etl_config = AgentConfig(
        name="etl_management",
        version="3.0.0",
        description="ETL管理Agent，提供基于DDL变动的智能ETL代码修改功能",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(ETLManagementAgent)

    registry.register("etl_management", factory, default_etl_config, {
        "category": "data_engineering",
        "capabilities": ["etl_modification", "ddl_analysis", "code_generation", "intelligent_optimization"],
        "agent_type": "langgraph_workflow"
    })