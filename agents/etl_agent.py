"""
ETL开发Agent - 极简版本
超简化流程：解析请求 → 查询ETL → 用LLM直接生成新ETL → 结束
"""
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from tools import get_etl_script


# LLM输出解析模型
class ETLRequestAnalysisModel(BaseModel):
    """ETL请求分析结果模型"""
    operation_type: str = Field(
        description="操作类型：create/update/query，根据用户意图判断",
        examples=["create", "update", "query"]
    )
    table_name: str = Field(description="目标表名，从用户输入中提取")
    modification_requirements: List[str] = Field(description="具体的修改需求列表")
    additional_context: str = Field(default="", description="额外的上下文信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation_type": "update",
                "table_name": "policy_renewal",
                "modification_requirements": ["添加续签提醒字段", "增加保费计算逻辑"],
                "additional_context": "用于提升续签率的业务分析"
            }
        }
    }


class ETLDevelopmentAgent(BaseAgent):
    """ETL开发Agent - 极简版本"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("🔧 初始化ETL开发Agent...")

        # 创建输出解析器
        self.request_parser = PydanticOutputParser(pydantic_object=ETLRequestAnalysisModel)

        # 创建工作流
        self.workflow = self._create_workflow()
        self._logger.info("✅ ETL开发Agent初始化完成")

    def _create_workflow(self):
        """创建极简的ETL开发工作流"""
        from langgraph.graph import StateGraph, START, END
        from typing_extensions import TypedDict

        class ETLState(TypedDict):
            user_input: str
            table_name: str
            operation_type: str
            modification_requirements: List[str]
            additional_context: str
            etl_info: Optional[Dict[str, Any]]
            final_etl_code: Optional[str]
            error_message: Optional[str]

        workflow = StateGraph(ETLState)

        # 添加节点 - 超简化为3个步骤
        workflow.add_node("parse_request", self._parse_request)
        workflow.add_node("query_etl", self._query_etl)
        workflow.add_node("generate_etl", self._generate_etl)

        # 设置流程
        workflow.add_edge(START, "parse_request")
        workflow.add_edge("parse_request", "query_etl")
        workflow.add_edge("query_etl", "generate_etl")
        workflow.add_edge("generate_etl", END)

        return workflow.compile()

    async def _parse_request(self, state) -> Dict[str, Any]:
        """解析用户ETL需求"""
        user_input = state["user_input"]
        self._logger.info("🔍 第1步: 解析用户ETL需求")

        prompt = ChatPromptTemplate.from_template("""
        你是一个ETL开发专家，请分析用户的ETL开发需求，提取关键信息。

        用户需求：{user_input}

        请仔细分析用户输入，提取以下信息：
        1. operation_type: 操作类型（create/update/query），根据用户意图判断
           - 包含"创建"、"新建"、"生成"、"写一个"等词汇 → create
           - 包含"修改"、"更新"、"变更"、"调整"、"优化"等词汇 → update
           - 包含"查询"、"查看"、"搜索"、"找一下"、"获取"等词汇 → query
        2. table_name: 目标表名，用户提到的数据库表名
        3. modification_requirements: 具体的修改需求列表，每个需求要具体明确
        4. additional_context: 额外的上下文信息，帮助理解业务场景

        注意事项：
        - 操作类型要根据用户的明确意图判断，这是后续处理的关键
        - 表名要准确提取，这是后续查询ETL脚本的关键
        - 修改需求要具体，便于后续ETL代码修改
        - 如果用户没有明确提到表名，请根据上下文推断

        {format_instructions}
        """)

        try:
            chain = prompt | self.llm | self.request_parser
            result = await chain.ainvoke({
                "user_input": user_input,
                "format_instructions": self.request_parser.get_format_instructions()
            })

            # 转换为字典格式
            analysis_data = result.dict()

            # 智能操作类型映射（类似 metric_agent）
            operation_map = {
                "创建": "create", "新建": "create", "生成": "create", "写一个": "create",
                "修改": "update", "更新": "update", "变更": "update", "调整": "update", "优化": "update",
                "查询": "query", "查看": "query", "搜索": "query", "找一下": "query", "获取": "query"
            }

            operation_text = analysis_data.get("operation_type", "update")
            operation_type = operation_map.get(operation_text, "update")

            state["table_name"] = analysis_data.get("table_name", "")
            state["operation_type"] = operation_type
            state["modification_requirements"] = analysis_data.get("modification_requirements", [])
            state["additional_context"] = analysis_data.get("additional_context", "")

            self._logger.info(f"✅ 需求解析完成")
            self._logger.info(f"📊 目标表: {state['table_name']}")
            self._logger.info(f"🔧 操作类型: {operation_type}")
            self._logger.info(f"📝 修改需求数量: {len(state['modification_requirements'])}")
            for i, req in enumerate(state['modification_requirements'], 1):
                self._logger.info(f"   {i}. {req}")

        except Exception as e:
            self._logger.error(f"❌ 解析需求失败: {e}")
            state["error_message"] = f"解析需求失败: {str(e)}"
            # 设置默认值
            state["table_name"] = "unknown"
            state["operation_type"] = "update"  # 默认操作类型
            state["modification_requirements"] = []
            state["additional_context"] = ""

        return state

    async def _query_etl(self, state) -> Dict[str, Any]:
        """查询现有ETL脚本"""
        table_name = state.get("table_name", "")
        self._logger.info(f"📋 第2步: 查询表 {table_name} 的现有ETL脚本")

        try:
            if not table_name or table_name == "unknown":
                self._logger.warning("⚠️ 缺少有效的表名，跳过ETL查询")
                state["etl_info"] = {}
                return state

            # 调用工具查询ETL脚本
            etl_script = await get_etl_script(table_name)

            if etl_script:
                state["etl_info"] = etl_script
                existing_etl_code = etl_script.get("etl_code", "")
                self._logger.info(f"✅ 找到现有ETL脚本")
                self._logger.info(f"📄 代码长度: {len(existing_etl_code)} 字符")

                # 显示代码预览（前100字符）
                preview = existing_etl_code[:100] + "..." if len(existing_etl_code) > 100 else existing_etl_code
                self._logger.info(f"🔍 代码预览: {preview}")
            else:
                self._logger.info(f"ℹ️ 未找到表 {table_name} 的现有ETL脚本")
                state["etl_info"] = {}

        except Exception as e:
            self._logger.error(f"❌ 查询ETL脚本失败: {e}")
            state["error_message"] = f"查询ETL脚本失败: {str(e)}"
            state["existing_etl_code"] = None

        return state

    async def _generate_etl(self, state) -> Dict[str, Any]:
        """直接用LLM生成新的ETL脚本"""
        user_input = state["user_input"]
        etl_info = state.get("etl_info")
        modification_requirements = state.get("modification_requirements", [])
        operation_type = state.get("operation_type", "")
        additional_context = state.get("additional_context", "")
        table_name = state.get("table_name", "")

        self._logger.info("🚀 第3步: 用LLM直接生成新的ETL脚本")

        try:
            # 构建现有ETL信息
            existing_code_info = "" if etl_info else etl_info.get("etl_code", "")
            if existing_code_info:
                # 现有ETL脚本信息（保持变量引用不变）
                existing_code_info = f"""
