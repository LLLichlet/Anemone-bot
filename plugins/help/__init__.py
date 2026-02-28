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
    config,
    PluginRegistry,
)


class HelpHandler(PluginHandler):
    """帮助处理器"""
    
    name = "帮助"
    description = "查看插件使用帮助"
    command = "help"
    aliases = {"帮助"}
    priority = 10
    feature_name = None
    
    async def handle(self, event, args: str) -> None:
        """处理帮助命令"""
        registry = PluginRegistry.get_instance()
        
        # 如果有参数，显示特定指令的详细信息
        if args:
            await self._show_plugin_detail(registry, args.strip())
            return
        
        # 否则显示功能列表
        await self._show_plugin_list(registry)
    
    async def _show_plugin_detail(self, registry: PluginRegistry, query: str) -> None:
        """显示特定插件的详细信息"""
        # 去掉可能的前导 /
        query = query.lstrip("/")
        
        # 特殊处理 help 自身
        if query in ("help", "帮助"):
            lines = ["/help 帮助"]
            lines.append("别名: /帮助")
            lines.append("描述: 查看插件使用帮助")
            lines.append("用法: /help [指令名] - 显示功能列表或查看指定指令详细用法")
            await self.send("\n".join(lines), finish=True)
            return
        
        # 通过命令名查找插件
        plugin = registry.get_plugin_by_command(query)
        
        if plugin is None or plugin.hidden:
            await self.reply(f"未找到指令: /{query}")
            return
        
        # 检查功能开关
        if plugin.feature_name and not config.is_enabled(plugin.feature_name):
            await self.reply(f"该功能当前已关闭: /{query}")
            return
        
        lines = [f"/{plugin.command} {plugin.name}"]
        
        if plugin.aliases:
            aliases_text = ", ".join(f"/{a}" for a in sorted(plugin.aliases))
            lines.append(f"别名: {aliases_text}")
        
        lines.append(f"描述: {plugin.description}")
        
        if plugin.usage:
            lines.append(f"用法: {plugin.usage}")
        
        await self.send("\n".join(lines), finish=True)
    
    async def _show_plugin_list(self, registry: PluginRegistry) -> None:
        """显示所有可用功能列表"""
        plugins = registry.get_command_plugins(include_hidden=False)
        
        if not plugins:
            await self.send("欢迎使用Anemone bot!\n\n当前没有可用的功能", finish=True)
            return
        
        enabled_plugins = []
        for plugin in plugins:
            if plugin.command == "help":
                continue
            
            # 检查功能开关
            if plugin.feature_name and not config.is_enabled(plugin.feature_name):
                continue
            
            enabled_plugins.append(plugin)
        
        lines = ["欢迎使用Anemone bot!"]
        
        for plugin in enabled_plugins:
            lines.append(f"/{plugin.command} {plugin.name}")
        
        message_plugins = registry.get_message_plugins(include_hidden=False)
        for plugin in message_plugins:
            if plugin.feature_name and not config.is_enabled(plugin.feature_name):
                continue
            
            lines.append(f"(自动触发) {plugin.name}")
        
        if len(enabled_plugins) == 0:
            lines.append("当前所有功能已关闭，请联系管理员")
        
        lines.append("\n使用 /help 指令名 查看详细用法")
        
        await self.send("\n".join(lines), finish=True)


# 创建处理器和接收器
handler = HelpHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command}",
        extra={"author": "Lichlet", "version": "2.3.1"}
    )
