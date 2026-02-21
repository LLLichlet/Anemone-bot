"""
一次性令牌服务

服务层 - 实现 TokenServiceProtocol 协议

提供基于时间的短期令牌生成和验证，用于管理员身份验证。
"""

import secrets
import time
from typing import Dict, Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..protocols import (
    TokenServiceProtocol,
    ServiceLocator,
)


@dataclass
class TokenInfo:
    """令牌信息"""
    token: str
    expire_time: float
    used: bool = False


class TokenService(ServiceBase, TokenServiceProtocol):
    """
    一次性令牌服务
    
    实现 TokenServiceProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    # 令牌有效期（秒）
    TOKEN_EXPIRE_SECONDS = 300  # 5分钟
    
    # 令牌长度（字节）
    TOKEN_BYTES = 8  # 约11位base64字符
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        self._tokens: Dict[int, TokenInfo] = {}
        self.logger = logging.getLogger("plugins.common.services.token")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注意：初始化完成后才注册到 ServiceLocator。
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(TokenServiceProtocol, self)
        self.logger.info("Token Service initialized")
    
    # ========== TokenServiceProtocol 实现 ==========
    
    def generate_token(self, user_id: int) -> str:
        """生成一次性令牌"""
        # 清除该用户的旧令牌
        if user_id in self._tokens:
            del self._tokens[user_id]
        
        # 生成新令牌
        token = secrets.token_urlsafe(self.TOKEN_BYTES)
        expire_time = time.time() + self.TOKEN_EXPIRE_SECONDS
        
        self._tokens[user_id] = TokenInfo(
            token=token,
            expire_time=expire_time,
            used=False
        )
        
        self.logger.info(f"为用户 {user_id} 生成令牌")
        return token
    
    def verify_token(self, user_id: int, token: str) -> bool:
        """验证并消耗令牌"""
        if user_id not in self._tokens:
            return False
        
        token_info = self._tokens[user_id]
        
        # 检查是否已使用
        if token_info.used:
            del self._tokens[user_id]
            return False
        
        # 检查是否过期
        current_time = time.time()
        if current_time > token_info.expire_time:
            del self._tokens[user_id]
            return False
        
        # 验证令牌内容（防止时序攻击）
        if not secrets.compare_digest(token_info.token, token):
            return False
        
        # 标记为已使用（一次性）
        del self._tokens[user_id]
        
        self.logger.info(f"用户 {user_id} 的令牌验证通过")
        return True
    
    # ========== 额外方法（不在协议中）==========
    
    def has_valid_token(self, user_id: int) -> bool:
        """检查用户是否有有效未使用的令牌"""
        if user_id not in self._tokens:
            return False
        
        token_info = self._tokens[user_id]
        
        if token_info.used:
            return False
        
        if time.time() > token_info.expire_time:
            return False
        
        return True
    
    def get_token_remaining_time(self, user_id: int) -> Optional[int]:
        """获取令牌剩余有效时间（秒）"""
        if user_id not in self._tokens:
            return None
        
        token_info = self._tokens[user_id]
        
        if token_info.used:
            return None
        
        remaining = int(token_info.expire_time - time.time())
        if remaining <= 0:
            return None
        
        return remaining
    
    def revoke_token(self, user_id: int) -> bool:
        """吊销用户的令牌"""
        if user_id in self._tokens:
            del self._tokens[user_id]
            self.logger.info(f"已吊销用户 {user_id} 的令牌")
            return True
        return False


def get_token_service() -> TokenService:
    """获取令牌服务实例（向后兼容）"""
    return TokenService.get_instance()