现有ETL脚本：
```sql
{existing_code_info}
```

注意：现有脚本中的变量引用（如 $变量名）是合理的，在生成新脚本时请保留这些变量引用。
"""
            else:
                existing_code_info = "未找到现有ETL脚本，需要创建新的ETL脚本。"

            # 构建修改需求信息
            requirements_text = ""
            if modification_requirements:
                requirements_text = "\n".join([f"- {req}" for req in modification_requirements])

            prompt = ChatPromptTemplate.from_template("""
你是一个资深的ETL开发工程师，需要根据用户需求{operation_type}ETL脚本。

用户原始需求：{user_input}

操作类型：{operation_type}

具体修改需求：
{requirements_text}

额外上下文：{additional_context}

{existing_code_info}

请根据用户需求生成完整的Hive ETL脚本，脚本应该包含：
1. 适当的注释说明
2. 变量设置（如果需要）
3. 完整的INSERT OVERWRITE语句
4. 必要的WHERE条件
5. 合适的字段计算逻辑
6. 处理时间戳字段

注意事项：
- 确保SQL语法正确
- 字段名要符合规范
- 添加必要的注释
- 考虑性能优化
- 处理数据类型转换
- 如果有现有脚本，请在其基础上进行修改，保留原有的变量引用
- 如果没有现有脚本，请创建全新的ETL脚本
- 目标表名：{table_name}

