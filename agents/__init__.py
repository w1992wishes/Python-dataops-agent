"""
Agents模块 - 提供各种智能代理功能
"""
from .base_agent import BaseAgent, AgentResponse, AgentConfig
from .agent_manager import AgentManager, get_agent_manager, execute_agent
from .registry import AgentRegistry

# 导入所有Agent以触发自动注册
from .table_agent import register_table_agent
from .etl_agent import register_etl_agent
from .metric_agent import register_metric_agent

# 确保所有Agent都被注册
register_table_agent()
register_etl_agent()
register_metric_agent()

__all__ = [
    'BaseAgent',
    'AgentResponse',
    'AgentConfig',
    'AgentManager',
    'AgentRegistry',
    'get_agent_manager',
    'execute_agent'
]