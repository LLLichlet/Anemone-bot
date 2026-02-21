"""
聊天服务模块 - 聊天记录和冷却管理

服务层 - 实现 ChatServiceProtocol 协议
"""

import re
import time
from collections import deque
from typing import Dict, Deque, List, Tuple, Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..config import config
from ..protocols import (
    ChatServiceProtocol,
    ServiceLocator,
)


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    timestamp: float
    user_id: int
    username: str
    message: str
    is_bot: bool = False
    
    @property
    def time_str(self) -> str:
        """格式化时间字符串"""
        from datetime import datetime
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")


class ChatService(ServiceBase, ChatServiceProtocol):
    """
    聊天服务类 - 管理群聊历史和冷却
    
    实现 ChatServiceProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        self._history: Dict[int, Deque[ChatMessage]] = {}
        self._cooldown: Dict[int, float] = {}
        self.logger = logging.getLogger("plugins.common.services.chat")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注意：初始化完成后才注册到 ServiceLocator。
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(ChatServiceProtocol, self)
        self.logger.info("Chat Service initialized")
    
    def _get_or_create_history(self, group_id: int) -> Deque[ChatMessage]:
        """获取或创建群聊历史"""
        if group_id not in self._history:
            self._history[group_id] = deque(maxlen=config.max_history_per_group)
        return self._history[group_id]
    
    @staticmethod
    def _clean_cq_codes(message: str) -> str:
        """清理消息中的 CQ 码"""
        cleaned = re.sub(r'\[CQ:[^\]]+\]', '', message)
        return cleaned.strip()
    
    # ========== ChatServiceProtocol 实现 ==========
    
    def record_message(
        self,
        group_id: int,
        user_id: int,
        username: str,
        message: str,
        is_bot: bool = False
    ) -> None:
        """记录聊天消息"""
        self.ensure_initialized()
        
        history = self._get_or_create_history(group_id)
        clean_message = self._clean_cq_codes(message)
        
        entry = ChatMessage(
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            message=clean_message,
            is_bot=is_bot
        )
        
        history.append(entry)
    
    def get_context(self, group_id: int, limit: int = 50) -> str:
        """获取格式化的聊天上下文"""
        self.ensure_initialized()
        
        if group_id not in self._history or not self._history[group_id]:
            return ""
        
        messages = list(self._history[group_id])
        messages = [m for m in messages if not m.is_bot]
        
        recent = messages[-limit:] if len(messages) > limit else messages
        
        lines = []
        for msg in recent:
            content = msg.message[:80]
            if content:
                lines.append(f"{msg.username}: {content}")
        
        if lines:
            return "最近的聊天：\n" + "\n".join(lines) + "\n\n"
        return ""
    
    def check_cooldown(self, group_id: int) -> bool:
        """检查群组冷却时间是否已过"""
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return True
        
        elapsed = time.time() - self._cooldown[group_id]
        return elapsed >= config.random_reply_cooldown
    
    def set_cooldown(self, group_id: int) -> None:
        """设置群组冷却时间"""
        self.ensure_initialized()
        self._cooldown[group_id] = time.time()
    
    # ========== 额外方法（不在协议中）==========
    
    def get_messages(
        self,
        group_id: int,
        limit: int = 50,
        include_bot: bool = False
    ) -> List[ChatMessage]:
        """获取消息列表"""
        self.ensure_initialized()
        
        if group_id not in self._history:
            return []
        
        messages = list(self._history[group_id])
        if not include_bot:
            messages = [m for m in messages if not m.is_bot]
        
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_recent_users(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Tuple[int, str]]:
        """获取最近活跃用户"""
        self.ensure_initialized()
        
        if group_id not in self._history or not self._history[group_id]:
            return []
        
        seen = set()
        users = []
        
        for msg in reversed(self._history[group_id]):
            if msg.user_id and msg.user_id not in seen:
                seen.add(msg.user_id)
                users.append((msg.user_id, msg.username))
                if len(users) >= limit:
                    break
        
        return users
    
    def get_cooldown_remaining(self, group_id: int) -> float:
        """获取剩余冷却秒数"""
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return 0
        
        remaining = config.random_reply_cooldown - (time.time() - self._cooldown[group_id])
        return max(0, remaining)
    
    def clear_history(self, group_id: Optional[int] = None) -> None:
        """清除聊天记录"""
        self.ensure_initialized()
        
        if group_id is None:
            self._history.clear()
            self.logger.info("Cleared all chat history")
        else:
            self._history.pop(group_id, None)
            self.logger.info(f"Cleared history for group {group_id}")
    
    def clear_cooldown(self, group_id: Optional[int] = None) -> None:
        """清除冷却时间"""
        self.ensure_initialized()
        
        if group_id is None:
            self._cooldown.clear()
        else:
            self._cooldown.pop(group_id, None)


def get_chat_service() -> ChatService:
    """获取聊天服务单例（向后兼容）"""
    return ChatService.get_instance()
