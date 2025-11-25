"""
Agent基类和通用接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
from datetime import datetime
import os

from config.logging_config import get_logger


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentConfig:
    """Agent配置类"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    timeout: int = 300  # 超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    enabled: bool = True
    openai_api_key: str = os.getenv("SILICONFLOW_API_KEY")
    model_name: str = "deepseek-ai/DeepSeek-V3.1",
    base_url: str = "https://api.siliconflow.cn/v1/"
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Agent响应类"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: str = ""
    agent_name: str = ""
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAgent(ABC):
    """Agent基类，定义所有Agent必须实现的接口"""

    def __init__(self, config: AgentConfig):
        """初始化Agent"""
        self.config = config
        self.status = AgentStatus.IDLE
        self._logger = get_logger(f"{__name__}.{config.name}")

        self._logger.info(f"🤖 [{config.name}] 初始化Agent...")
        self._logger.info(f"📋 版本: {config.version}")
        self._logger.info(f"📝 描述: {config.description}")

        # 初始化LLM
        self._initialize_llm()

        self._logger.info(f"✅ [{config.name}] Agent初始化完成")

    def _initialize_llm(self):
        """初始化LLM - 子类可以重写"""
        from langchain_openai import ChatOpenAI
        import os

        api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        model = self.config.model_name or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        base_url = self.config.base_url or os.getenv("OPENAI_BASE_URL")



        if not api_key:
            raise ValueError(f"Agent {self.config.name} 需要提供 OpenAI API Key")

        self._logger.info(f"🔑 使用模型: {model}")
        if base_url:
            self._logger.info(f"🌐 API基础URL: {base_url}")

        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=0.1
        )

    @property
    def name(self) -> str:
        """获取Agent名称"""
        return self.config.name

    @property
    def is_enabled(self) -> bool:
        """检查Agent是否启用"""
        return self.config.enabled

    @property
    def current_status(self) -> AgentStatus:
        """获取当前状态"""
        return self.status

    @abstractmethod
    async def process(self, user_input: str, **kwargs) -> AgentResponse:
        """处理用户输入的核心方法 - 子类必须实现"""
        pass

    async def execute_with_timeout(self, user_input: str, **kwargs) -> AgentResponse:
        """带超时控制的执行方法"""
        if not self.is_enabled:
            return AgentResponse(
                success=False,
                error=f"Agent {self.name} 已禁用",
                agent_name=self.name,
                session_id=kwargs.get("session_id", "")
            )

        self.status = AgentStatus.RUNNING
        start_time = time.time()
        session_id = kwargs.get("session_id", f"{self.name}_{int(time.time())}")

        self._logger.info(f"🚀 [{self.name}] 开始处理请求")
        self._logger.info(f"📝 会话ID: {session_id}")
        self._logger.info(f"📋 用户输入: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")

        try:
            # 使用asyncio.wait_for实现超时控制
            result = await asyncio.wait_for(
                self.process(user_input, **kwargs),
                timeout=self.config.timeout
            )

            execution_time = time.time() - start_time

            # 更新响应信息
            result.execution_time = execution_time
            result.session_id = session_id
            result.agent_name = self.name

            if result.success:
                self.status = AgentStatus.COMPLETED
                self._logger.info(f"✅ [{self.name}] 处理成功，耗时: {execution_time:.2f}秒")
            else:
                self.status = AgentStatus.FAILED
                self._logger.error(f"❌ [{self.name}] 处理失败: {result.error}")
                self._logger.info(f"⏱️ 失败前耗时: {execution_time:.2f}秒")

            return result

        except asyncio.TimeoutError:
            self.status = AgentStatus.TIMEOUT
            execution_time = time.time() - start_time
            self._logger.error(f"⏰ [{self.name}] 处理超时: {self.config.timeout}秒")

            return AgentResponse(
                success=False,
                error=f"处理超时，超过 {self.config.timeout} 秒",
                agent_name=self.name,
                session_id=session_id,
                execution_time=execution_time
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            execution_time = time.time() - start_time
            self._logger.error(f"💥 [{self.name}] 处理异常: {e}")
            self._logger.info(f"⏱️ 异常前耗时: {execution_time:.2f}秒")

            return AgentResponse(
                success=False,
                error=f"处理异常: {str(e)}",
                agent_name=self.name,
                session_id=session_id,
                execution_time=execution_time
            )

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 简单的健康检查 - 尝试调用LLM
            test_response = await self.llm.ainvoke("Hello")

            return {
                "agent_name": self.name,
                "status": "healthy",
                "config": {
                    "version": self.config.version,
                    "model": self.config.model_name,
                    "timeout": self.config.timeout
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent_name": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "version": self.config.version,
            "description": self.config.description,
            "status": self.status.value,
            "enabled": self.is_enabled,
            "config": {
                "model_name": self.config.model_name,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
        }

    def __str__(self) -> str:
        return f"Agent({self.name}, {self.config.version}, {self.status.value})"

    def __repr__(self) -> str:
        return self.__str__()


class AgentFactory(ABC):
    """Agent工厂基类"""

    @abstractmethod
    def create_agent(self, config: AgentConfig) -> BaseAgent:
        """创建Agent实例"""
        pass

    @abstractmethod
    def get_default_config(self) -> AgentConfig:
        """获取默认配置"""
        pass


class SimpleAgentFactory(AgentFactory):
    """简单的Agent工厂实现"""

    def __init__(self, agent_class):
        self.agent_class = agent_class

    def create_agent(self, config: AgentConfig) -> BaseAgent:
        """创建Agent实例"""
        return self.agent_class(config)

    def get_default_config(self) -> AgentConfig:
        """获取默认配置"""
        return AgentConfig(
            name="simple_agent",
            version="1.0.0",
            description="Simple Agent"
        )