"""
游戏服务基类 - 统一的群聊游戏状态管理

提供标准化的群聊游戏状态管理，支持多群同时游戏，
每群独立状态，自动处理游戏生命周期。

使用示例:
    >>> from plugins.common.services.game import GameServiceBase, GameState
    >>> import asyncio
    
    >>> @dataclass
    ... class MyGameState(GameState):
    ...     score: int = 0
    ...     level: int = 1
    >>> 
    >>> class MyGameService(GameServiceBase[MyGameState]):
    ...     async def create_game(self, group_id: int, **kwargs) -> MyGameState:
    ...         return MyGameState(group_id=group_id, score=0, level=1)
    >>> 
    >>> service = MyGameService.get_instance()
    >>> result = await service.start_game(123456)
    >>> game = service.get_game(123456)
    >>> await service.end_game(123456)

设计特点:
    1. 泛型支持：支持自定义 GameState 类型
    2. 单例模式：每种服务类型全局唯一
    3. 类型安全：完整的类型注解
    4. 并发安全：使用 asyncio.Lock 保护状态
    5. 自动清理：结束游戏时自动清理状态
"""

import asyncio
from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from dataclasses import dataclass, field

from ..base import Result, ServiceBase


@dataclass
class GameState:
    """
    游戏状态基类
    
    所有游戏状态的父类，包含通用字段。
    
    Attributes:
        group_id: 群号
        is_active: 游戏是否进行中
        metadata: 额外元数据（可选）
    """
    group_id: int
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T', bound=GameState)


class GameServiceBase(ServiceBase, Generic[T]):
    """
    游戏服务基类
    
    提供标准化的群聊游戏管理功能，支持多群并发游戏。
    使用 asyncio.Lock 确保并发安全。
    
    子类必须实现:
        - create_game(): 创建初始游戏状态
    
    注意：子类应该使用 async/await 来调用需要锁保护的方法。
    """
    
    _instances: Dict[type, 'GameServiceBase'] = {}
    
    def __new__(cls: type) -> 'GameServiceBase':
        """确保每种子类只有一个实例"""
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]
    
    @classmethod
    def get_instance(cls: type) -> 'GameServiceBase':
        """获取服务单例"""
        return cls()
    
    def __init__(self) -> None:
        """初始化服务（只执行一次）"""
        if self._initialized:
            return
        super().__init__()
        self._games: Dict[int, T] = {}
        self._lock = asyncio.Lock()  # 并发锁
        self._initialized = True
    
    @abstractmethod
    def create_game(self, group_id: int, **kwargs) -> T:
        """
        创建游戏状态（子类必须实现）
        
        Args:
            group_id: 群号
            **kwargs: 额外参数
            
        Returns:
            初始化的游戏状态对象
        """
        pass
    
    def has_active_game(self, group_id: int) -> bool:
        """
        检查指定群是否有进行中的游戏
        
        注意：此方法不加锁，仅用于快速查询。
        如需精确判断，请使用 get_game()。
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果有进行中的游戏
        """
        game = self._games.get(group_id)
        return game is not None and game.is_active
    
    def get_game(self, group_id: int) -> Optional[T]:
        """
        获取指定群的游戏状态
        
        注意：此方法不加锁，返回当前状态的快照。
        如需修改状态，请使用 start_game() / end_game()。
        
        Args:
            group_id: 群号
            
        Returns:
            游戏状态对象，如果不存在返回 None
        """
        return self._games.get(group_id)
    
    async def start_game(self, group_id: int, **kwargs) -> Result[T]:
        """
        开始新游戏（线程安全）
        
        如果该群已有进行中的游戏，会结束旧游戏并开始新游戏。
        
        Args:
            group_id: 群号
            **kwargs: 传递给 create_game() 的参数
            
        Returns:
            Result[T]: 成功返回游戏状态，失败返回错误
        """
        async with self._lock:
            try:
                # 如果已有游戏，先结束它
                if group_id in self._games:
                    await self._end_game_locked(group_id)
                
                # 创建新游戏状态
                game = self.create_game(group_id, **kwargs)
                self._games[group_id] = game
                
                return Result.success(game)
            except Exception as e:
                return Result.fail(f"开始游戏失败: {e}")
    
    async def end_game(self, group_id: int) -> bool:
        """
        结束游戏（线程安全）
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果成功结束游戏，False 如果没有进行中的游戏
        """
        async with self._lock:
            return await self._end_game_locked(group_id)
    
    async def _end_game_locked(self, group_id: int) -> bool:
        """
        结束游戏（内部方法，需在持有锁时调用）
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果成功结束游戏
        """
        game = self._games.get(group_id)
        if game is None:
            return False
        
        game.is_active = False
        del self._games[group_id]
        return True
    
    def get_active_games_count(self) -> int:
        """
        获取当前活跃游戏数量
        
        Returns:
            活跃游戏数量
        """
        return len(self._games)
    
    def list_active_games(self) -> Dict[int, T]:
        """
        获取所有活跃游戏的快照
        
        Returns:
            群号到游戏状态的映射字典（副本）
        """
        return self._games.copy()
    

