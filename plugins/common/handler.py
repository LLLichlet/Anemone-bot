"""
处理器基类模块 - 插件业务逻辑接口

此模块定义插件层的业务逻辑处理器基类。
Handler 只负责业务处理，不处理命令接收。

架构:
    插件层继承 PluginHandler -> 实现 handle() 方法
    接收层 CommandReceiver 调用 Handler
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from contextvars import ContextVar

from .compat import (
    NONEBOT_AVAILABLE,
    MessageEvent,
    GroupMessageEvent,
    Matcher,
)

# 上下文变量：存储当前处理的事件
_current_event_var: ContextVar[Optional[MessageEvent]] = ContextVar('current_event', default=None)


class PluginHandler(ABC):
    """
    插件业务逻辑处理器基类
    
    子类只需实现 handle() 方法，使用 send/reply 发送消息。
    """
    
    # 元数据（子类配置）
    name: str = ""
    description: str = ""
    command: Optional[str] = None
    aliases: Optional[set] = None
    priority: int = 10
    block: bool = True
    feature_name: Optional[str] = None
    hidden_in_help: bool = False
    
    def __init__(self) -> None:
        self._matcher: Optional[Matcher] = None
    
    @abstractmethod
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理命令（子类必须实现）"""
        pass
    
    async def handle_error(self, error: Exception) -> None:
        """处理错误（可重写）"""
        await self.send(f"处理出错: {error}", finish=True)
    
    async def send(self, message: Any, *, at: bool = False, finish: bool = False) -> None:
        """
        发送消息
        
        Args:
            message: 消息内容
            at: 是否@发送者（仅群聊有效）
            finish: 是否结束会话
        """
        if not self._current_matcher:
            return
        
        if at and NONEBOT_AVAILABLE:
            event = _current_event_var.get()
            if event:
                from ..utils import build_at_message
                message = build_at_message(event.user_id, str(message))
        
        if finish:
            await self._current_matcher.finish(message)
        else:
            await self._current_matcher.send(message)
    
    async def reply(self, message: Any, *, finish: bool = False) -> None:
        """回复用户（自动@）"""
        await self.send(message, at=True, finish=finish)
    
    @property
    def _event(self) -> Optional[MessageEvent]:
        """获取当前事件"""
        return _current_event_var.get()
    
    @property
    def is_group(self) -> bool:
        """是否为群聊"""
        return isinstance(self._event, GroupMessageEvent)


class MessageHandler(PluginHandler):
    """消息处理器基类 - 处理所有消息"""
    
    message_priority: int = 1
    message_block: bool = False
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """转发到 handle_message"""
        await self.handle_message(event)
    
    @abstractmethod
    async def handle_message(self, event: MessageEvent) -> None:
        """处理消息（子类必须实现）"""
        pass
