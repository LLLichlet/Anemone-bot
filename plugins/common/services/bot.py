"""
Bot API 服务 - 封装 NoneBot 群管理接口

服务层 - 实现 BotServiceProtocol 协议
"""

from typing import List, Dict, Any, Optional
import random
import logging

try:
    from nonebot import get_bot
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class Bot: pass
    class Message: pass
    class MessageSegment: pass
    def get_bot(): pass

from ..base import ServiceBase, Result
from ..protocols import (
    BotServiceProtocol,
    ServiceLocator,
)


class BotService(ServiceBase, BotServiceProtocol):
    """
    Bot API 服务类 - 封装群管理操作
    
    实现 BotServiceProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        self.logger = logging.getLogger("plugins.common.services.bot")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注意：初始化完成后才注册到 ServiceLocator。
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(BotServiceProtocol, self)
        self.logger.info("Bot Service initialized")
    
    def _get_bot(self) -> Optional[Bot]:
        """获取 Bot 实例"""
        if not NONEBOT_AVAILABLE:
            return None
        try:
            return get_bot()
        except Exception as e:
            self.logger.error(f"Failed to get bot: {e}")
            return None
    
    # ========== BotServiceProtocol 实现 ==========
    
    async def send_message(
        self,
        event,
        message: Any,
        at_user: bool = False
    ) -> Result[bool]:
        """发送消息"""
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            if at_user and hasattr(event, 'user_id'):
                message = MessageSegment.at(event.user_id) + MessageSegment.text(" ") + message
            
            await bot.send(event, message)
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return Result.fail(f"发送消息失败: {e}")
    
    async def ban_user(self, group_id: int, user_id: int, duration: int) -> Result[bool]:
        """禁言用户"""
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            await bot.set_group_ban(
                group_id=group_id,
                user_id=user_id,
                duration=duration
            )
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Failed to ban user: {e}")
            return Result.fail(f"禁言失败: {e}")
    
    # ========== 额外方法（不在协议中）==========
    
    async def ban_random_duration(
        self,
        group_id: int,
        user_id: int,
        min_minutes: int = 1,
        max_minutes: int = 10
    ) -> Result[int]:
        """
        随机时长禁言
        
        Args:
            group_id: QQ群号
            user_id: 用户QQ号
            min_minutes: 最短禁言分钟数
            max_minutes: 最长禁言分钟数
            
        Returns:
            Result[int] - 成功时 value 为实际禁言秒数
        """
        duration_seconds = random.randint(min_minutes, max_minutes) * 60
        
        result = await self.ban_user(group_id, user_id, duration_seconds)
        if result.is_success:
            return Result.success(duration_seconds)
        return Result.fail(result.error)
    
    async def ban_multiple(
        self,
        group_id: int,
        user_ids: List[int],
        duration: int
    ) -> Result[List[int]]:
        """
        批量禁言用户
        
        Args:
            group_id: QQ群号
            user_ids: 用户QQ号列表
            duration: 禁言时长（秒）
            
        Returns:
            Result[List[int]] - 成功禁言的用户ID列表
        """
        banned = []
        failed = []
        
        for user_id in user_ids:
            result = await self.ban_user(group_id, user_id, duration)
            if result.is_success:
                banned.append(user_id)
            else:
                failed.append(user_id)
        
        if failed:
            self.logger.warning(f"Failed to ban {len(failed)} users")
        
        return Result.success(banned)
    
    async def get_group_members(self, group_id: int) -> Result[List[Dict[str, Any]]]:
        """获取群成员列表"""
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            members = await bot.get_group_member_list(group_id=group_id)
            return Result.success(members)
        except Exception as e:
            self.logger.error(f"Failed to get group members: {e}")
            return Result.fail(f"获取群成员列表失败: {e}")


def get_bot_service() -> BotService:
    """获取 Bot 服务单例（向后兼容）"""
    return BotService.get_instance()
