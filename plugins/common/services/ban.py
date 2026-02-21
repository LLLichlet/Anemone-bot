"""
黑名单服务模块 - 用户封禁管理

服务层 - 实现 BanServiceProtocol 协议
"""

import json
from pathlib import Path
from typing import List, Set
import logging

from ..base import ServiceBase, Result
from ..config import config
from ..protocols import (
    BanServiceProtocol,
    ServiceLocator,
)


class BanService(ServiceBase, BanServiceProtocol):
    """
    黑名单服务类
    
    实现 BanServiceProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    def __init__(self) -> None:
        """初始化服务，数据延迟加载"""
        super().__init__()
        self._banned_users: Set[int] = set()
        self.logger = logging.getLogger("plugins.common.services.ban")
    
    def initialize(self) -> None:
        """
        初始化黑名单数据
        
        注意：初始化完成后才注册到 ServiceLocator，确保服务可用时已完成初始化。
        """
        if self._initialized:
            return
        
        self._banned_users = set(self._load_banned_list())
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(BanServiceProtocol, self)
        self.logger.info(f"Initialized with {len(self._banned_users)} banned users")
    
    def _get_banned_file_path(self) -> Path:
        """获取黑名单文件路径"""
        data_dir = Path(config.data_dir)
        
        json_path = data_dir / "banned.json"
        pkl_path = data_dir / "banned.pkl"
        
        if json_path.exists():
            return json_path
        
        if pkl_path.exists():
            return pkl_path
        
        return json_path
    
    def _load_banned_list(self) -> List[int]:
        """加载黑名单数据"""
        banned_file = self._get_banned_file_path()
        
        if not banned_file.exists():
            return []
        
        if banned_file.suffix == '.pkl':
            return self._migrate_from_pickle(banned_file)
        
        try:
            with open(banned_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [int(uid) for uid in data] if isinstance(data, list) else []
        except Exception as e:
            self.logger.error(f"Failed to load json: {e}")
            return []
    
    def _migrate_from_pickle(self, pkl_path: Path) -> List[int]:
        """从旧版 pickle 迁移数据"""
        try:
            import pickle
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    self._save_banned_list(data)
                    pkl_path.unlink()
                    self.logger.info(f"Migrated {len(data)} users from pickle to json")
                    return data
        except Exception as e:
            self.logger.error(f"Failed to migrate pickle: {e}")
        return []
    
    def _save_banned_list(self, users: List[int]) -> Result[None]:
        """保存黑名单到文件"""
        banned_file = Path(config.data_dir) / "banned.json"
        try:
            with open(banned_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return Result.success(None)
        except Exception as e:
            self.logger.error(f"Failed to save: {e}")
            return Result.fail(f"保存失败: {e}")
    
    # ========== BanServiceProtocol 实现 ==========
    
    def is_banned(self, user_id: int) -> bool:
        """检查用户是否被拉黑"""
        self.ensure_initialized()
        return user_id in self._banned_users
    
    def ban(self, user_id: int) -> Result[bool]:
        """拉黑用户"""
        self.ensure_initialized()
        
        if user_id in self._banned_users:
            return Result.success(False)
        
        self._banned_users.add(user_id)
        save_result = self._save_banned_list(list(self._banned_users))
        
        if save_result.is_success:
            self.logger.info(f"User {user_id} banned")
            return Result.success(True)
        return Result.fail(save_result.error or "保存失败")
    
    def unban(self, user_id: int) -> Result[bool]:
        """解封用户"""
        self.ensure_initialized()
        
        if user_id not in self._banned_users:
            return Result.success(False)
        
        self._banned_users.discard(user_id)
        save_result = self._save_banned_list(list(self._banned_users))
        
        if save_result.is_success:
            self.logger.info(f"User {user_id} unbanned")
            return Result.success(True)
        return Result.fail(save_result.error or "保存失败")
    
    # ========== 额外方法（不在协议中）==========
    
    def get_banned_count(self) -> int:
        """获取黑名单用户数量"""
        self.ensure_initialized()
        return len(self._banned_users)
    
    def get_banned_list(self) -> List[int]:
        """获取黑名单列表"""
        self.ensure_initialized()
        return list(self._banned_users)


def get_ban_service() -> BanService:
    """获取黑名单服务单例（向后兼容）"""
    return BanService.get_instance()
