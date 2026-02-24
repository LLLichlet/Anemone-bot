"""
数学定义查询插件

使用新架构（PluginHandler + CommandReceiver）开发。

功能:
    查询数学名词的定义和解释，使用香蕉空间风格。
    支持中英法德俄日多语言回复。

使用:
    /定义 [数学名词]
    
    例如:
    /定义 群论
    /定义 黎曼猜想
    /定义 拓扑空间

配置:
    QUERY_MATH_ENABLED=True/False      # 功能开关
    QUERY_MATH_TEMPERATURE=0.1         # AI 温度
    QUERY_MATH_MAX_TOKENS=8192         # 最大 token
    QUERY_MATH_TOP_P=0.1               # Top-p 参数
"""

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    AIServiceProtocol,
    config,
    read_prompt,
)


class MathDefinitionHandler(PluginHandler):
    """
    数学定义查询处理器
    
    纯业务逻辑处理器，命令接收由 CommandReceiver 负责。
    """
    
    # 元数据配置
    name = "数学定义查询"
    description = "查询数学名词的定义和解释"
    command = "define"
    aliases = {"定义"}
    feature_name = "math"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理数学定义查询
        
        Args:
            event: 消息事件对象
            args: 命令参数（已去除首尾空格）
        """
        # 参数检查
        if not args:
            await self.reply("请输入要查询的数学名词")
            return
        
        # 读取提示词
        system_prompt = read_prompt("math_def")
        if not system_prompt:
            await self.reply("数学定义系统提示文件不存在，请联系管理员")
            return
        
        # 通过协议层获取 AI 服务
        ai = ServiceLocator.get(AIServiceProtocol)
        if ai is None:
            await self.reply("AI 服务未初始化")
            return
        
        if not ai.is_available:
            await self.reply("AI 服务未配置，无法查询")
            return
        
        # 获取 AI 参数
        temperature = config.math_temperature
        max_tokens = config.math_max_tokens
        top_p = config.math_top_p
        
        # 调用 AI
        result = await ai.chat(
            system_prompt=system_prompt,
            user_input=args,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # 处理结果
        if result.is_success:
            await self.reply(result.value)
        else:
            await self.reply(f"查询失败: {result.error}")


# 创建处理器和接收器
handler = MathDefinitionHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command} (/{' /'.join(handler.aliases)}) [数学名词]",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
