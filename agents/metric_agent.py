"""
指标管理Agent - 处理指标的创建、更新和查询
使用LangGraph固定工作流
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
from models.metric_schemas import MetricOperationResult, MetricInfo, MetricAnalysisResult
from tools.metric_tools import (
    query_metric_by_name_zh, get_metric_domains
)
from config.metric_prompts import (
    METRIC_ANALYSIS_PROMPT
)


def create_metric_info_safe(data: Dict[str, Any]) -> MetricInfo:
    """安全创建MetricInfo对象，处理缺失字段的情况"""
    if not data:
        # 如果数据为空，返回一个默认的MetricInfo
        return MetricInfo(
            nameZh="未知指标",
            name="unknown_metric",
            processDomainId="unknown",
            businessInfoMap={}
        )

    # 提取所有可能的字段，如果不存在则使用默认值
    return MetricInfo(
        id=data.get("id"),
        nameZh=data.get("nameZh", "未知指标"),
        name=data.get("name", "unknown_metric"),
        code=data.get("code", ""),
        applicationScenarios=data.get("applicationScenarios", "HIVE_OFFLINE"),
        type=data.get("type", "IA"),
        lv=data.get("lv", "T2"),
        processDomainId=data.get("processDomainId", "unknown"),
        safeLv=data.get("safeLv", "S1"),
        businessCaliberDesc=data.get("businessCaliberDesc", ""),
        businessOwner=data.get("businessOwner", "待指定"),
        businessTeam=data.get("businessTeam", "待指定"),
        statisticalObject=data.get("statisticalObject", "待定义"),
        statisticalRule=data.get("statisticalRule", "待定义"),
        statisticalRuleIt=data.get("statisticalRuleIt", "待定义"),
        statisticalTime=data.get("statisticalTime", "日"),
        unit=data.get("unit", "个"),
        physicalInfoList=data.get("physicalInfoList"),
        businessInfoMap=data.get("businessInfoMap", {})
    )


class MetricManagementAgent(BaseAgent):
    """指标管理Agent - 使用LangGraph固定工作流"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("📊 初始化指标管理LangGraph Agent...")

        # 创建输出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=MetricAnalysisResult)
        self.result_parser = PydanticOutputParser(pydantic_object=MetricOperationResult)

        # 创建LangGraph工作流
        self.graph = self._create_workflow()
        self._logger.info("✅ 指标管理LangGraph Agent初始化完成")

    def _create_workflow(self):
        """创建LangGraph固定工作流"""
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
            user_input: str
            analysis_result: Optional[Dict[str, Any]]
            existing_metric: Optional[Dict[str, Any]]
            final_result: Optional[MetricOperationResult]
            success: bool

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("query_metric", self._query_metric)
        workflow.add_node("execute_operation", self._execute_operation)

        # 添加边 - 固定的执行流程
        workflow.add_edge(START, "analyze_request")
        workflow.add_edge("analyze_request", "query_metric")
        workflow.add_edge("query_metric", "execute_operation")
        workflow.add_edge("execute_operation", END)

        return workflow.compile()

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """使用LangGraph工作流处理用户输入"""
        self._logger.info("📊 开始执行指标管理工作流")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "analysis_result": None,
            "existing_metric": None,
            "final_result": None,
            "success": False
        }

        try:
            result = await self.graph.ainvoke(initial_state)
            final_result = result.get("final_result")
            success = result.get("success", False)

            if success and final_result:
                self._logger.info(f"✅ 工作流执行完成: {final_result.operation_type} - {final_result.status}")
                return AgentResponse(
                    success=True,
                    data={
                        "operation_result": final_result.model_dump(),
                        "agent_reply": final_result.message
                    }
                )
            else:
                self._logger.warning("⚠️ 工作流执行完成但未成功")
                return AgentResponse(
                    success=False,
                    error="工作流执行失败"
                )

        except Exception as e:
            self._logger.error(f"💥 工作流执行异常: {str(e)}")
            self._logger.error(f"💥 工作流执行异常链路: {traceback.format_exc()}")
            return AgentResponse(
                success=False,
                error=f"工作流执行异常: {str(e)}"
            )

    async def process_stream(self, user_input: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """使用LangGraph的流式处理方法"""
        self._logger.info("📊 开始执行指标管理工作流（流式）")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "analysis_result": None,
            "existing_metric": None,
            "final_result": None,
            "success": False
        }

        try:
            # 先发送开始消息
            yield {
                "step": "starting",
                "data": {"user_input": user_input},
                "message": "🔍 开始处理您的指标管理需求...",
                "timestamp": datetime.now().isoformat()
            }

            # 使用LangGraph的流式执行
            async for output in self.graph.astream(initial_state):
                node_name = list(output.keys())[0]
                node_state = output[node_name]

                # 构建流式输出数据
                chunk = {
                    "step": node_name,
                    "data": {
                        "node": node_name,
                        "state_summary": {
                            "has_analysis": node_state.get("analysis_result") is not None,
                            "has_existing_metric": node_state.get("existing_metric") is not None,
                            "has_final_result": node_state.get("final_result") is not None,
                            "success": node_state.get("success", False)
                        }
                    },
                    "message": f"执行步骤: {node_name}"
                }

                # 添加步骤特定的数据
                if node_name == "analyze_request":
                    analysis = node_state.get("analysis_result", {})
                    if analysis:
                        chunk["data"]["analysis"] = analysis
                        chunk["message"] = f"✅ 需求分析完成: {analysis.get('operation_type', 'N/A')} - {analysis.get('metric_name_zh', 'N/A')}"
                    else:
                        chunk["message"] = "📝 正在分析您的需求..."

                elif node_name == "query_metric":
                    existing = node_state.get("existing_metric")
                    if existing:
                        chunk["data"]["existing_metric"] = existing
                        chunk["message"] = f"📋 查询到已存在指标: {existing.get('nameZh', 'N/A')}"
                    else:
                        chunk["message"] = "ℹ️ 未找到已存在指标"

                elif node_name == "execute_operation":
                    final_result = node_state.get("final_result")
                    success = node_state.get("success", False)
                    if final_result and success:
                        chunk["data"]["final_result"] = final_result.model_dump()
                        chunk["message"] = f"🎉 指标处理完成: {final_result.operation_type} - {final_result.status}"
                    else:
                        chunk["message"] = "❌ 指标处理失败"

                chunk["timestamp"] = datetime.now().isoformat()
                yield chunk

            # 发送最终完成消息
            final_chunk = {
                "step": "completed",
                "data": {"workflow_completed": True},
                "message": "✅ 指标管理工作流执行完成",
                "timestamp": datetime.now().isoformat()
            }
            yield final_chunk

        except Exception as e:
            self._logger.error(f"💥 流式执行异常: {str(e)}")
            self._logger.error(f"💥 流式执行异常链路: {traceback.format_exc()}")
            error_chunk = {
                "step": "error",
                "data": {"error": str(e)},
                "message": f"❌ 工作流执行异常: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield error_chunk

    # ========== LangGraph 工作流节点 ==========

    async def _analyze_request(self, state) -> Dict[str, Any]:
        """分析用户需求节点 - 直接输出MetricInfo格式"""
        user_input = state["user_input"]
        self._logger.info("🔍 分析用户指标管理需求")

        # 获取业务域信息
        try:
            domains_info = get_metric_domains()
            domains_text = "\n".join([f"- {domain['id']}: {domain['nameZh']}" for domain in domains_info])
        except Exception as e:
            self._logger.warning(f"⚠️ 获取业务域信息失败: {str(e)}")
            self._logger.warning(f"⚠️ 获取业务域异常链路: {traceback.format_exc()}")
            domains_text = ""

        # 使用配置文件中的提示词和格式化指令
        format_instructions = self.analysis_parser.get_format_instructions()
        prompt = ChatPromptTemplate.from_template(METRIC_ANALYSIS_PROMPT)

        try:
            chain = prompt | self.llm
            result = await chain.ainvoke({
                "user_input": user_input,
                "domains_text": domains_text,
                "format_instructions": format_instructions
            })

            # 使用Pydantic解析器解析LLM返回的结果
            analysis_result = self.analysis_parser.parse(result.content)

            state["analysis_result"] = analysis_result.model_dump()

            if analysis_result.metric_info:
                metric_name = analysis_result.metric_info.nameZh
                self._logger.info(f"✅ 需求分析完成: {analysis_result.operation_type} - {metric_name}")
            else:
                self._logger.info(f"✅ 需求分析完成: {analysis_result.operation_type} - 无指标信息")

        except Exception as e:
            self._logger.error(f"❌ 分析需求失败: {str(e)}")
            self._logger.error(f"❌ 分析需求异常链路: {traceback.format_exc()}")
            # 使用默认分析结果
            default_analysis = MetricAnalysisResult(
                operation_type="create",
                metric_info=None
            )
            state["analysis_result"] = default_analysis.model_dump()

        return state

    async def _query_metric(self, state) -> Dict[str, Any]:
        """查询指标节点 - 固定执行步骤"""
        analysis_data = state.get("analysis_result", {})

        # 从分析结果中获取操作类型和指标信息
        operation_type = analysis_data.get("operation_type", "create")
        metric_info_data = analysis_data.get("metric_info", {})

        # 获取指标名称进行查询
        metric_name_zh = metric_info_data.get("nameZh", "") if metric_info_data else ""
        metric_name_en = metric_info_data.get("name", "") if metric_info_data else ""

        # 优先使用中文名称查询
        query_name = metric_name_zh if metric_name_zh else metric_name_en
        self._logger.info(f"🔍 查询指标: {query_name} (操作类型: {operation_type})")

        if not query_name:
            self._logger.info("ℹ️ 未提供指标名称，跳过查询")
            state["existing_metric"] = None
            return state

        try:
            # 调用查询工具
            existing_metric = await query_metric_by_name_zh(query_name)

            if existing_metric:
                self._logger.info(f"✅ 找到现有指标: {existing_metric.get('nameZh', 'N/A')} ({existing_metric.get('code', 'N/A')})")
            else:
                self._logger.info(f"ℹ️ 未找到指标: {query_name}")

            state["existing_metric"] = existing_metric

        except Exception as e:
            self._logger.error(f"❌ 查询指标失败: {str(e)}")
            self._logger.error(f"❌ 查询指标异常链路: {traceback.format_exc()}")
            state["existing_metric"] = None

        return state

    async def _execute_operation(self, state) -> Dict[str, Any]:
        """执行指标操作节点"""
        user_input = state["user_input"]
        analysis_data = state.get("analysis_result", {})
        existing_metric = state.get("existing_metric")

        operation_type = analysis_data.get("operation_type", "create")

        # 从分析结果中提取metric_info，如果是字典则转换为MetricInfo对象
        metric_info_data = analysis_data.get("metric_info", {})
        if isinstance(metric_info_data, dict):
            analyzed_metric_info = create_metric_info_safe(metric_info_data)
        else:
            analyzed_metric_info = metric_info_data

        self._logger.info(f"🔄 执行指标操作 - {operation_type}")
        if analyzed_metric_info:
            self._logger.info(f"📊 解析的指标信息: {analyzed_metric_info.nameZh}")

        try:
            # 根据操作类型和查询结果执行相应逻辑
            if operation_type == "create":
                if existing_metric:
                    # 指标已存在
                    existing_metric_info = create_metric_info_safe(existing_metric)
                    final_result = MetricOperationResult(
                            operation_type="create",
                            status="exist",
                            message=f"指标已存在，无需重复创建: {existing_metric_info.nameZh}",
                            metric_info=None,
                            existing_metric=existing_metric_info
                        )
                else:
                    # 创建新指标 - 直接使用分析得出的MetricInfo
                    if analyzed_metric_info:
                        # 为新指标设置ID和创建时间
                        analyzed_metric_info.id = None
                        # 如果业务口径描述为空，使用用户输入
                        if not analyzed_metric_info.businessCaliberDesc:
                            analyzed_metric_info.businessCaliberDesc = f"基于用户需求创建的指标: {user_input}"

                        final_result = MetricOperationResult(
                            operation_type="create",
                            status="success",
                            message=f"指标创建成功: {analyzed_metric_info.nameZh}",
                            metric_info=analyzed_metric_info,
                            existing_metric=None
                        )
                    else:
                        final_result = MetricOperationResult(
                            operation_type="create",
                            status="error",
                            message="分析结果中缺少指标信息",
                            metric_info=None,
                            existing_metric=None
                        )

            elif operation_type == "update":
                if existing_metric:
                    # 修改现有指标 - 合并分析得出的信息和现有指标信息
                    existing_metric_info = create_metric_info_safe(existing_metric)

                        # 更新现有指标的某些字段（如果分析结果中有值）
                    if analyzed_metric_info:
                        if analyzed_metric_info.nameZh:
                            existing_metric_info.nameZh = analyzed_metric_info.nameZh
                        if analyzed_metric_info.name:
                            existing_metric_info.name = analyzed_metric_info.name
                        if analyzed_metric_info.businessCaliberDesc:
                            existing_metric_info.businessCaliberDesc = f"{existing_metric_info.businessCaliberDesc}。更新需求: {user_input}"

                    final_result = MetricOperationResult(
                        operation_type="update",
                        status="success",
                        message=f"指标修改成功: {existing_metric_info.nameZh}",
                        metric_info=existing_metric_info,
                        existing_metric=None
                    )
                else:
                    # 指标不存在
                    metric_name = analyzed_metric_info.nameZh if analyzed_metric_info else "未知指标"
                    final_result = MetricOperationResult(
                        operation_type="update",
                        status="not_exist",
                        message=f"指标不存在，无法修改: {metric_name}",
                        metric_info=None,
                        existing_metric=None
                    )

            elif operation_type == "query":
                if existing_metric:
                    # 查询成功
                    existing_metric_info = create_metric_info_safe(existing_metric)
                    final_result = MetricOperationResult(
                        operation_type="query",
                        status="success",
                        message=f"查询成功: {existing_metric_info.nameZh}",
                        metric_info=existing_metric_info,
                        existing_metric=None
                    )
                else:
                    # 查询无结果 - 返回分析得出的指标信息作为参考
                    if analyzed_metric_info:
                        final_result = MetricOperationResult(
                            operation_type="query",
                            status="not_exist",
                            message=f"未找到指标，但为您分析了相似指标: {analyzed_metric_info.nameZh}",
                            metric_info=analyzed_metric_info,
                            existing_metric=None
                        )
                    else:
                        final_result = MetricOperationResult(
                            operation_type="query",
                            status="not_exist",
                            message="未找到指标且无法分析相关信息",
                            metric_info=None,
                            existing_metric=None
                        )
            else:
                final_result = MetricOperationResult(
                    operation_type="unknown",
                    status="error",
                    message=f"不支持的操作类型: {operation_type}",
                    metric_info=None,
                    existing_metric=None
                )

            # 使用result_parser验证最终结果
            state["final_result"] = final_result
            state["success"] = True
            self._logger.info(f"✅ 指标操作执行完成: {final_result.operation_type} - {final_result.status}")


        except Exception as e:
            self._logger.error(f"❌ 执行指标操作失败: {str(e)}")
            self._logger.error(f"❌ 执行指标操作异常链路: {traceback.format_exc()}")
            error_result = MetricOperationResult(
                operation_type=operation_type,
                status="error",
                message=f"操作执行失败: {str(e)}",
                metric_info=None,
                existing_metric=None
            )
            state["final_result"] = error_result
            state["success"] = False

        return state

# 注册MetricManagementAgent
from .registry import get_registry

def register_metric_agent():
    """注册指标管理Agent"""
    registry = get_registry()

    default_metric_config = AgentConfig(
        name="metric_management",
        version="3.0.0",
        description="指标管理Agent，提供基于LangGraph的指标创建、更新和查询功能",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(MetricManagementAgent)

    registry.register("metric_management", factory, default_metric_config, {
        "category": "data_governance",
        "capabilities": ["metric_creation", "metric_update", "metric_query", "metadata_generation"],
        "agent_type": "langgraph_workflow"
    })