"""
帮助插件

自动从 PluginRegistry 读取插件元数据，动态生成帮助信息。
使用新架构（PluginHandler + CommandReceiver）重构
"""
try:
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    ConfigProviderProtocol,
    PluginRegistry,
)


class HelpHandler(PluginHandler):
    """帮助处理器"""
    
    name = "帮助"
    description = "查看插件使用帮助"
    command = "帮助"
    priority = 10
    feature_name = None
    
    async def handle(self, event, args: str) -> None:
        """处理帮助命令"""
        registry = PluginRegistry.get_instance()
        
        plugins = registry.get_command_plugins(include_hidden=False)
        
        if not plugins:
            await self.finish("当前没有可用的功能")
            return
        
        # 获取配置提供者
        config = ServiceLocator.get(ConfigProviderProtocol)
        
        enabled_plugins = []
        for plugin in plugins:
            if plugin.command == "帮助":
                continue
            
            # 通过协议层检查功能开关
            if plugin.feature_name and config is not None:
                is_enabled = config.is_feature_enabled(plugin.feature_name)
                if not is_enabled:
                    continue
            
            enabled_plugins.append(plugin)
        
        lines = ["功能列表:"]
        
        for i, plugin in enumerate(enabled_plugins, 1):
            cmd_text = f"/{plugin.command}"
            if plugin.aliases:
                aliases_text = ", ".join(f"/{a}" for a in sorted(plugin.aliases))
                cmd_text = f"{cmd_text} ({aliases_text})"
            
            lines.append(f"{i}. {plugin.name}: {cmd_text}")
            lines.append(f"   {plugin.description}")
        
        message_plugins = registry.get_message_plugins(include_hidden=False)
        for plugin in message_plugins:
            if plugin.feature_name and config is not None:
                is_enabled = config.is_feature_enabled(plugin.feature_name)
                if not is_enabled:
                    continue
            
            lines.append(f"{len(enabled_plugins) + 1}. {plugin.name}: 自动触发")
            lines.append(f"   {plugin.description}")
            break
        
        if len(lines) == 1:
            lines.append("当前所有功能已关闭，请联系管理员")
        
        await self.finish("\n".join(lines))


# 创建处理器和接收器
handler = HelpHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command}",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
