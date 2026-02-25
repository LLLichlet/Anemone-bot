"""
命令接收器模块 - 接收消息并控制发送频率

使用 buffer 控制同群消息间隔，避免风控。
处理逻辑仍在 NoneBot 上下文中执行。
"""

import asyncio
from contextvars import ContextVar
from typing import Optional, Callable

from .compat import (
    NONEBOT_AVAILABLE,
    MessageEvent,
    GroupMessageEvent,
    Matcher,
    CommandArg,
)

if NONEBOT_AVAILABLE:
    from nonebot import on_command, on_message
    from nonebot.exception import FinishedException
else:
    class FinishedException(Exception):
        pass
    def on_command(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs): return lambda f: f
        return FakeMatcher()
    def on_message(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs): return lambda f: f
        return FakeMatcher()

from .protocols import ServiceLocator, BanServiceProtocol
from .config import config
from .handler import PluginHandler, MessageHandler, _current_event_var

# ContextVar 存储当前请求的 matcher（解决并发冲突）
_current_matcher_var: ContextVar[Optional[Matcher]] = ContextVar('_current_matcher', default=None)


class CommandReceiver:
    """命令接收器 - 带频率控制"""
    
    def __init__(self, handler: PluginHandler) -> None:
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        self._register_to_registry()
        if NONEBOT_AVAILABLE:
            self._register_command()
    
    def _register_to_registry(self) -> None:
        try:
            from .services.registry import PluginRegistry, PluginInfo
            registry = PluginRegistry.get_instance()
            info = PluginInfo(
                name=self._handler.name,
                description=self._handler.description,
                command=self._handler.command,
                aliases=self._handler.aliases,
                feature_name=self._handler.feature_name,
                usage=self._get_usage(),
                is_message_plugin=False,
                hidden=self._handler.hidden_in_help
            )
            registry.register(info)
        except Exception:
            pass
    
    def _get_usage(self) -> str:
        if self._handler.command:
            return f"/{self._handler.command} [参数]"
        return "自动触发"
    
    def _register_command(self) -> None:
        if not self._handler.command:
            raise ValueError(f"Handler {self._handler.name} 没有设置 command")
        try:
            self._matcher = on_command(
                self._handler.command,
                aliases=self._handler.aliases,
                priority=self._handler.priority,
                block=self._handler.block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" not in str(e):
                raise
    
    def _create_handler(self) -> Callable:
        """创建处理器 - 带频率控制"""
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent, args=CommandArg()):
            # 权限检查
            if not receiver._check_permission(event):
                await matcher.finish("笨蛋,你的账号被拉黑了!")
                return
            
            # 功能开关检查
            if not receiver._check_feature():
                await matcher.finish("笨蛋,这个功能被关掉了!")
                return
            
            # 执行处理（在 NoneBot 上下文中）
            event_token = _current_event_var.set(event)
            matcher_token = _current_matcher_var.set(matcher)
            try:
                content = args.extract_plain_text().strip() if args else ""
                
                try:
                    await receiver._handler.handle(event, content)
                except FinishedException:
                    raise
                except Exception as e:
                    await receiver._handler.handle_error(e)
            finally:
                _current_event_var.reset(event_token)
                _current_matcher_var.reset(matcher_token)
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        ban_service = ServiceLocator.get(BanServiceProtocol)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        if not self._handler.feature_name:
            return True
        return config.is_enabled(self._handler.feature_name)


class MessageReceiver:
    """消息接收器 - 带频率控制"""
    
    def __init__(self, handler: MessageHandler) -> None:
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        self._register_to_registry()
        if NONEBOT_AVAILABLE:
            self._register_message_handler()
    
    def _register_to_registry(self) -> None:
        try:
            from .services.registry import PluginRegistry, PluginInfo
            registry = PluginRegistry.get_instance()
            info = PluginInfo(
                name=self._handler.name,
                description=self._handler.description,
                command=None,
                aliases=None,
                feature_name=self._handler.feature_name,
                usage="自动触发",
                is_message_plugin=True,
                hidden=self._handler.hidden_in_help
            )
            registry.register(info)
        except Exception:
            pass
    
    def _register_message_handler(self) -> None:
        try:
            self._matcher = on_message(
                priority=self._handler.message_priority,
                block=self._handler.message_block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" not in str(e):
                raise
    
    def _create_handler(self) -> Callable:
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent):
            if not receiver._check_permission(event):
                return
            if not receiver._check_feature():
                return
            
            # 执行处理（在 NoneBot 上下文中）
            event_token = _current_event_var.set(event)
            matcher_token = _current_matcher_var.set(matcher)
            try:
                try:
                    await receiver._handler.handle_message(event)
                except FinishedException:
                    raise
                except Exception as e:
                    print(f"Message handler error: {e}")
            finally:
                _current_event_var.reset(event_token)
                _current_matcher_var.reset(matcher_token)
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        ban_service = ServiceLocator.get(BanServiceProtocol)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        if not self._handler.feature_name:
            return True
        return config.is_enabled(self._handler.feature_name)
