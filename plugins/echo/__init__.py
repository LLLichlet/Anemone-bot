"""
复读插件

随机复读群聊消息，有概率倒着复读
使用新架构（MessageHandler + MessageReceiver）
"""
import random

try:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class GroupMessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    MessageHandler,
    MessageReceiver,
    config,
)


class EchoHandler(MessageHandler):
    """复读处理器"""
    
    name = "复读"
    description = "随机复读群聊消息，有概率倒着复读"
    feature_name = "echo"
    message_priority = 2  # 优先级比随机回复低
    message_block = False
    
    def _should_echo(self, event: GroupMessageEvent) -> tuple[bool, bool]:
        """
        判断是否满足复读条件
        
        Returns:
            (是否复读, 是否倒序)
        """
        if not NONEBOT_AVAILABLE:
            return False, False
            
        if event.user_id == event.self_id:
            return False, False
        
        message = event.get_plaintext().strip()
        
        # 过滤命令消息
        if message.startswith('/'):
            return False, False
        
        # 过滤太短的消
        if len(message) < 2:
            return False, False
        
        # 获取配置
        echo_prob = config.echo_probability
        reverse_prob = config.echo_reverse_probability
        
        # 判断是否复读
        if random.random() >= echo_prob:
            return False, False
        
        # 判断是否倒序（在复读的基础上）
        is_reverse = random.random() < reverse_prob
        
        return True, is_reverse
    
    async def handle_message(self, event: GroupMessageEvent) -> None:
        """处理群聊消息"""
        if not NONEBOT_AVAILABLE:
            return
        
        should_echo, is_reverse = self._should_echo(event)
        
        if not should_echo:
            return
        
        # 获取消息内容
        message = event.get_plaintext().strip()
        
        # 处理消息
        if is_reverse:
            # 倒序复读
            reply = message[::-1]
        else:
            # 正序复读
            reply = message
        
        # 发送回复
        await self.send(reply)


# 创建处理器和接收器
handler = EchoHandler()
receiver = MessageReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage="无命令，自动触发",
        extra={"author": "Lichlet", "version": "2.3.1"}
    )
