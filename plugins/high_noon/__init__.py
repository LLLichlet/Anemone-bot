"""
午时已到（俄罗斯轮盘赌）插件

使用新架构（PluginHandler + CommandReceiver）重构
"""
import random
from dataclasses import dataclass, field

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
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    GameServiceBase,
    GameState,
    BotServiceProtocol,
    config,
)


# ========== 数据模型 ==========

@dataclass
class HighNoonState(GameState):
    """午时已到游戏状态"""
    bullet_pos: int = 0
    shot_count: int = 0
    players: list = field(default_factory=list)


# ========== 游戏服务 ==========

class HighNoonService(GameServiceBase[HighNoonState]):
    """午时已到游戏服务"""
    
    STATEMENTS = [
        "无需退路。( 1 / 6 )",
        "英雄们啊，为这最强大的信念，请站在我们这边。( 2 / 6 )",
        "颤抖吧，在真正的勇敢面前。( 3 / 6 )",
        "哭嚎吧，为你们不堪一击的信念。( 4 / 6 )",
        "现在可没有后悔的余地了。( 5 / 6 )"
    ]
    
    def create_game(self, group_id: int, **kwargs) -> HighNoonState:
        """创建新游戏状态"""
        bullet_pos = random.randint(1, 6)
        
        return HighNoonState(
            group_id=group_id,
            bullet_pos=bullet_pos,
            shot_count=0,
            players=[]
        )
    
    async def fire(self, group_id: int, user_id: int, username: str) -> Optional[dict]:
        """处理开枪"""
        # 注意：由于 has_active_game 和 get_game 是无锁的，
        # 我们在这里只读取状态，不修改状态
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return None
        
        if user_id not in game.players:
            game.players.append(user_id)
        
        game.shot_count += 1
        
        if game.shot_count == game.bullet_pos:
            # 异步结束游戏
            await self.end_game(group_id)
            return {
                "hit": True,
                "message": f"来吧,{username},鲜血会染红这神圣的场所",
                "game_over": True
            }
        else:
            return {
                "hit": False,
                "message": self.STATEMENTS[game.shot_count - 1],
                "game_over": False
            }


# ========== 处理器类 ==========

class HighNoonStartHandler(PluginHandler):
    """午时已到 - 开始游戏"""
    
    name = "决斗"
    description = "俄罗斯轮盘赌禁言游戏"
    command = "highnoon"
    aliases = {"午时已到"}
    feature_name = "highnoon"
    priority = 10
    
    async def handle(self, event: GroupMessageEvent, args: str) -> None:
        """开始午时已到游戏"""
        if not NONEBOT_AVAILABLE:
            return
        
        group_id = event.group_id
        service = HighNoonService.get_instance()
        
        result = await service.start_game(group_id)
        
        if result.is_failure:
            await self.reply("开始游戏失败")
            return
        
        game = result.value
        
        # 检查调试模式
        if config.debug_mode or config.debug_highnoon:
            await self.send(
                f"午时已到\n"
                f"（调试：子弹位置={game.bullet_pos}）"
            )
        else:
            await self.send("午时已到")


class FireHandler(PluginHandler):
    """午时已到 - 开枪"""
    
    name = "开枪"
    description = "午时已到游戏开枪命令"
    command = "fire"
    aliases = {"开枪"}
    feature_name = "highnoon"
    priority = 5
    block = False
    
    async def handle(self, event: GroupMessageEvent, args: str) -> None:
        """处理开枪命令"""
        if not NONEBOT_AVAILABLE:
            return
        
        group_id = event.group_id
        user_id = event.user_id
        username = event.sender.card or event.sender.nickname or f"用户{user_id}"
        
        service = HighNoonService.get_instance()
        
        if not service.has_active_game(group_id):
            return
        
        result = await service.fire(group_id, user_id, username)
        
        if result is None:
            return
        
        # 通过协议层获取 Bot 服务
        bot = ServiceLocator.get(BotServiceProtocol)
        if bot is None:
            return
        
        if result["hit"]:
            # 中弹！禁言
            ban_result = await bot.ban_random_duration(
                group_id=group_id,
                user_id=user_id,
                min_minutes=1,
                max_minutes=10
            )
            
            if ban_result.is_success:
                await bot.send_message(event, result["message"])
            else:
                await bot.send_message(
                    event,
                    f"{username},哀悼的钟声为你停下……"
                )
            
            await bot.send_message(event, "钟摆落地,一切归于宁静")
        else:
            # 安全
            await bot.send_message(event, result["message"])


# ========== 创建处理器和接收器 ==========
start_handler = HighNoonStartHandler()
fire_handler = FireHandler()

start_receiver = CommandReceiver(start_handler)
fire_receiver = CommandReceiver(fire_handler)


# ========== 导出元数据 ==========
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="午时已到",
        description="俄罗斯轮盘赌禁言游戏",
        usage="/highnoon (午时已到) 开始游戏，/fire (开枪) 参与",
        extra={"author": "Lichlet", "version": "2.3.1"}
    )
