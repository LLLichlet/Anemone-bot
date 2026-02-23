"""
兼容性模块 - 统一处理可选依赖的导入

集中处理 NoneBot 等可选依赖的导入，避免每个文件重复 try/except。
"""

try:
    from nonebot import get_bot
    from nonebot.adapters.onebot.v11 import (
        MessageEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
        Bot,
        Message,
        MessageSegment,
    )
    from nonebot.matcher import Matcher
    from nonebot.plugin import PluginMetadata
    from nonebot.params import CommandArg

    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False

    def get_bot():
        return None

    class MessageEvent:
        pass

    class GroupMessageEvent:
        pass

    class PrivateMessageEvent:
        pass

    class Bot:
        pass

    class Message:
        pass

    class MessageSegment:
        @staticmethod
        def at(user_id):
            return ""

        @staticmethod
        def image(file):
            return ""

    class Matcher:
        async def send(self, msg):
            pass

        async def finish(self, msg):
            pass

    class PluginMetadata:
        def __init__(self, **kwargs):
            pass

    def CommandArg():
        return None


__all__ = [
    "NONEBOT_AVAILABLE",
    "get_bot",
    "MessageEvent",
    "GroupMessageEvent",
    "PrivateMessageEvent",
    "Bot",
    "Message",
    "MessageSegment",
    "Matcher",
    "PluginMetadata",
    "CommandArg",
]
