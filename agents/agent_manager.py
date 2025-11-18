"""
Agent管理器 - 负责Agent的生命周期管理和调度
"""
from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
import time
from datetime import datetime
from .base_agent import BaseAgent, AgentConfig, AgentResponse, AgentStatus
from .registry import get_registry

logger = logging.getLogger(__name__)


class AgentManager:
    """Agent管理器，负责管理Agent实例的生命周期"""

    def __init__(self):
        """初始化Agent管理器"""
        self._instances: Dict[str, BaseAgent] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._registry = get_registry()
        self._max_history = 1000  # 最大历史记录数

        logger.info("Agent管理器初始化完成")

    async def create_agent(
        self,
        name: str,
        config: Optional[AgentConfig] = None,
        reuse_existing: bool = True
    ) -> Optional[BaseAgent]:
        """创建Agent实例"""
        if reuse_existing and name in self._instances:
            instance = self._instances[name]
            logger.info(f"🔄 复用现有Agent实例: {name}")
            return instance

        logger.info(f"🏗️ 创建新的Agent实例: {name}")
        instance = self._registry.create_agent(name, config)

        if instance:
            self._instances[name] = instance
            logger.info(f"✅ Agent实例创建成功: {name}")
        else:
            logger.error(f"❌ Agent实例创建失败: {name}")

        return instance

    async def execute_agent(
        self,
        agent_name: str,
        user_input: str,
        config: Optional[AgentConfig] = None,
        **kwargs
    ) -> AgentResponse:
        """执行指定的Agent"""
        start_time = time.time()
        session_id = kwargs.get("session_id", f"{agent_name}_{int(start_time)}")

        logger.info(f"🚀 开始执行Agent: {agent_name}")
        logger.info(f"📝 会话ID: {session_id}")
        logger.info(f"📋 用户输入: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")

        # 记录额外参数（如table_name）
        if kwargs:
            param_summary = {k: v for k, v in kwargs.items() if k != 'session_id'}
            if param_summary:
                logger.info(f"📊 额外参数: {param_summary}")

        try:
            # 获取或创建Agent实例
            agent = await self.create_agent(agent_name, config)
            if not agent:
                error_msg = f"无法创建Agent实例: {agent_name}"
                logger.error(f"❌ {error_msg}")

                response = AgentResponse(
                    success=False,
                    error=error_msg,
                    agent_name=agent_name,
                    session_id=session_id
                )
                self._record_execution(response)
                return response

            # 执行Agent
            response = await agent.execute_with_timeout(user_input, **kwargs)

            # 记录执行历史
            self._record_execution(response)

            elapsed_time = time.time() - start_time
            logger.info(f"✅ Agent执行完成: {agent_name}")
            logger.info(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
            logger.info(f"🎯 执行结果: {'成功' if response.success else '失败'}")

            return response

        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Agent执行异常: {str(e)}"
            logger.error(f"💥 {error_msg}")
            logger.info(f"⏱️ 异常前耗时: {elapsed_time:.2f}秒")

            response = AgentResponse(
                success=False,
                error=error_msg,
                agent_name=agent_name,
                session_id=session_id,
                execution_time=elapsed_time
            )
            self._record_execution(response)
            return response

    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[AgentResponse]:
        """并行执行多个Agent任务"""
        logger.info(f"🚀 开始并行执行 {len(tasks)} 个Agent任务")

        start_time = time.time()

        # 创建并行任务
        async_tasks = []
        for i, task in enumerate(tasks):
            agent_name = task["agent_name"]
            user_input = task["user_input"]
            config = task.get("config")
            kwargs = task.get("kwargs", {})

            async_tasks.append(
                self.execute_agent(agent_name, user_input, config, **kwargs)
            )

        # 并行执行所有任务
        try:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)

            # 处理结果
            responses = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"并行任务异常: {str(result)}"
                    logger.error(f"❌ 任务 {i} 失败: {error_msg}")

                    response = AgentResponse(
                        success=False,
                        error=error_msg,
                        agent_name=tasks[i].get("agent_name", f"task_{i}"),
                        session_id=f"parallel_{i}_{int(start_time)}"
                    )
                else:
                    response = result

                responses.append(response)

            elapsed_time = time.time() - start_time
            successful_count = sum(1 for r in responses if r.success)

            logger.info(f"✅ 并行执行完成: {successful_count}/{len(tasks)} 成功")
            logger.info(f"⏱️ 总耗时: {elapsed_time:.2f}秒")

            return responses

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"💥 并行执行异常: {e}")
            logger.info(f"⏱️ 异常前耗时: {elapsed_time:.2f}秒")

            # 返回失败响应
            return [
                AgentResponse(
                    success=False,
                    error=f"并行执行异常: {str(e)}",
                    agent_name=task.get("agent_name", f"task_{i}"),
                    session_id=f"parallel_error_{i}_{int(start_time)}"
                )
                for i, task in enumerate(tasks)
            ]

    def get_agent_instance(self, name: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self._instances.get(name)

    def list_active_agents(self) -> List[str]:
        """列出活跃的Agent实例"""
        return [name for name, agent in self._instances.items()
                if agent.current_status == AgentStatus.RUNNING]

    def list_all_agents(self) -> List[str]:
        """列出所有Agent实例"""
        return list(self._instances.keys())

    def get_agent_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Agent状态"""
        agent = self._instances.get(name)
        if not agent:
            return None

        return {
            "name": agent.name,
            "status": agent.current_status.value,
            "enabled": agent.is_enabled,
            "info": agent.get_info()
        }

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """获取所有Agent状态"""
        return [self.get_agent_status(name) for name in self.list_all_agents()]

    async def health_check(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """健康检查"""
        if agent_name:
            # 检查特定Agent
            agent = self._instances.get(agent_name)
            if not agent:
                return {
                    "agent_name": agent_name,
                    "status": "not_found",
                    "error": "Agent实例不存在"
                }
            return await agent.health_check()
        else:
            # 检查所有Agent
            health_results = {}
            for name, agent in self._instances.items():
                try:
                    health_results[name] = await agent.health_check()
                except Exception as e:
                    health_results[name] = {
                        "agent_name": name,
                        "status": "error",
                        "error": str(e)
                    }

            return {
                "overall_status": "healthy" if all(
                    r.get("status") == "healthy" for r in health_results.values()
                ) else "degraded",
                "agents": health_results,
                "timestamp": datetime.now().isoformat()
            }

    def remove_agent(self, name: str) -> bool:
        """移除Agent实例"""
        if name in self._instances:
            del self._instances[name]
            logger.info(f"🗑️ Agent实例已移除: {name}")
            return True
        else:
            logger.warning(f"⚠️ Agent实例不存在: {name}")
            return False

    def clear_all_agents(self):
        """清空所有Agent实例"""
        count = len(self._instances)
        self._instances.clear()
        logger.info(f"🗑️ 清空了 {count} 个Agent实例")

    def _record_execution(self, response: AgentResponse):
        """记录执行历史"""
        history_record = {
            "agent_name": response.agent_name,
            "session_id": response.session_id,
            "success": response.success,
            "error": response.error,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp,
            "data_size": len(str(response.data)) if response.data else 0
        }

        self._execution_history.append(history_record)

        # 保持历史记录数量限制
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def get_execution_history(
        self,
        agent_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取执行历史"""
        history = self._execution_history

        # 按Agent名称过滤
        if agent_name:
            history = [h for h in history if h["agent_name"] == agent_name]

        # 限制数量
        if limit:
            history = history[-limit:]

        return history

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        registered_agents = len(self._registry.list_agents())

        if not self._execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0.0,
                "agents_count": len(self._instances),
                "active_agents": len(self.list_active_agents()),
                "registered_agents": registered_agents
            }

        total = len(self._execution_history)
        successful = sum(1 for h in self._execution_history if h["success"])
        failed = total - successful
        avg_time = sum(h["execution_time"] for h in self._execution_history) / total

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / total * 100,
            "average_execution_time": avg_time,
            "agents_count": len(self._instances),
            "active_agents": len(self.list_active_agents()),
            "registered_agents": registered_agents
        }

    async def shutdown(self):
        """关闭管理器，清理资源"""
        logger.info("🔄 正在关闭Agent管理器...")

        # 停止所有运行的Agent
        for name, agent in self._instances.items():
            if agent.current_status == AgentStatus.RUNNING:
                logger.info(f"⏹️ 停止运行中的Agent: {name}")
                # 这里可以添加优雅停止的逻辑

        # 清空实例
        self.clear_all_agents()

        logger.info("✅ Agent管理器已关闭")


# 全局Agent管理器实例
_global_manager = None


def get_agent_manager() -> AgentManager:
    """获取全局Agent管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = AgentManager()
    return _global_manager


async def execute_agent(
    agent_name: str,
    user_input: str,
    config: Optional[AgentConfig] = None,
    **kwargs
) -> AgentResponse:
    """通过全局管理器执行Agent"""
    manager = get_agent_manager()
    return await manager.execute_agent(agent_name, user_input, config, **kwargs)