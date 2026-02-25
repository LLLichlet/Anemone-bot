"""
消息构建工具 - QQ 消息格式化

提供便捷的 QQ 消息构建函数，避免重复的 Message/MessageSegment 操作。

使用示例:
    >>> from plugins.utils import build_at_message, build_reply_message
    >>> from nonebot.adapters.onebot.v11 import Message
    >>> 
    >>> # 简单 @ 回复
    >>> msg = build_at_message(123456789, "这是回复内容")
    >>> 
    >>> # 带前缀的回复
    >>> msg = build_reply_message(123456789, "请输入正确格式", prefix="错误")

设计原则:
    - 纯函数：不修改输入，返回新对象
    - 类型安全：完整的类型提示
    - 链式友好：返回值可直接用于后续操作
"""

from typing import Optional, Union
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


def build_reply_message(
    user_id: int,
    text: str,
    prefix: Optional[str] = None
) -> Message:
    """
    构建回复消息
    
    可选择添加前缀，生成的消息格式: "[@user] [prefix] text" 或 "@user text"
    
    Args:
        user_id: 用户 QQ 号
        text: 回复文本内容
        prefix: 可选的前缀文本（如"错误"、"提示"等）
        
    Returns:
        Message 对象
        
    Example:
        >>> msg = build_reply_message(123456789, "操作成功")
        >>> msg = build_reply_message(123456789, "请输入正确格式", prefix="错误")
    """
    msg = Message()
    msg.append(MessageSegment.at(user_id))
    msg.append(" ")
    if prefix:
        msg.append(f"[{prefix}] ")
    msg.append(text)
    return msg


def ensure_message(content: Union[str, Message]) -> Message:
    """
    确保内容是 Message 对象
    
    如果输入是字符串，转换为 Message；如果已经是 Message，直接返回。
    
    Args:
        content: 字符串或 Message 对象
        
    Returns:
        Message 对象
        
    Example:
        >>> msg1 = ensure_message("纯文本")  # 转为 Message
        >>> msg2 = ensure_message(msg1)     # 直接返回 msg1
    """
    if isinstance(content, Message):
        return content
    return Message(content)
