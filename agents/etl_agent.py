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

            operation_type = analysis_data.get("operation_type", "update")

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
        """生成ETL脚本，保留配置部分，只修改转换逻辑"""
        user_input = state["user_input"]
        etl_info = state.get("etl_info")
        modification_requirements = state.get("modification_requirements", [])
        operation_type = state.get("operation_type", "")
        additional_context = state.get("additional_context", "")
        table_name = state.get("table_name", "")

        self._logger.info("🚀 第3步: 生成ETL脚本，保留配置，修改转换逻辑")

        try:
            # 解析现有ETL脚本
            existing_etl_code = etl_info.get("etl_code", "") if etl_info else ""

            if existing_etl_code and operation_type == "update":
                # 分离配置部分和转换部分
                config_part, transform_part = self._parse_etl_script(existing_etl_code)

                self._logger.info(f"📋 识别到配置部分长度: {len(config_part)} 字符")
                self._logger.info(f"🔄 识别到转换部分长度: {len(transform_part)} 字符")

                # 构建修改需求信息
                requirements_text = ""
                if modification_requirements:
                    requirements_text = "\n".join([f"- {req}" for req in modification_requirements])

                # 生成新的转换逻辑
                prompt = ChatPromptTemplate.from_template("""
你是一个资深的ETL开发工程师，需要根据用户需求修改ETL脚本的转换逻辑部分。

用户原始需求：{user_input}

具体修改需求：
{requirements_text}

额外上下文：{additional_context}

现有转换逻辑：
```sql
{transform_part}
```

要求：
1. 只修改转换逻辑部分（INSERT、SELECT、WHERE等SQL语句）
2. 保留原有的变量引用（如 $变量名）
3. 确保新的转换逻辑满足用户的修改需求
4. 保持SQL语法正确性
5. 考虑性能优化
6. 目标表名：{table_name}

请只返回修改后的转换逻辑部分，不要包含配置部分，也不要包含```sql```标记。
""")

                response = await self.llm.ainvoke([
                    HumanMessage(content=prompt.format(
                        user_input=user_input,
                        requirements_text=requirements_text,
                        additional_context=additional_context,
                        transform_part=transform_part,
                        table_name=table_name
                    ))
                ])

                # 提取新的转换逻辑
                new_transform_code = response.content.strip()

                # 清理可能的代码块标记
                if "```sql" in new_transform_code:
                    code_match = re.search(r'```sql\s*(.*?)\s*```', new_transform_code, re.DOTALL)
                    if code_match:
                        new_transform_code = code_match.group(1).strip()
                elif "```" in new_transform_code:
                    code_match = re.search(r'```\s*(.*?)\s*```', new_transform_code, re.DOTALL)
                    if code_match:
                        new_transform_code = code_match.group(1).strip()

                # 组合配置部分和新的转换逻辑
                final_etl_code = self._combine_etl_parts(config_part, new_transform_code)

                self._logger.info(f"✅ ETL脚本修改完成，保留了配置部分")
                self._logger.info(f"📄 最终代码长度: {len(final_etl_code)} 字符")

            else:
                # 创建新的ETL脚本
                requirements_text = ""
                if modification_requirements:
                    requirements_text = "\n".join([f"- {req}" for req in modification_requirements])

                prompt = ChatPromptTemplate.from_template("""
你是一个资深的ETL开发工程师，需要根据用户需求创建新的ETL脚本。

用户需求：{user_input}

具体需求：
{requirements_text}

额外上下文：{additional_context}

请创建完整的Hive ETL脚本，包含：
1. 变量设置部分（Hive参数、日期变量等）
2. 转换逻辑部分（INSERT OVERWRITE语句等）

要求：
- 确保SQL语法正确
- 添加适当的注释说明
- 考虑性能优化
- 处理数据类型转换
- 目标表名：{table_name}

请直接返回完整的Hive ETL脚本，不要包含```sql```标记。
""")

                response = await self.llm.ainvoke([
                    HumanMessage(content=prompt.format(
                        user_input=user_input,
                        requirements_text=requirements_text,
                        additional_context=additional_context,
                        table_name=table_name
                    ))
                ])

                final_etl_code = response.content.strip()

                # 清理可能的代码块标记
                if "```sql" in final_etl_code:
                    code_match = re.search(r'```sql\s*(.*?)\s*```', final_etl_code, re.DOTALL)
                    if code_match:
                        final_etl_code = code_match.group(1).strip()
                elif "```" in final_etl_code:
                    code_match = re.search(r'```\s*(.*?)\s*```', final_etl_code, re.DOTALL)
                    if code_match:
                        final_etl_code = code_match.group(1).strip()

                self._logger.info(f"✅ 新ETL脚本创建完成")

            state["final_etl_code"] = final_etl_code
            self._logger.info("✅ ETL脚本生成完成")
            self._logger.info(f"📄 生成代码长度: {len(final_etl_code)} 字符")
            self._logger.info(f"🎉 ETL开发流程完成! 操作类型: {operation_type}")

        except Exception as e:
            self._logger.error(f"❌ 生成ETL脚本失败: {e}")
            state["error_message"] = f"生成ETL脚本失败: {str(e)}"
            state["final_etl_code"] = None

        return state

    def _parse_etl_script(self, etl_code: str) -> tuple:
        """解析ETL脚本，分离配置部分和转换部分"""
        lines = etl_code.split('\n')
        config_lines = []
        transform_lines = []

        in_transform_section = False

        for line in lines:
            stripped_line = line.strip()

            # 识别转换逻辑开始的标志
            if (stripped_line.upper().startswith('INSERT') or
                stripped_line.upper().startswith('WITH') or
                stripped_line.upper().startswith('SELECT') or
                stripped_line.startswith('--') and '转换' in stripped_line or
                stripped_line.startswith('--') and 'transform' in stripped_line.lower() or
                stripped_line.startswith('--') and 'ETL' in stripped_line):
                in_transform_section = True
                transform_lines.append(line)
            # 如果已经在转换部分，继续添加
            elif in_transform_section:
                transform_lines.append(line)
            # 配置部分的特征
            elif (stripped_line.startswith('SET ') or
                  stripped_line.startswith('ADD JAR ') or
                  stripped_line.startswith('USE ') or
                  stripped_line.startswith('--') and '配置' in stripped_line or
                  stripped_line.startswith('--') and 'config' in stripped_line.lower() or
                  stripped_line.startswith('--') and '参数' in stripped_line or
                  stripped_line.startswith('--') and 'variable' in stripped_line.lower() or
                  not stripped_line):  # 空行也属于配置部分
                config_lines.append(line)
            else:
                # 默认情况下，不确定的内容先归为配置部分
                if not in_transform_section:
                    config_lines.append(line)
                else:
                    transform_lines.append(line)

        config_part = '\n'.join(config_lines).strip()
        transform_part = '\n'.join(transform_lines).strip()

        return config_part, transform_part

    def _combine_etl_parts(self, config_part: str, transform_part: str) -> str:
        """组合配置部分和转换部分"""
        parts = []

        if config_part:
            parts.append(config_part)

        if config_part and transform_part:
            parts.append("")  # 添加空行分隔

        if transform_part:
            parts.append(transform_part)

        return '\n'.join(parts)

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