"""
处理器基类模块 - 插件业务逻辑接口

Handler 只负责业务处理，不处理命令接收。
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

# 上下文变量：存储当前处理的事件和 matcher
_current_event_var: ContextVar[Optional[MessageEvent]] = ContextVar('current_event', default=None)


class PluginHandler(ABC):
    """插件业务逻辑处理器基类"""
    
    # 元数据（子类配置）
    name: str = ""
    description: str = ""
    command: Optional[str] = None
    aliases: Optional[set] = None
    priority: int = 10
    block: bool = True
    feature_name: Optional[str] = None
    hidden_in_help: bool = False
    
    @abstractmethod
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理命令（子类必须实现）"""
        pass
    
    async def handle_error(self, error: Exception) -> None:
        """处理错误（可重写）"""
        await self.send(f"处理出错: {error}", finish=True)
    
    def _get_current_matcher(self) -> Optional[Matcher]:
        """获取当前请求的 matcher（从 ContextVar，支持并发）"""
        # 避免循环导入，延迟导入
        from .receiver import _current_matcher_var
        return _current_matcher_var.get()
    
    async def send(self, message: Any, *, at: bool = False, finish: bool = False) -> None:
        """
        发送消息（默认使用缓冲，防风控）
        
        Args:
            message: 消息内容
            at: 是否@发送者
            finish: 是否结束会话
        """
        matcher = self._get_current_matcher()
        if not matcher:
            return
        
        from .buffer import get_buffer
        from .config import config
        
        # 构建消息
        if at and NONEBOT_AVAILABLE:
            event = _current_event_var.get()
            if event:
                from ..utils import build_at_message
                msg = build_at_message(event.user_id, str(message))
            else:
                msg = message
        else:
            msg = message
        
        # 并发调试模式：附加buffer队列数量
        if config.debug_concurrent:
            buffer = get_buffer()
            queue_size = buffer.qsize()
            msg = f"[{queue_size}]{msg}"
        
        # 获取群号
        event = _current_event_var.get()
        group_id = event.group_id if event and hasattr(event, 'group_id') else 0
        
        # 使用缓冲发送
        if finish:
            # finish 需要立即执行并结束
            await matcher.finish(msg)
        else:
            await get_buffer().send(group_id, msg, matcher.send)
    
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
        """默认调用 handle_message"""
        await self.handle_message(event)
    
    async def handle_message(self, event: MessageEvent) -> None:
        """处理消息（子类重写）"""
        pass
