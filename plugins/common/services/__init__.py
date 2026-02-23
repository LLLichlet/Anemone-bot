"""
services 子模块 - 服务层实现

提供项目所需的各项服务实现。

架构说明:
    所有服务都实现相应的 Protocol 接口，并通过 ServiceLocator 注册。
    插件层通过 ServiceLocator.get(Protocol) 获取服务，不直接实例化。

服务列表:
    - AIService: DeepSeek API 调用
    - BanService: 黑名单管理
    - BotService: NoneBot 群管理 API
    - ChatService: 群聊历史记录
    - GameServiceBase: 游戏服务基类
    - PluginRegistry: 插件注册表
    - SystemMonitorService: 系统监控
    - TokenService: 一次性令牌

使用方式:
    from plugins.common import AIService
    ai = AIService.get_instance()
    
    from plugins.common.protocols import ServiceLocator, AIServiceProtocol
    ai = ServiceLocator.get(AIServiceProtocol)
"""

# 服务导出
from .ai import AIService
from .ban import BanService
from .bot import BotService
from .chat import ChatService
from .game import GameServiceBase, GameState
from .registry import PluginRegistry, PluginInfo
from .system import SystemMonitorService
from .token import TokenService

__all__ = [
    # 核心服务
    'AIService',
    'BanService',
    'BotService',
    'ChatService',
    
    # 游戏服务
    'GameServiceBase',
    'GameState',
    
    # 注册表
    'PluginRegistry',
    'PluginInfo',
    
    # 其他服务
    'SystemMonitorService',
    'TokenService',
]
