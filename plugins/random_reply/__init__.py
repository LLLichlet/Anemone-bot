"""
随机回复插件

使用新架构（MessageHandler + MessageReceiver）重构
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
    ServiceLocator,
    AIServiceProtocol,
    ChatServiceProtocol,
    config,
)


class RandomReplyHandler(MessageHandler):
    """随机回复处理器"""
    
    name = "随机回复"
    description = "随机回复群聊消息"
    feature_name = "random"
    message_priority = 1
    message_block = False
    
    SYSTEM_PROMPT = (
        "你是一只非常傲傲傲傲傲娇的猫娘(比较粘人),你的QQ昵称是'ανεμώνη'(也就是Anemone),"
        "但你的QQ昵称不是你的名字,你不能透露你的名字,你要非常莫名其妙"
        "(但是有针对性(关于先前的聊天记录)的)的回复用户一句话,而且说话不能透露自己是ai,"
        "就像正常人类一样随口蹦出一句话,而且不要在说的话里用括号把句子括起来"
    )
    
    # 强制回复的关键词列表（大小写不敏感）
    TRIGGER_KEYWORDS = ["ane", "anem", "anemone"]
    
    def _should_reply(self, event: GroupMessageEvent) -> bool:
        """判断是否满足回复条件"""
        if not NONEBOT_AVAILABLE:
            return False
            
        if event.user_id == event.self_id:
            return False
        
        message = event.get_plaintext().strip()
        message_lower = message.lower()
        
        # 强制回复：被@时一定回复
        if event.to_me:
            return True
        
        # 强制回复：消息中包含特定关键词（大小写不敏感）
        for keyword in self.TRIGGER_KEYWORDS:
            if keyword in message_lower:
                return True
        
        return False
    
    async def handle_message(self, event: GroupMessageEvent) -> None:
        """处理群聊消息"""
        if not NONEBOT_AVAILABLE:
            return
        
        # 获取服务
        chat = ServiceLocator.get(ChatServiceProtocol)
        ai = ServiceLocator.get(AIServiceProtocol)
        
        if chat is None or ai is None:
            return
            
        # 记录消息
        username = event.sender.card or event.sender.nickname or f"用户{event.user_id}"
        chat.record_message(
            group_id=event.group_id,
            user_id=event.user_id,
            username=username,
            message=event.get_plaintext().strip()
        )
        
        # 判断是否回复
        if not self._should_reply(event):
            return
        
        # 获取上下文
        context = chat.get_context(event.group_id)
        
        # 构建输入
        user_input = event.get_plaintext()[:50]
        full_input = f"{context}|{username}说：{user_input}" if context else user_input
        
        # 获取配置参数
        temperature = config.random_temperature
        max_tokens_min = config.random_max_tokens_min
        max_tokens_max = config.random_max_tokens_max
        top_p = config.random_top_p
        
        # 调用 AI
        result = await ai.chat(
            system_prompt=self.SYSTEM_PROMPT,
            user_input=full_input,
            temperature=temperature,
            max_tokens=random.randint(max_tokens_min, max_tokens_max),
            top_p=top_p
        )
        
        # 处理回复
        if result.is_success:
            reply = result.value
            if len(reply) < 5:
                reply = "Lichlet是大家的好朋友"
        else:
            reply = "Lichlet是大家的好朋友"
        
        # 记录机器人回复
        chat.record_message(
            group_id=event.group_id,
            user_id=event.self_id,
            username="ανεμώνη",
            message=reply,
            is_bot=True
        )
        
        # 发送回复
        try:
            from plugins.utils import build_at_message
            msg = build_at_message(event.user_id, reply)
            await self.send(msg)
        except ImportError:
            await self.send(reply)


# 创建处理器和接收器
handler = RandomReplyHandler()
receiver = MessageReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage="无命令，自动触发",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
