"""
PJSK 谱面插件

支持：
- /chart - 随机谱面
- /chart <编号> - 指定编号谱面（如 /chart 001）
- /chart <歌曲名> - 搜索歌曲谱面（如 /chart Tell Your World）

使用新架构（PluginHandler + CommandReceiver）重构
"""
import random
import asyncio
import json
import os
import re

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
    from plugins.utils import download_image, image_to_message, merge_images, calculate_similarity
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class PJSKHandler(PluginHandler):
    """PJSK 谱面处理器"""
    
    name = "PJSK谱面"
    description = "pjsk谱面相关功能，支持随机、指定编号、搜索歌曲名"
    command = "chart"
    aliases = {"pjsk随机谱面", "pjsk谱面"}
    feature_name = "pjskpartiton"
    priority = 10
    
    def __init__(self):
        super().__init__()
        self.songs_data = self._load_songs_data()
    
    def _load_songs_data(self) -> dict:
        """加载歌曲数据"""
        json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "pjsk_songs.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            songs = data.get("songs", [])
            id_to_name = {s["id_str"]: s["name"] for s in songs}
            return {
                "songs": songs,
                "id_to_name": id_to_name,
            }
        except Exception:
            return {"songs": [], "id_to_name": {}}
    
    def _find_song_by_name(self, query: str) -> tuple[str, str] | None:
        """根据歌曲名搜索，返回相似度最高的 (id_str, name)"""
        query = query.lower()
        best_match = None
        best_score = 0.0
        
        for song in self.songs_data.get("songs", []):
            song_name = song["name"]
            # 精确包含优先
            if query == song_name.lower():
                return song["id_str"], song_name
            # 相似度匹配
            if UTILS_AVAILABLE:
                score = calculate_similarity(query, song_name.lower())
                if score > best_score:
                    best_score = score
                    best_match = (song["id_str"], song_name)
        
        # 相似度阈值 0.4
        if best_match and best_score > 0.4:
            return best_match
        return None
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理谱面命令"""
        if not UTILS_AVAILABLE:
            await self.reply("图片处理模块未加载")
            return
        
        song_id = None
        song_name = None
        difficulty = None
        
        # 解析参数
        if args:
            args = args.strip()
            
            # 检查是否包含难度参数 (exp/mst/apd)
            diff_match = re.search(r'\s+(exp|mst|apd)$', args, re.IGNORECASE)
            if diff_match:
                difficulty = diff_match.group(1).lower()
                args = args[:diff_match.start()].strip()
            
            # 判断是编号还是歌曲名
            if args.isdigit():
                # 数字编号
                num = int(args)
                if 1 <= num <= 639:
                    song_id = f"{num:03d}"
                    song_name = self.songs_data.get("id_to_name", {}).get(song_id)
                else:
                    await self.reply("查不到这个谱面哦")
                    return
            else:
                # 歌曲名搜索
                result = self._find_song_by_name(args)
                if result:
                    song_id, song_name = result
                else:
                    await self.reply("查不到这个谱面哦")
                    return
        else:
            # 随机模式
            song_id = f"{random.randint(1, 639):03d}"
            song_name = self.songs_data.get("id_to_name", {}).get(song_id, "未知歌曲")
        
        # 默认难度（随机时不选apd，因为不是所有歌曲都有）
        if not difficulty:
            difficulty = random.choice(["exp", "mst"])
        
        # 先发送歌曲名
        if args:
            await self.reply(f"{song_name}")
        
        # 构建 URL 并下载图片
        bg_url = f"https://sdvx.in/prsk/bg/{song_id}bg.png"
        bar_url = f"https://sdvx.in/prsk/bg/{song_id}bar.png"
        data_url = f"https://sdvx.in/prsk/obj/data{song_id}{difficulty}.png"
        
        bg, bar, data = await self._download_images(bg_url, bar_url, data_url)
        
        # 检查是否下载成功
        if bg is None or bar is None or data is None:
            await self.reply("查不到这个谱面哦")
            return
        
        # 合并图片
        result = merge_images(bg, data, bar)
        if result is None:
            await self.reply("查不到这个谱面哦")
            return
        
        # 发送图片
        msg = image_to_message(result)
        await self.send(msg, finish=True)
    
    async def _download_images(self, bg_url: str, bar_url: str, data_url: str):
        """并发下载三张图片"""
        tasks = [
            download_image(bg_url),
            download_image(bar_url),
            download_image(data_url),
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
        usage="/chart [编号/歌曲名] [难度(exp/mst/apd)]",
        extra={"author": "Lichlet", "version": "2.3.1"}
    )
