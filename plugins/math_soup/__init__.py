"""
数学谜题插件 - 20 Questions 模式

AI 在心中选定一个数学概念（定理、公式、人物或对象），
玩家通过最多 20 个是非问题来推理出答案。
"""

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    ConfigProviderProtocol,
)

from .service import MathPuzzleService


class MathPuzzleStartHandler(PluginHandler):
    """数学谜题 - 开始游戏"""
    
    name = "数学谜题"
    description = "通过是非问题猜测数学概念的猜谜游戏"
    command = "数学谜"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理开始游戏命令"""
        service = MathPuzzleService.get_instance()
        
        if service.has_active_game(event.group_id):
            await self.reply(
                "当前已有进行中的数学谜题！\n"
                "请使用 /答案 结束当前游戏后再开始新游戏。"
            )
            return
        
        result = await service.start_game(event.group_id)
        
        if result.is_failure:
            await self.reply(f"开始游戏失败: {result.error}")
            return
        
        game = result.value
        msg = f"数学谜题开始"
        
        # 通过协议层检查调试模式
        config = ServiceLocator.get(ConfigProviderProtocol)
        if config is not None:
            debug_mode = config.get("debug_mode", False)
            debug_math_soup = config.get("debug_math_soup", False)
            if debug_mode or debug_math_soup:
                msg += f" [调试: {game.concept.answer}]"
        
        await self.reply(msg)


class MathPuzzleAskHandler(PluginHandler):
    """数学谜题 - 提问"""
    
    name = "数学谜题提问"
    description = "提出是非问题来推理答案"
    command = "问"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理提问命令"""
        if not args:
            await self.reply("请输入问题内容，例如：/问 这是关于几何的吗")
            return
        
        service = MathPuzzleService.get_instance()
        
        if not service.has_active_game(event.group_id):
            await self.reply("请先使用 /数学谜 开始游戏")
            return
        
        result = await service.ask_question(event.group_id, args)
        
        if result.is_failure:
            await self.reply(result.error)
            return
        
        await self.reply(f"{result.value}")


class MathPuzzleGuessHandler(PluginHandler):
    """数学谜题 - 猜测答案"""
    
    name = "数学谜题猜测"
    description = "直接猜测答案"
    command = "猜"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理猜测命令"""
        if not args:
            await self.reply("请输入猜测的答案，例如：/猜 欧拉公式")
            return
        
        service = MathPuzzleService.get_instance()
        
        if not service.has_active_game(event.group_id):
            await self.reply("请先使用 /数学谜 开始游戏")
            return
        
        result = await service.make_guess(event.group_id, args)
        
        if result.is_failure:
            await self.reply(result.error)
            return
        
        data = result.value
        if data["correct"]:
            await self.reply(
                f"正确。答案是 {data['answer']}。\n"
                f"{data['description']}"
            )
        else:
            sim = data.get("similarity", 0)
            if sim > 50:
                await self.reply(f"很接近了--相似度{sim:.0f}%")
            else:
                await self.reply("错误。")


class MathPuzzleRevealHandler(PluginHandler):
    """数学谜题 - 揭示答案"""
    
    name = "数学谜题答案"
    description = "揭示答案并结束游戏"
    command = "答案"
    aliases = {"不猜了", "揭晓"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理揭示答案命令"""
        service = MathPuzzleService.get_instance()
        
        game = service.get_game(event.group_id)
        if game is None or not game.is_active:
            await self.reply("当前没有进行中的游戏")
            return
        
        if game.concept is None:
            await self.reply("游戏状态异常")
            return
        
        concept = game.concept
        await service.end_game(event.group_id)
        
        await self.reply(
            f"答案: {concept.answer}\n"
            f"{concept.description}\n"
            f"提问: {game.question_count}次, 猜测: {game.guess_count}次"
        )


# ========== 创建处理器和接收器 ==========
start_handler = MathPuzzleStartHandler()
ask_handler = MathPuzzleAskHandler()
guess_handler = MathPuzzleGuessHandler()
reveal_handler = MathPuzzleRevealHandler()

start_receiver = CommandReceiver(start_handler)
ask_receiver = CommandReceiver(ask_handler)
guess_receiver = CommandReceiver(guess_handler)
reveal_receiver = CommandReceiver(reveal_handler)


# ========== 导出元数据 ==========
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="数学谜题",
        description="通过是非问题猜测数学概念的猜谜游戏",
        usage="/数学谜 - 开始游戏，/问 [问题] - 提问，/猜 [答案] - 猜测",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
