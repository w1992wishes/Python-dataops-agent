"""
指标管理Agent - 处理指标的创建、更新和查询
使用LangGraph工作流
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models import MetricOperationType
from tools import (
    query_metric_by_name_zh, get_metric_domains
)


# LLM输出解析模型
class MetricAnalysisModel(BaseModel):
    """指标分析结果模型"""
    operation_type: str = Field(
        description="操作类型：create/update/query，根据用户意图判断",
        examples=["create", "update", "query"]
    )
    target_metric: str = Field(
        default="",
        description="目标指标名称，如果是修改操作时指定要修改的指标"
    )
    metric_name: str = Field(
        description="指标英文名称，指标的英文标识符，通常使用下划线分隔的小写单词",
        examples=["monthly_active_users", "order_conversion_rate", "customer_lifetime_value", "daily_sales_amount"]
    )
    metric_name_zh: str = Field(
        description="指标中文名称，从用户输入中准确提取的核心指标名称",
        examples=["月度活跃用户数", "订单转化率", "客户生命周期价值", "日销售额"]
    )
    metric_type: str = Field(
        default="IA",
        description="指标类型：IA原子指标(直接统计)/IB派生指标(计算得出)",
        examples=["IA", "IB"]
    )
    metric_level: str = Field(
        default="T2",
        description="指标重要等级：T1核心指标/T2重要指标/T3一般指标",
        examples=["T1", "T2", "T3"]
    )
    application_scenarios: str = Field(
        default="HIVE_OFFLINE",
        description="应用场景：HIVE_OFFLINE离线数仓/OLAP_ONLINE在线分析",
        examples=["HIVE_OFFLINE", "OLAP_ONLINE"]
    )
    process_domain: str = Field(
        default="domain_001",
        description="业务域ID，从可用域中选择最合适的",
        examples=["domain_001", "domain_002", "domain_003", "domain_004"]
    )
    safe_level: str = Field(
        default="S1",
        description="安全等级：S1普通数据/S2/S3/S4/S5国密数据",
        examples=["S1", "S2", "S3", "S4", "S5"]
    )
    business_owner: str = Field(
        default="待指定",
        description="业务负责人，根据指标性质推断合适角色",
        examples=["产品经理", "运营总监", "财务主管", "数据分析师"]
    )
    business_team: str = Field(
        default="待指定",
        description="业务属主团队，根据指标业务领域确定",
        examples=["产品团队", "运营团队", "财务团队", "市场团队"]
    )
    statistical_object: str = Field(
        default="待定义",
        description="统计对象，指标统计的主体",
        examples=["用户", "订单", "商品", "访问", "活动", "客户", "交易"]
    )
    statistical_rule: str = Field(
        default="待定义",
        description="统计规则，业务层面的统计逻辑，用自然语言描述"
    )
    statistical_rule_it: str = Field(
        default="待定义",
        description="IT口径，技术实现的具体SQL或技术规则"
    )
    statistical_time: str = Field(
        default="待定义",
        description="统计时间粒度，指标统计的时间周期",
        examples=["实时", "小时", "日", "周", "月", "季度", "年"]
    )
    unit: str = Field(
        default="个",
        description="指标单位，指标数值的计量单位",
        examples=["个", "人", "元", "%", "次", "笔", "天", "小时", "GB", "MB"]
    )
    business_caliber: str = Field(
        default="",
        description="指标业务口径，详细的业务含义说明，解释指标的实际业务意义和价值"
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="其他需求列表，用户提到的特殊要求或约束条件"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation_type": "create",
                "target_metric": "",
                "metric_name": "monthly_active_users",
                "metric_name_zh": "月度活跃用户数",
                "metric_type": "IA",
                "metric_level": "T1",
                "application_scenarios": "HIVE_OFFLINE",
                "process_domain": "domain_002",
                "safe_level": "S1",
                "business_owner": "产品经理",
                "business_team": "用户增长团队",
                "statistical_object": "用户",
                "statistical_rule": "统计当月内有登录或使用行为的去重用户数量",
                "statistical_rule_it": "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE activity_date >= DATE_TRUNC('month', CURRENT_DATE) AND activity_type IN ('login', 'page_view', 'click')",
                "statistical_time": "月",
                "unit": "人",
                "business_caliber": "衡量产品月度活跃度的重要指标，反映用户粘性和产品吸引力，用于指导运营策略和产品迭代",
                "requirements": ["包含所有用户类型", "排除测试账号", "按自然月统计"]
            }
        }
    }


class MetricManagementAgent(BaseAgent):
    """指标管理Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("📊 初始化指标管理Agent...")

        # 创建输出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=MetricAnalysisModel)

        # 创建工作流图
        self.graph = self._create_workflow()
        self._logger.info("✅ 指标管理Agent初始化完成")

    def _create_workflow(self):
        """创建LangGraph工作流"""
        from langgraph.graph import StateGraph, START, END
        from typing_extensions import TypedDict, Annotated
        from langgraph.graph.message import add_messages

        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
            user_input: str
            analysis_result: Optional[Dict[str, Any]]
            existing_metric: Optional[Dict[str, Any]]
            final_metric: Optional[Dict[str, Any]]
            success: bool

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("query_metric", self._query_metric)
        workflow.add_node("execute_operation", self._execute_operation)

        # 添加边
        workflow.add_edge(START, "analyze_request")
        workflow.add_edge("analyze_request", "query_metric")
        workflow.add_edge("query_metric", "execute_operation")
        workflow.add_edge("execute_operation", END)

        return workflow.compile()

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法"""
        self._logger.info("📊 开始执行指标管理工作流")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "analysis_result": None,
            "existing_metric": None,
            "final_metric": None,
            "success": False
        }

        try:
            result = await self.graph.ainvoke(initial_state)
            success = result.get("success", False)
            final_metric = result.get("final_metric")
            analysis_result = result.get("analysis_result")
            existing_metric = result.get("existing_metric")

            self._logger.info("✅ 指标管理工作流执行完成")

            return AgentResponse(
                success=success,
                data={
                    "metric": final_metric,
                    "existing_metric": existing_metric,
                    "analysis": analysis_result
                }
            )

        except Exception as e:
            self._logger.error(f"💥 指标管理工作流异常: {e}")
            return AgentResponse(
                success=False,
                error=f"指标管理工作流异常: {str(e)}"
            )

    async def process_stream(self, user_input: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户输入的流式方法"""
        self._logger.info("📊 开始执行指标管理工作流（流式）")

        initial_state = {
            "messages": [],
            "user_input": user_input,
            "analysis_result": None,
            "existing_metric": None,
            "final_metric": None,
            "success": False
        }

        try:
            # 先发送开始消息
            yield {
                "step": "starting",
                "data": {"user_input": user_input},
                "message": "🔍 开始分析您的指标管理需求...",
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
                            "has_final_metric": node_state.get("final_metric") is not None,
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
                        chunk["message"] = f"✅ 需求分析完成: {analysis.get('metric_name', 'N/A')} - {analysis.get('operation_type', 'N/A')}"
                    else:
                        chunk["message"] = "📝 正在分析您的需求..."

                elif node_name == "query_metric":
                    existing = node_state.get("existing_metric")
                    if existing:
                        chunk["data"]["existing_metric"] = existing
                        chunk["message"] = f"📋 找到已存在指标: {existing.get('nameZh', 'N/A')} ({existing.get('code', 'N/A')})"
                    else:
                        chunk["message"] = "ℹ️ 未找到已存在指标，将创建新指标"

                elif node_name == "execute_operation":
                    final_metric = node_state.get("final_metric")
                    success = node_state.get("success", False)
                    if final_metric and success:
                        chunk["data"]["final_metric"] = final_metric
                        chunk["message"] = f"🎉 指标处理完成: {final_metric.get('nameZh', 'N/A')}"
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
            error_chunk = {
                "step": "error",
                "data": {"error": str(e)},
                "message": f"❌ 指标管理工作流异常: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield error_chunk

    # ========== LangGraph 工作流节点 ==========

    async def _analyze_request(self, state) -> Dict[str, Any]:
        """分析用户需求节点"""
        user_input = state["user_input"]
        self._logger.info("🔍 分析用户指标管理需求")

        # 获取业务域信息
        try:
            domains_info = await get_metric_domains()
            domains_text = "\n".join([f"- {domain['id']}: {domain['nameZh']}" for domain in domains_info])
        except Exception as e:
            self._logger.warning(f"⚠️ 获取业务域信息失败: {e}")
            domains_info = []
            domains_text = "- domain_001: 财务\n- domain_002: 用户\n- domain_003: 产品\n- domain_004: 运营"

        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的数据分析师，请仔细分析用户的指标管理需求，提取完整的指标信息。理解用户的具体业务场景和需求细节。

        用户输入：{user_input}

        可用业务域：
        {domains_text}

        {format_instructions}

        请根据用户输入提取以下详细信息。仔细分析用户的业务场景，提取或推断出合理的指标属性：

        1. operation_type: 操作类型（create/update/query）
        2. metric_name: 指标英文名称（必填，基于中文名称生成的英文标识符，通常使用下划线分隔的小写单词）
        3. metric_name_zh: 指标中文名称（必填，从用户输入中准确提取的核心指标名称）
        4. metric_type: 指标类型（IA原子指标/IB派生指标）
           - 原子指标：直接从业务系统统计得到的原始指标，如"用户数"、"订单量"
           - 派生指标：基于其他指标计算得出的指标，如"转化率"、"人均收入"
        5. metric_level: 指标重要等级（T1最重要/T2中等/T3一般）
           - T1：核心业务指标，直接影响业务决策
           - T2：重要业务指标，常规监控使用
           - T3：一般指标，辅助分析使用
        6. application_scenarios: 应用场景（HIVE_OFFLINE离线数仓/OLAP_ONLINE在线分析）
           - HIVE_OFFLINE：用于离线数据分析，通常批量处理
           - OLAP_ONLINE：用于在线实时分析，需要快速响应
        7. process_domain: 业务域ID（从上面可用业务域列表中选择最合适的）
        8. safe_level: 安全等级（S1普通数据/S2/S3/S4/S5国密数据）
           - S1：普通业务数据
           - S2-S4：逐步增加敏感度的数据
           - S5：国密级敏感数据
        9. business_owner: 业务负责人（如果用户未明确提及，请根据指标性质推断合适的负责人角色）
        10. business_team: 业务属主团队（如"产品团队"、"运营团队"、"财务团队"等）
        11. statistical_object: 统计的主体（如"用户"、"订单"、"商品"、"访问"、"活动"等）
        12. statistical_rule: 统计规则（业务层面的统计逻辑，用自然语言描述）
        13. statistical_rule_it: IT口径（技术实现的具体SQL或规则，更技术化的描述）
        14. statistical_time: 统计时间粒度（实时、小时、日、周、月、季度、年等）
        15. unit: 指标单位（指标数值的计量单位）
           - 常见单位：个、人、元、%、次、笔、天、小时、GB、MB等
           - 根据指标名称和业务场景推断合适的单位
           - 如果用户明确提及单位则使用用户指定的单位
        16. business_caliber: 业务口径描述（详细的业务含义说明，解释这个指标的实际业务意义）
        17. requirements: 其他需求列表（用户提到的其他特殊要求）

        操作类型判断规则：
        - 包含"创建"、"新增"、"增加"、"建立一个"等词汇 → create
        - 包含"修改"、"更新"、"变更"、"调整"等词汇 → update
        - 包含"查询"、"查看"、"搜索"、"找一下"、"获取"等词汇 → query

        重要说明：
        - 如果用户没有明确提到的字段，请基于业务常识和指标性质进行合理推断
        - metric_name必须准确提取，这是后续查询和分析的关键
        - 对于派生指标(type=IB)，需要在statistical_rule中说明计算公式
        - 业务口径应该简洁明确，让业务人员能够理解指标的实际含义
        - IT口径应该更技术化，便于开发人员理解实现方式
        """)

        try:
            chain = prompt | self.llm | self.analysis_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "domains_text": domains_text,
                "format_instructions": self.analysis_parser.get_format_instructions()
            })

            # 转换为字典格式存储
            analysis_data = result.dict()

            # 确定操作类型
            operation_map = {
                "创建": "create", "新增": "create", "增加": "create",
                "修改": "update", "更新": "update", "变更": "update",
                "查询": "query", "查看": "query", "搜索": "query"
            }

            operation_text = analysis_data.get("operation_type", "create")
            operation_type = MetricOperationType(operation_map.get(operation_text, "create"))
            analysis_data["operation_type"] = operation_type.value

            state["analysis_result"] = analysis_data
            self._logger.info(f"✅ 需求分析完成: {operation_type.value} - 指标: {analysis_data.get('metric_name', 'N/A')}")

        except Exception as e:
            self._logger.error(f"❌ 分析需求失败: {e}")
            # 使用默认配置
            default_analysis = {
                "operation_type": "create",
                "metric_name": "新指标",
                "business_owner": "待指定",
                "business_team": "待指定"
            }
            state["analysis_result"] = default_analysis

        return state

    async def _query_metric(self, state) -> Dict[str, Any]:
        """查询指标节点"""
        analysis_data = state.get("analysis_result", {})
        metric_name_zh = analysis_data.get("metric_name_zh", "")
        metric_name_en = analysis_data.get("metric_name", "")

        # 优先使用中文名称查询，如果没有中文名再使用英文名
        query_name = metric_name_zh if metric_name_zh else metric_name_en
        self._logger.info(f"🔍 查询指标: {query_name}")

        if not query_name:
            self._logger.warning("⚠️ 未提供指标名称，跳过查询")
            state["existing_metric"] = None
            return state

        try:
            # 根据指标中文名称查询
            existing_metric = await query_metric_by_name_zh(query_name)

            if existing_metric:
                self._logger.info(f"✅ 找到现有指标: {existing_metric.get('nameZh', 'N/A')} ({existing_metric.get('code', 'N/A')})")
            else:
                self._logger.info(f"ℹ️ 未找到指标: {query_name}")

            state["existing_metric"] = existing_metric

        except Exception as e:
            self._logger.error(f"❌ 查询指标失败: {e}")
            state["existing_metric"] = None

        return state

    async def _execute_operation(self, state) -> Dict[str, Any]:
        """执行指标操作节点"""
        user_input = state["user_input"]
        analysis_data = state.get("analysis_result", {})
        existing_metric = state.get("existing_metric")

        operation_type_str = analysis_data.get("operation_type", "create")
        operation_type = MetricOperationType(operation_type_str)

        self._logger.info(f"🔄 执行指标操作 - {operation_type.value}")

        try:
            if operation_type == MetricOperationType.CREATE:
                # 新增逻辑：如果查询到已有指标，返回查询结果；否则创建新指标
                if existing_metric:
                    self._logger.info(f"ℹ️ 指标已存在，直接返回: {existing_metric.get('nameZh', 'N/A')}")
                    state["final_metric"] = existing_metric
                    state["success"] = True
                else:
                    # 生成新指标Schema
                    new_metric_schema = await self._create_new_metric_schema(user_input, analysis_data)
                    if new_metric_schema:
                        state["final_metric"] = new_metric_schema
                        state["success"] = True
                        self._logger.info(f"✅ 新指标Schema生成成功: {new_metric_schema.get('nameZh', 'N/A')}")
                    else:
                        state["final_metric"] = None
                        state["success"] = False

            elif operation_type == MetricOperationType.UPDATE:
                # 修改逻辑：如果查询到已有指标，进行合并更新；否则提示未找到
                if existing_metric:
                    updated_metric_schema = self._update_existing_metric_schema(user_input, analysis_data, existing_metric)
                    if updated_metric_schema:
                        state["final_metric"] = updated_metric_schema
                        state["success"] = True
                        self._logger.info(f"✅ 指标更新Schema生成成功: {updated_metric_schema.get('nameZh', 'N/A')}")
                    else:
                        state["final_metric"] = None
                        state["success"] = False
                else:
                    self._logger.warning(f"⚠️ 未找到要更新的指标: {analysis_data.get('metric_name', 'N/A')}")
                    state["final_metric"] = None
                    state["success"] = False

            elif operation_type == MetricOperationType.QUERY:
                # 查询逻辑：直接返回查询结果
                if existing_metric:
                    self._logger.info(f"✅ 指标查询成功: {existing_metric.get('nameZh', 'N/A')}")
                    state["final_metric"] = existing_metric
                    state["success"] = True
                else:
                    self._logger.info(f"ℹ️ 未找到指标: {analysis_data.get('metric_name', 'N/A')}")
                    state["final_metric"] = None
                    state["success"] = True  # 查询不到也算成功

            else:
                self._logger.error(f"❌ 不支持的操作类型: {operation_type}")
                state["final_metric"] = None
                state["success"] = False

        except Exception as e:
            self._logger.error(f"❌ 执行指标操作失败: {e}")
            state["final_metric"] = None
            state["success"] = False

        return state

    async def _create_new_metric_schema(self, user_input: str, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建新指标的Schema"""
        try:
            # 获取当前时间戳
            from datetime import datetime
            current_time = datetime.now().isoformat()

            metric_name_zh = analysis_data.get("metric_name_zh", "")
            metric_name_en = analysis_data.get("metric_name", "")

            if not metric_name_zh:
                self._logger.warning("⚠️ 缺少指标中文名称，无法生成Schema")
                return None

            # 如果没有英文名，根据中文名生成
            if not metric_name_en:
                metric_name_en = metric_name_zh.lower().replace(" ", "_").replace("（", "").replace("）", "").replace("(", "").replace(")", "")

            # 获取业务域并智能匹配
            process_domain = analysis_data.get("process_domain", "")

            # 智能推断负责人和团队
            business_owner = analysis_data.get("business_owner", "WAN")
            business_team = analysis_data.get("business_team", "最强财富团队")

            # 构建完整的业务口径描述
            business_caliber = analysis_data.get("business_caliber", "")
            if not business_caliber:
                stat_time = analysis_data.get("statistical_time", "待定义")
                stat_object = analysis_data.get("statistical_object", "指标")
                business_caliber = f"统计{stat_time}的{metric_name_zh}，反映{stat_object}的相关业务情况"

            # 构建技术实现说明
            statistical_rule_it = analysis_data.get("statistical_rule_it", "")
            if not statistical_rule_it:
                statistical_rule = analysis_data.get("statistical_rule", "")
                if statistical_rule:
                    statistical_rule_it = f"根据统计规则实现: {statistical_rule}"
                else:
                    statistical_rule_it = f"基于业务规则计算{metric_name_zh}"

            # 智能推断指标单位
            unit = analysis_data.get("unit", "个")

            # 从分析数据中获取值，如果没有则使用智能推断的默认值
            metric_data = {
                "nameZh": metric_name_zh,
                "name": metric_name_en,
                "code": "",  # 新增时为空
                "applicationScenarios": analysis_data.get("application_scenarios", "HIVE_OFFLINE"),
                "type": analysis_data.get("metric_type", "IA"),
                "lv": analysis_data.get("metric_level", "T2"),
                "processDomainId": process_domain,
                "safeLv": analysis_data.get("safe_level", "S1"),
                "businessCaliberDesc": business_caliber,
                "businessOwner": business_owner,
                "businessTeam": business_team,
                "statisticalObject": analysis_data.get("statistical_object", metric_name_zh.split("数")[0] if "数" in metric_name_zh else "业务对象"),
                "statisticalRule": analysis_data.get("statistical_rule", f"统计{metric_name_zh}的业务逻辑"),
                "statisticalRuleIt": statistical_rule_it,
                "statisticalTime": analysis_data.get("statistical_time", "日"),
                "unit": unit,
                "physicalInfoList": [] if analysis_data.get("metric_type") == "IA" else [{"metricId": ""}],
                "id": None,
                "create_time": current_time,
                "update_time": current_time
            }

            self._logger.info(f"✅ 生成新指标Schema: {metric_data.get('nameZh', 'N/A')} (域: {process_domain}, 负责人: {business_owner})")
            return metric_data

        except Exception as e:
            self._logger.error(f"❌ 生成新指标Schema失败: {e}")
            return None

    def _update_existing_metric_schema(self, user_input: str, analysis_data: Dict[str, Any], existing_metric: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新现有指标的Schema"""
        try:
            # 获取当前时间戳
            from datetime import datetime
            current_time = datetime.now().isoformat()

            # 合并更新数据 - 优先使用分析数据，没有则保留原数据
            updated_metric = existing_metric.copy()

            # 更新各个字段，如果分析数据中有新值则使用新值，否则保留原值
            if analysis_data.get("metric_name_zh"):
                updated_metric["nameZh"] = analysis_data["metric_name_zh"]

            # 英文名：优先使用用户提供的，如果用户没提供则根据中文名生成
            if analysis_data.get("metric_name"):
                updated_metric["name"] = analysis_data["metric_name"]
            elif analysis_data.get("metric_name_zh"):
                updated_metric["name"] = analysis_data["metric_name_zh"].lower().replace(" ", "_")

            if analysis_data.get("application_scenarios"):
                updated_metric["applicationScenarios"] = analysis_data["application_scenarios"]

            if analysis_data.get("metric_type"):
                updated_metric["type"] = analysis_data["metric_type"]
                # 如果是派生指标，需要设置physicalInfoList
                if analysis_data["metric_type"] == "IB":
                    updated_metric["physicalInfoList"] = [{"metricId": ""}]
                else:
                    updated_metric["physicalInfoList"] = []

            if analysis_data.get("metric_level"):
                updated_metric["lv"] = analysis_data["metric_level"]

            if analysis_data.get("process_domain"):
                updated_metric["processDomainId"] = analysis_data["process_domain"]

            if analysis_data.get("safe_level"):
                updated_metric["safeLv"] = analysis_data["safe_level"]

            if analysis_data.get("business_owner"):
                updated_metric["businessOwner"] = analysis_data["business_owner"]

            if analysis_data.get("business_team"):
                updated_metric["businessTeam"] = analysis_data["business_team"]

            if analysis_data.get("statistical_object"):
                updated_metric["statisticalObject"] = analysis_data["statistical_object"]

            if analysis_data.get("statistical_rule"):
                updated_metric["statisticalRule"] = analysis_data["statistical_rule"]

            if analysis_data.get("statistical_rule_it"):
                updated_metric["statisticalRuleIt"] = analysis_data["statistical_rule_it"]

            if analysis_data.get("statistical_time"):
                updated_metric["statisticalTime"] = analysis_data["statistical_time"]

            if analysis_data.get("unit"):
                updated_metric["unit"] = analysis_data["unit"]

            # 更新业务口径 - 保留原有并追加更新内容
            if analysis_data.get("business_caliber"):
                original_caliber = existing_metric.get("businessCaliberDesc", "")
                update_info = analysis_data["business_caliber"]
                if original_caliber:
                    updated_metric["businessCaliberDesc"] = f"{original_caliber}。更新内容: {update_info}"
                else:
                    updated_metric["businessCaliberDesc"] = update_info

            # 更新时间戳
            updated_metric["update_time"] = current_time

            self._logger.info(f"✅ 生成更新指标Schema: {updated_metric.get('nameZh', 'N/A')}")
            return updated_metric

        except Exception as e:
            self._logger.error(f"❌ 生成更新指标Schema失败: {e}")
            return None

    

# 注册MetricManagementAgent
from .registry import get_registry
from .base_agent import AgentConfig

def register_metric_agent():
    """注册指标管理Agent"""
    registry = get_registry()

    default_metric_config = AgentConfig(
        name="metric_management",
        version="1.0.0",
        description="指标管理Agent，提供指标的创建、更新和查询功能",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(MetricManagementAgent)

    registry.register("metric_management", factory, default_metric_config, {
        "category": "data_governance",
        "capabilities": ["metric_creation", "metric_update", "metric_query", "metadata_generation"]
    })