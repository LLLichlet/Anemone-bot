"""
common 模块 - 基础设施层

提供整个项目的基础功能和公共服务。

目录结构:
    base.py           - 基础层: ServiceBase, Result[T]
    config.py         - 配置层: PluginConfig
    compat.py         - 兼容性: NoneBot 导入保护
    protocols.py      - 协议层: 接口定义, ServiceLocator
    handler.py        - 处理器层: PluginHandler, MessageHandler
    receiver.py       - 接收层: CommandReceiver, MessageReceiver
    services/         - 服务实现层
        ├── ai.py           - AI服务
        ├── ban.py          - 黑名单服务
        ├── bot.py          - Bot API服务
        ├── chat.py         - 聊天服务
        ├── game.py         - 游戏服务基类
        ├── registry.py     - 插件注册表
        ├── system.py       - 系统监控
        └── token.py        - 一次性令牌

使用方式:
    # 从 common 导入常用功能
    from plugins.common import PluginHandler, CommandReceiver
    from plugins.common import Result, ServiceBase
    from plugins.common.protocols import ServiceLocator, AIServiceProtocol
"""

# 阻止 NoneBot 将其识别为插件
__plugin_meta__ = None

# ========== 基础层 ==========
from .base import (
    ServiceBase,
    Result,
)

# ========== 配置层 ==========
from .config import config, PluginConfig

# ========== 兼容性 ==========
from .compat import NONEBOT_AVAILABLE

# ========== 协议层 ==========
from .protocols import (
    ServiceLocator,
    # 协议接口
    AIServiceProtocol,
    BanServiceProtocol,
    ChatServiceProtocol,
    BotServiceProtocol,
    TokenServiceProtocol,
    SystemMonitorProtocol,
)

# ========== 处理器层 ==========
from .handler import (
    PluginHandler,
    MessageHandler,
)

# ========== 接收层 ==========
from .receiver import (
    CommandReceiver,
    MessageReceiver,
)

# ========== 工具层（常用）==========
from ..utils import read_prompt

# ========== 服务层（常用）==========
from .services import (
    AIService,
    BanService,
    ChatService,
    BotService,
    TokenService,
    SystemMonitorService,
    GameServiceBase,
    GameState,
    PluginRegistry,
    PluginInfo,
)

__all__ = [
    # 兼容性
    'NONEBOT_AVAILABLE',
    
    # 工具层
    'read_prompt',
    
    # 基础层
    'ServiceBase',
    'Result',
    
    # 配置层
    'config',
    'PluginConfig',
    
    # 协议层
    'ServiceLocator',
    'AIServiceProtocol',
    'BanServiceProtocol',
    'ChatServiceProtocol',
    'BotServiceProtocol',
    'TokenServiceProtocol',
    'SystemMonitorProtocol',
    
    # 处理器层
    'PluginHandler',
    'MessageHandler',
    
    # 接收层
    'CommandReceiver',
    'MessageReceiver',
    
    # 服务层
    'AIService',
    'BanService',
    'ChatService',
    'BotService',
    'TokenService',
    'SystemMonitorService',
    'GameServiceBase',
    'GameState',
    'PluginRegistry',
    'PluginInfo',
]
