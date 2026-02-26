"""
协议层 - 定义层间通信接口

此模块定义所有层间通信的抽象接口，实现依赖倒置原则。
上层（插件层）只依赖此协议的抽象接口，不依赖下层具体实现。

分层依赖关系:
    插件层 ──依赖──> 协议层 <──实现── 服务层
    接收层 ──依赖──> 协议层 <──实现── 服务层
    服务层 ──依赖──> 协议层（基础部分）
    
设计原则:
    1. 协议层不包含任何实现，只有抽象接口
    2. 上层通过协议接口调用下层能力
    3. 下层实现协议接口并注册到服务定位器
    4. 禁止跨层直接导入具体类
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic, Callable, Type

# 导入基础层的结果类型
from .base import Result


# ========== 服务协议接口 ==========

class AIServiceProtocol(ABC):
    """AI 服务协议 - 插件层通过此接口使用 AI 能力"""
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """AI 服务是否可用"""
        pass
    
    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9
    ) -> Result[str]:
        """调用 AI 对话"""
        pass


class BanServiceProtocol(ABC):
    """黑名单服务协议"""
    
    @abstractmethod
    def is_banned(self, user_id: int) -> bool:
        """检查用户是否被拉黑"""
        pass
    
    @abstractmethod
    def ban(self, user_id: int) -> Result[bool]:
        """拉黑用户"""
        pass
    
    @abstractmethod
    def unban(self, user_id: int) -> Result[bool]:
        """解封用户"""
        pass


class ChatServiceProtocol(ABC):
    """聊天服务协议"""
    
    @abstractmethod
    def record_message(
        self,
        group_id: int,
        user_id: int,
        username: str,
        message: str,
        is_bot: bool = False
    ) -> None:
        """记录消息到历史"""
        pass
    
    @abstractmethod
    def get_context(self, group_id: int, limit: int = 50) -> str:
        """获取群聊上下文"""
        pass
    
    @abstractmethod
    def check_cooldown(self, group_id: int, cooldown_seconds: int = 30) -> bool:
        """检查冷却时间"""
        pass
    
    @abstractmethod
    def set_cooldown(self, group_id: int) -> None:
        """设置冷却时间"""
        pass


class BotServiceProtocol(ABC):
    """Bot API 服务协议"""
    
    @abstractmethod
    async def send_message(self, event: Any, message: Any, at_user: bool = False) -> Result[bool]:
        """发送消息"""
        pass
    
    @abstractmethod
    async def ban_user(self, group_id: int, user_id: int, duration: int) -> Result[bool]:
        """禁言用户"""
        pass


class TokenServiceProtocol(ABC):
    """令牌服务协议"""
    
    @abstractmethod
    def generate_token(self, user_id: int) -> str:
        """生成一次性令牌"""
        pass
    
    @abstractmethod
    def verify_token(self, user_id: int, token: str) -> bool:
        """验证令牌"""
        pass


class SystemMonitorProtocol(ABC):
    """系统监控服务协议"""
    
    @abstractmethod
    def get_status_text(self) -> str:
        """获取格式化的状态文本"""
        pass




# ========== 服务定位器 ==========

T = TypeVar('T')


class ServiceLocator:
    """
    服务定位器 - 解耦服务的获取与实现
    
    上层通过 locator 获取服务接口，不关心具体实现。
    下层在初始化完成后注册到 locator。
    
    Example:
        # 服务层初始化完成后注册
        service.initialize()
        locator.register(AIServiceProtocol, service)
        
        # 插件层通过 locator 获取
        ai = locator.get(AIServiceProtocol)
        result = await ai.chat(...)
    """
    
    _services: dict[Type[Any], Any] = {}
    
    @classmethod
    def register(cls, protocol: Type[T], implementation: T) -> None:
        """
        注册服务实现
        
        Args:
            protocol: 协议接口类
            implementation: 协议实现实例（必须已完成初始化）
        """
        cls._services[protocol] = implementation
    
    @classmethod
    def get(cls, protocol: Type[T]) -> Optional[T]:
        """
        获取服务实现
        
        Args:
            protocol: 协议接口类
            
        Returns:
            协议实现实例，如果未注册返回 None
        """
        return cls._services.get(protocol)
    
    @classmethod
    def has(cls, protocol: Type[Any]) -> bool:
        """检查是否已注册某协议"""
        return protocol in cls._services


