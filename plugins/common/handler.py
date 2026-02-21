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

try:
    from nonebot.adapters.onebot.v11 import (
        MessageEvent, GroupMessageEvent
    )
    from nonebot.matcher import Matcher
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class Matcher: pass
    class MessageEvent: pass
    class GroupMessageEvent: pass


# 上下文变量：存储当前处理的事件
_current_event_var: ContextVar[Optional[MessageEvent]] = ContextVar('current_event', default=None)


class PluginHandler(ABC):
    """
    插件业务逻辑处理器基类 - 只负责业务处理
    
    此类属于插件层，职责:
    1. 实现业务逻辑（handle 方法）
    2. 通过协议接口使用下层服务
    3. 不直接处理命令接收
    
    Attributes:
        name: 插件显示名称
        description: 功能描述
        command: 命令名（不带/）
        feature_name: 功能开关名
        priority: 处理器优先级
        block: 是否阻止后续处理器
        hidden_in_help: 是否在帮助中隐藏
    """
    
    # ========== 元数据（子类配置）==========
    name: str = ""
    description: str = ""
    version: str = "2.2.2"
    author: str = "Lichlet"
    
    command: Optional[str] = None
    aliases: Optional[set] = None
    priority: int = 10
    block: bool = True
    
    feature_name: Optional[str] = None
    hidden_in_help: bool = False
    
    def __init__(self) -> None:
        """初始化处理器"""
        self._current_matcher: Optional[Matcher] = None
    
    @abstractmethod
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理命令（子类必须实现）
        
        Args:
            event: 消息事件对象
            args: 命令参数（已去除首尾空格）
        """
        pass
    
    async def handle_error(self, error: Exception) -> None:
        """处理错误（可重写）"""
        await self.finish(f"处理出错: {str(error)}")
    
    # ========== 便捷方法 ==========
    
    async def send(self, message: Any) -> None:
        """发送消息（不结束会话）"""
        if self._current_matcher:
            await self._current_matcher.send(message)
    
    async def finish(self, message: Any) -> None:
        """发送消息并结束会话"""
        if self._current_matcher:
            await self._current_matcher.finish(message)
    
    async def reply(self, text: str, at_user: bool = True) -> None:
        """回复用户（自动@发送者）"""
        if not NONEBOT_AVAILABLE:
            return
        
        current_event = self._current_event
        if not current_event:
            await self.send(text)
            return
        
        if at_user:
            try:
                from ..utils import build_at_message
                msg = build_at_message(current_event.user_id, text)
                await self.send(msg)
            except ImportError:
                await self.send(text)
        else:
            await self.send(text)
    
    @property
    def _current_event(self) -> Optional[MessageEvent]:
        """获取当前处理的事件（从上下文变量）"""
        return _current_event_var.get()
    
    @property
    def is_group_chat(self) -> bool:
        """是否为群聊"""
        return isinstance(self._current_event, GroupMessageEvent)


class MessageHandler(PluginHandler):
    """
    消息处理器基类 - 处理所有消息而非特定命令
    
    用于监听所有群聊消息的场景。
    
    Attributes:
        message_priority: 消息处理器优先级
        message_block: 是否阻止后续处理器
    """
    
    message_priority: int = 1
    message_block: bool = False
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """对于 MessageHandler，args 包含完整消息文本"""
        await self.handle_message(event)
    
    async def handle_message(self, event: MessageEvent) -> None:
        """
        处理消息（子类必须实现）
        
        Args:
            event: 消息事件
        """
        raise NotImplementedError("MessageHandler 必须实现 handle_message 方法")