请直接返回完整的Hive ETL脚本，不要包含其他解释文字。
""")

            response = await self.llm.ainvoke([
                HumanMessage(content=prompt.format(
                    user_input=user_input,
                    operation_type=operation_type,
                    requirements_text=requirements_text,
                    additional_context=additional_context,
                    existing_code_info=existing_code_info,
                    table_name=table_name
                ))
            ])

            # 提取ETL代码（去除可能的额外说明）
            etl_code = response.content.strip()

            # 如果响应中包含代码块标记，提取其中的代码
            if "```sql" in etl_code:
                code_match = re.search(r'```sql\s*(.*?)\s*```', etl_code, re.DOTALL)
                if code_match:
                    etl_code = code_match.group(1).strip()
            elif "```" in etl_code:
                code_match = re.search(r'```\s*(.*?)\s*```', etl_code, re.DOTALL)
                if code_match:
                    etl_code = code_match.group(1).strip()

            state["final_etl_code"] = etl_code
            self._logger.info("✅ ETL脚本生成完成")
            self._logger.info(f"📄 生成代码长度: {len(etl_code)} 字符")
            self._logger.info(f"🎉 ETL开发流程完成! 操作类型: {operation_type}")

        except Exception as e:
            self._logger.error(f"❌ 生成ETL脚本失败: {e}")
            state["error_message"] = f"生成ETL脚本失败: {str(e)}"
            state["final_etl_code"] = None

        return state

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法"""
        self._logger.info("🚀 开始ETL脚本开发流程")

        try:
            initial_state = {
                "user_input": user_input,
                "table_name": "",
                "operation_type": "update",  # 默认操作类型
                "modification_requirements": [],
                "additional_context": "",
                "existing_etl_code": None,
                "final_etl_code": None,
                "error_message": None
            }

            # 执行工作流
            final_state = await self.workflow.ainvoke(initial_state)
            etl_info_from_state = final_state.get("etl_info")
            operation_type = final_state.get("operation_type", "update")

            final_etl_code = final_state.get("final_etl_code")
            if final_etl_code:
                self._logger.info("✅ ETL脚本开发成功!")
                self._logger.info(f"🔄 操作类型: {operation_type}")

                return AgentResponse(
                    success=True,
                    data={
                        "etl_info": {
                            **etl_info_from_state, "etl_code": final_etl_code
                        },
                        "analysis": {"operation_type": operation_type}
                    }
                )
            else:
                error_msg = final_state.get("error_message") or "ETL脚本开发失败"
                self._logger.error(f"❌ ETL脚本开发失败: {error_msg}")

                return AgentResponse(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            self._logger.error(f"💥 ETL开发流程异常: {e}")
            return AgentResponse(
                success=False,
                error=f"ETL开发流程异常: {str(e)}"
            )


# 注册ETLDevelopmentAgent
from .registry import get_registry
from .base_agent import AgentConfig

def register_etl_agent():
    """注册ETL开发Agent"""
    registry = get_registry()

    default_etl_config = AgentConfig(
        name="etl_development",
        version="3.0.0",
        description="ETL脚本开发Agent - 生成Hive ETL脚本",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(ETLDevelopmentAgent)

    registry.register("etl_development", factory, default_etl_config, {
        "category": "data_engineering",
        "capabilities": ["etl_development", "hive_sql", "script_generation"]
    })