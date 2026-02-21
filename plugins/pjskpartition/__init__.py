"""
随机谱面插件

使用新架构（PluginHandler + CommandReceiver）重构
"""
import random
import asyncio

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import PluginHandler, CommandReceiver

try:
    from plugins.utils import download_image_async, image_to_message, merge_images
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class PJSKHandler(PluginHandler):
    """PJSK 随机谱面处理器"""
    
    name = "pjsk随机谱面"
    description = "pjsk随机谱面猜歌"
    command = "pjsk随机谱面"
    feature_name = "pjskpartiton"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理随机谱面命令"""
        if not UTILS_AVAILABLE:
            await self.reply("图片处理模块未加载")
            return
            
        # 生成随机数据
        song_id = str(random.randint(1, 639)).zfill(3)
        difficulty = random.choice(["exp", "mst"])
        
        # 构建 URL
        bg_url = f"https://sdvx.in/prsk/bg/{song_id}bg.png"
        bar_url = f"https://sdvx.in/prsk/bg/{song_id}bar.png"
        data_url = f"https://sdvx.in/prsk/obj/data{song_id}{difficulty}.png"
        
        # 异步下载图片
        bg, bar, data = await self._download_images(bg_url, bar_url, data_url)
        
        if bg is None:
            await self.reply("谱面背景下载失败，请稍后再试")
            return
        if bar is None:
            await self.reply("谱面小节下载失败，请稍后再试")
            return
        if data is None:
            await self.reply("谱面内容下载失败，请稍后再试")
            return
        
        # 合并图片
        result = merge_images(bg, data, bar)
        if result is None:
            await self.reply("图片合并失败，请稍后再试")
            return
        
        # 发送图片
        msg = image_to_message(result)
        await self.finish(msg)
    
    async def _download_images(self, bg_url: str, bar_url: str, data_url: str):
        """并发下载三张图片"""
        tasks = [
            download_image_async(bg_url),
            download_image_async(bar_url),
            download_image_async(data_url),
        ]
        return await asyncio.gather(*tasks)


# 创建处理器和接收器
handler = PJSKHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command}",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
