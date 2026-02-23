"""
消息构建工具 - QQ 消息格式化

提供便捷的 QQ 消息构建函数，避免重复的 Message/MessageSegment 操作。

使用示例:
    >>> from plugins.utils import build_at_message
    >>> from nonebot.adapters.onebot.v11 import Message
    >>> 
    >>> # 简单 @ 回复
    >>> msg = build_at_message(123456789, "这是回复内容")

设计原则:
    - 纯函数：不修改输入，返回新对象
    - 类型安全：完整的类型提示
    - 链式友好：返回值可直接用于后续操作
"""

from nonebot.adapters.onebot.v11 import Message, MessageSegment


def build_at_message(user_id: int, text: str) -> Message:
    """
    构建 @ 某人的消息
    
    生成的消息格式: "@user text"
    
    Args:
        user_id: 用户 QQ 号
        text: 回复文本内容
        
    Returns:
        Message 对象，可直接用于 finish/send
        
    Example:
        >>> msg = build_at_message(123456789, "你好")
        >>> await handler.finish(msg)
        
        # 输出效果: @用户 你好
    """
    msg = Message()
    msg.append(MessageSegment.at(user_id))
    msg.append(" ")
    msg.append(text)
    return msg
