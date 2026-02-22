"""
命令接收器模块 - 负责接收命令消息

此模块属于接收层，职责:
1. 注册 NoneBot 命令处理器
2. 接收用户输入
3. 执行前置检查（权限、功能开关）
4. 调用插件层 Handler 处理业务逻辑

依赖关系:
    接收层 ──依赖──> 协议层 <──实现── 服务层
    接收层 ──依赖──> 插件层 (Handler)
"""

from typing import Optional, Callable

try:
    from nonebot import on_command, on_message
    from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
    from nonebot.matcher import Matcher
    from nonebot.params import CommandArg
    from nonebot.exception import FinishedException
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class Matcher: pass
    class MessageEvent: pass
    class GroupMessageEvent: pass
    class FinishedException(Exception): pass
    def on_command(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs):
                return lambda f: f
        return FakeMatcher()
    def on_message(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs):
                return lambda f: f
        return FakeMatcher()
    def CommandArg():
        return None

# 依赖协议层
from .protocols import (
    ServiceLocator,
    BanServiceProtocol,
    ConfigProviderProtocol,
)


def _ensure_service_initialized(protocol_type, service_class):
    """确保服务已初始化并注册到 ServiceLocator"""
    service = ServiceLocator.get(protocol_type)
    if service is None:
        # 尝试初始化服务
        try:
            instance = service_class.get_instance()
            instance.initialize()
            service = ServiceLocator.get(protocol_type)
        except Exception:
            pass
    return service

# 依赖插件层
from .handler import PluginHandler, MessageHandler, _current_event_var


class CommandReceiver:
    """
    命令接收器 - 负责接收命令并调用处理器
    
    此类属于接收层，职责:
    1. 注册 NoneBot 命令处理器
    2. 接收用户输入
    3. 执行权限检查、功能开关检查
    4. 调用 PluginHandler.handle() 执行业务逻辑
    """
    
    def __init__(self, handler: PluginHandler) -> None:
        """
        初始化命令接收器
        
        Args:
            handler: 业务逻辑处理器实例
        """
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        
        # 注册到插件注册表
        self._register_to_registry()
        
        # 注册 NoneBot 命令处理器
        if NONEBOT_AVAILABLE:
            self._register_command()
    
    def _register_to_registry(self) -> None:
        """注册到插件注册表"""
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
        """获取使用说明"""
        if self._handler.command:
            return f"/{self._handler.command} [参数]"
        return "自动触发"
    
    def _register_command(self) -> None:
        """注册 NoneBot 命令处理器"""
        if not self._handler.command:
            raise ValueError(f"Handler {self._handler.name} 没有设置 command 属性")
        
        try:
            self._matcher = on_command(
                self._handler.command,
                aliases=self._handler.aliases,
                priority=self._handler.priority,
                block=self._handler.block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" in str(e):
                pass
            else:
                raise
    
    def _create_handler(self) -> Callable:
        """创建处理器包装函数"""
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent, args=CommandArg()):
            """实际的命令处理器"""
            token = _current_event_var.set(event)
            
            try:
                # 权限检查
                if not receiver._check_permission(event):
                    await matcher.finish("笨蛋,你的账号被拉黑了!")
                    return
                
                # 功能开关检查
                if not receiver._check_feature():
                    await matcher.finish("笨蛋,这个功能被关掉了!")
                    return
                
                # 提取参数
                content = args.extract_plain_text().strip() if args else ""
                
                # 设置 handler 的 matcher
                receiver._handler._current_matcher = matcher
                
                # 执行业务逻辑
                try:
                    await receiver._handler.handle(event, content)
                except FinishedException:
                    raise
                except Exception as e:
                    await receiver._handler.handle_error(e)
                    
            finally:
                _current_event_var.reset(token)
                receiver._handler._current_matcher = None
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        """检查用户权限"""
        from .services import BanService
        ban_service = _ensure_service_initialized(BanServiceProtocol, BanService)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        """检查功能是否开启"""
        if not self._handler.feature_name:
            return True
        
        from .services import ConfigProvider
        config_provider = _ensure_service_initialized(ConfigProviderProtocol, ConfigProvider)
        if config_provider is not None:
            return config_provider.is_feature_enabled(self._handler.feature_name)
        
        return True


class MessageReceiver:
    """
    消息接收器 - 负责接收所有消息并调用处理器
    """
    
    def __init__(self, handler: MessageHandler) -> None:
        """
        初始化消息接收器
        
        Args:
            handler: 消息处理器实例（必须是 MessageHandler 类型）
        """
        if not isinstance(handler, MessageHandler):
            raise TypeError("MessageReceiver 只接受 MessageHandler 类型")
        
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        
        # 注册到插件注册表
        self._register_to_registry()
        
        # 注册 NoneBot 消息处理器
        if NONEBOT_AVAILABLE:
            self._register_message()
    
    def _register_to_registry(self) -> None:
        """注册到插件注册表"""
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
    
    def _register_message(self) -> None:
        """注册 NoneBot 消息处理器"""
        try:
            self._matcher = on_message(
                priority=self._handler.message_priority,
                block=self._handler.message_block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" in str(e):
                pass
            else:
                raise
    
    def _create_handler(self) -> Callable:
        """创建消息处理器包装函数"""
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent):
            """实际的消息处理器"""
            # 只处理群聊消息（MessageHandler 设计用于群聊场景）
            if not isinstance(event, GroupMessageEvent):
                return
            
            token = _current_event_var.set(event)
            
            try:
                # 功能开关检查
                if not receiver._check_feature():
                    return
                
                # 权限检查
                if not receiver._check_permission(event):
                    return
                
                # 设置 handler 的 matcher
                receiver._handler._current_matcher = matcher
                
                # 执行处理
                try:
                    await receiver._handler.handle_message(event)
                except Exception as e:
                    await receiver._handler.handle_error(e)
                    
            finally:
                _current_event_var.reset(token)
                receiver._handler._current_matcher = None
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        """检查用户权限"""
        from .services import BanService
        ban_service = _ensure_service_initialized(BanServiceProtocol, BanService)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        """检查功能是否开启"""
        if not self._handler.feature_name:
            return True
        
        from .services import ConfigProvider
        config_provider = _ensure_service_initialized(ConfigProviderProtocol, ConfigProvider)
        if config_provider is not None:
            return config_provider.is_feature_enabled(self._handler.feature_name)
        
        return True


# ========== 便捷函数 ==========

def register_command(handler: PluginHandler) -> CommandReceiver:
    """注册命令处理器（便捷函数）"""
    return CommandReceiver(handler)


def register_message(handler: MessageHandler) -> MessageReceiver:
    """注册消息处理器（便捷函数）"""
    return MessageReceiver(handler)
