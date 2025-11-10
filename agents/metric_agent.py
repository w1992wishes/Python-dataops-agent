"""
指标管理Agent - 处理指标的创建、更新和查询
使用React Agent重构
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_agent
from langchain_core.tools import tool

from .base_agent import BaseAgent, AgentConfig, AgentResponse
from models.metric_schemas import MetricOperationResult
from tools.metric_tools import (
    query_metric_by_name_zh, get_metric_domains
)
from config.react_agent_prompts import (
    METRIC_REACT_AGENT_SYSTEM_PROMPT,
    DOMAIN_INFO
)


# 指标查询工具
@tool
async def query_metric_tool(metric_name: str) -> Dict[str, Any]:
    """查询指定名称的指标是否存在

    Args:
        metric_name: 指标名称（中文或英文）

    Returns:
        查询结果，包含指标信息或提示不存在
    """
    try:
        result = await query_metric_by_name_zh(metric_name)
        if result:
            return {
                "success": True,
                "message": f"找到指标: {result.get('nameZh', 'N/A')}",
                "metric": result
            }
        else:
            return {
                "success": False,
                "message": f"未找到指标: {metric_name}",
                "metric": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"查询指标时出错: {str(e)}",
            "metric": None
        }


@tool
async def get_domains_tool() -> Dict[str, Any]:
    """获取可用的业务域列表

    Returns:
        业务域信息列表
    """
    try:
        domains = await get_metric_domains()
        return {
            "success": True,
            "message": "获取业务域列表成功",
            "domains": domains
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取业务域列表失败: {str(e)}",
            "domains": []
        }


class MetricManagementAgent(BaseAgent):
    """指标管理Agent - 使用React Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._logger.info("📊 初始化指标管理React Agent...")

        # 创建输出解析器
        self.result_parser = PydanticOutputParser(pydantic_object=MetricOperationResult)

        # 准备工具列表
        tools = [query_metric_tool, get_domains_tool]

        # 动态生成完整的系统提示词
        format_instructions = self.result_parser.get_format_instructions()
        system_message = METRIC_REACT_AGENT_SYSTEM_PROMPT.format(
            format_instructions=format_instructions,
            domain_info=DOMAIN_INFO
        )

        self.react_agent = create_agent(
            self.llm,
            tools,
            system_prompt=system_message
        )

        self._logger.info("✅ 指标管理React Agent初始化完成")

    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """使用React Agent处理用户输入"""
        self._logger.info("📊 开始执行指标管理React Agent")

        try:
            # 准备输入消息
            messages = [
                ("human", user_input)
            ]

            # 调用React Agent
            response = await self.react_agent.ainvoke({
                "messages": messages
            })

            # 获取最后的回复消息
            last_message = response["messages"][-1]
            agent_reply = last_message.content

            # 直接解析Agent的结构化输出
            try:
                # React Agent现在应该直接输出JSON格式的结果
                result = self.result_parser.parse(agent_reply)

                self._logger.info(f"✅ React Agent执行完成: {result.operation_type} - {result.status}")
                return AgentResponse(
                    success=True,
                    data={
                        "operation_result": result.model_dump(),
                        "agent_reply": agent_reply
                    }
                )

            except Exception as parse_error:
                self._logger.warning(f"⚠️ 解析结构化结果失败，返回原始回复: {parse_error}")
                # 如果解析失败，尝试从文本中提取信息
                import re

                # 尝试从回复中提取JSON
                json_match = re.search(r'\{.*\}', agent_reply, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group()
                        result = self.result_parser.parse(json_str)
                        return AgentResponse(
                            success=True,
                            data={
                                "operation_result": result.dict(),
                                "agent_reply": agent_reply
                            }
                        )
                    except:
                        pass

                # 如果还是失败，创建基本的结果结构
                basic_result = MetricOperationResult(
                    operation_type="query",
                    status="success",
                    message=agent_reply[:200] + "..." if len(agent_reply) > 200 else agent_reply,
                    metric_info=None,
                    existing_metric=None
                )

                return AgentResponse(
                    success=True,
                    data={
                        "operation_result": basic_result.dict(),
                        "agent_reply": agent_reply
                    }
                )

        except Exception as e:
            self._logger.error(f"💥 React Agent执行异常 | 错误类型: {type(e).__name__} | 错误信息: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"React Agent执行异常: {str(e)}"
            )

    async def process_stream(self, user_input: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """使用React Agent的流式处理方法"""
        self._logger.info("📊 开始执行指标管理React Agent（流式）")

        try:
            # 先发送开始消息
            yield {
                "step": "starting",
                "data": {"user_input": user_input},
                "message": "🔍 开始处理您的指标管理需求...",
                "timestamp": datetime.now().isoformat()
            }

            # 准备输入消息
            messages = [
                ("human", user_input)
            ]

            # 使用React Agent的流式执行
            async for chunk in self.react_agent.astream({
                "messages": messages
            }):
                # 发送Agent执行的中间结果
                chunk_data = {
                    "step": "agent_thinking",
                    "data": {
                        "chunk": chunk,
                        "agent_type": "react_agent"
                    },
                    "message": "🤖 Agent正在分析和处理...",
                    "timestamp": datetime.now().isoformat()
                }
                yield chunk_data

            # 发送最终完成消息
            final_chunk = {
                "step": "completed",
                "data": {"react_agent_completed": True},
                "message": "✅ React Agent处理完成",
                "timestamp": datetime.now().isoformat()
            }
            yield final_chunk

        except Exception as e:
            error_chunk = {
                "step": "error",
                "data": {"error": str(e)},
                "message": f"❌ React Agent执行异常: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield error_chunk

    

# 注册MetricManagementAgent
from .registry import get_registry
from .base_agent import AgentConfig

def register_metric_agent():
    """注册指标管理React Agent"""
    registry = get_registry()

    default_metric_config = AgentConfig(
        name="metric_management_react",
        version="2.0.0",
        description="指标管理React Agent，提供基于LangGraph的智能指标创建、更新和查询功能",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    from .base_agent import SimpleAgentFactory
    factory = SimpleAgentFactory(MetricManagementAgent)

    registry.register("metric_management_react", factory, default_metric_config, {
        "category": "data_governance",
        "capabilities": ["metric_creation", "metric_update", "metric_query", "metadata_generation", "react_agent"],
        "agent_type": "react",
        "tools": ["query_metric_tool", "get_domains_tool"]
    })