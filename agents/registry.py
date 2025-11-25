"""
Agent注册中心 - 管理所有可用的Agent
"""
from typing import Dict, List, Optional, Type, Any
import logging
from .base_agent import BaseAgent, AgentFactory, AgentConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent注册中心，负责管理所有Agent的注册和发现"""

    def __init__(self):
        """初始化注册中心"""
        self._agents: Dict[str, AgentFactory] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("Agent注册中心初始化完成")

    def register(
        self,
        name: str,
        factory: AgentFactory,
        config: Optional[AgentConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """注册Agent"""
        if name in self._agents:
            logger.warning(f"⚠️ Agent '{name}' 已存在，将被覆盖")

        self._agents[name] = factory
        self._agent_configs[name] = config or factory.get_default_config()
        self._agent_metadata[name] = metadata or {}

        logger.info(f"Agent '{name}' 注册成功")
        logger.info(f"   描述: {self._agent_configs[name].description}")
        logger.info(f"   工厂: {factory.__class__.__name__}")

    def register_class(
        self,
        name: str,
        agent_class: Type[BaseAgent],
        config: Optional[AgentConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """通过类注册Agent（使用简单工厂）"""
        from .base_agent import SimpleAgentFactory
        factory = SimpleAgentFactory(agent_class)
        self.register(name, factory, config, metadata)

    def unregister(self, name: str) -> bool:
        """注销Agent"""
        if name in self._agents:
            del self._agents[name]
            del self._agent_configs[name]
            if name in self._agent_metadata:
                del self._agent_metadata[name]
            logger.info(f"🗑️ Agent '{name}' 注销成功")
            return True
        else:
            logger.warning(f"⚠️ Agent '{name}' 不存在")
            return False

    def get_factory(self, name: str) -> Optional[AgentFactory]:
        """获取Agent工厂"""
        return self._agents.get(name)

    def get_config(self, name: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        return self._agent_configs.get(name)

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Agent元数据"""
        return self._agent_metadata.get(name)

    def create_agent(self, name: str, config_override: Optional[AgentConfig] = None) -> Optional[BaseAgent]:
        """创建Agent实例"""
        factory = self.get_factory(name)
        if not factory:
            logger.error(f"❌ Agent '{name}' 未注册")
            return None

        # 合并配置
        base_config = self.get_config(name)
        if config_override:
            # 创建新的配置对象，合并覆盖项
            import os
            merged_config = AgentConfig(
                name=config_override.name or base_config.name,
                version=config_override.version or base_config.version,
                description=config_override.description or base_config.description,
                timeout=config_override.timeout or base_config.timeout,
                max_retries=config_override.max_retries or base_config.max_retries,
                enabled=config_override.enabled if config_override.enabled is not None else base_config.enabled,
                openai_api_key=config_override.openai_api_key or base_config.openai_api_key,
                model_name=config_override.model_name or base_config.model_name,
                base_url=config_override.base_url or base_config.base_url,
                extra_config={**base_config.extra_config, **config_override.extra_config}
            )
        else:
            merged_config = base_config

        try:
            agent = factory.create_agent(merged_config)
            logger.info(f"✅ Agent '{name}' 实例创建成功")
            return agent
        except Exception as e:
            logger.error(f"❌ 创建 Agent '{name}' 失败: {e}")
            return None

    def list_agents(self) -> List[str]:
        """列出所有已注册的Agent名称"""
        return list(self._agents.keys())

    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Agent详细信息"""
        if name not in self._agents:
            return None

        config = self.get_config(name)
        metadata = self.get_metadata(name)

        return {
            "name": name,
            "factory": self._agents[name].__class__.__name__,
            "config": {
                "name": config.name,
                "version": config.version,
                "description": config.description,
                "timeout": config.timeout,
                "max_retries": config.max_retries,
                "enabled": config.enabled,
                "model_name": config.model_name
            },
            "metadata": metadata
        }

    def list_agents_info(self) -> List[Dict[str, Any]]:
        """列出所有Agent的详细信息"""
        return [self.get_agent_info(name) for name in self.list_agents()]

    def is_registered(self, name: str) -> bool:
        """检查Agent是否已注册"""
        return name in self._agents

    def clear(self):
        """清空所有注册的Agent"""
        count = len(self._agents)
        self._agents.clear()
        self._agent_configs.clear()
        self._agent_metadata.clear()
        logger.info(f"🗑️ 清空了 {count} 个注册的Agent")


# 全局Agent注册中心实例
_global_registry = AgentRegistry()


def register_agent_class(
    name: str,
    agent_class: Type[BaseAgent],
    config: Optional[AgentConfig] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """注册Agent类"""
    _global_registry.register_class(name, agent_class, config, metadata)


def get_registry() -> AgentRegistry:
    """获取全局Agent注册中心"""
    return _global_registry


def create_agent(name: str, config_override: Optional[AgentConfig] = None) -> Optional[BaseAgent]:
    """通过全局注册中心创建Agent实例"""
    return _global_registry.create_agent(name, config_override)


def list_available_agents() -> List[str]:
    """列出所有可用的Agent"""
    return _global_registry.list_agents()


def get_agent_info(name: str) -> Optional[Dict[str, Any]]:
    """获取Agent信息"""
    return _global_registry.get_agent_info(name)