"""
消息发送缓冲 - 用于防风控

使用方式：
    from plugins.common.buffer import get_buffer
    
    # 排队发送（间隔 800ms，防风控）
    await get_buffer().send(group_id, message, send_func)
    
    # 立即发送（可能触发风控）
    await matcher.send(message)
"""

import asyncio
import time
from typing import Optional, Any, Callable, Dict


class SendBuffer:
    """发送缓冲器 - 控制发送频率，在调用者上下文中执行发送"""
    
    def __init__(self, interval_ms: float = 800.0):
        self._interval = interval_ms / 1000.0
        self._last_time: Dict[int, float] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
    
    def _get_lock(self, group_id: int) -> asyncio.Lock:
        """获取群的锁（每群独立，不同群并发）"""
        if group_id not in self._locks:
            self._locks[group_id] = asyncio.Lock()
        return self._locks[group_id]
    
    async def send(self, group_id: int, message: Any, send_func: Callable):
        """
        发送消息（带频率控制）
        
        在调用者上下文中执行，避免 ContextVar 丢失问题。
        同群消息按顺序执行，间隔至少 800ms。
        
        Args:
            group_id: 群号
            message: 消息内容
            send_func: 发送函数（如 matcher.send）
        """
        lock = self._get_lock(group_id)
        
        async with lock:
            # 等待间隔
            now = time.time()
            last = self._last_time.get(group_id, 0)
            wait = self._interval - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            
            # 发送（在调用者上下文中）
            try:
                await send_func(message)
            except Exception as e:
                print(f"[SendBuffer] 发送失败: {e}")
            
            self._last_time[group_id] = time.time()
    
    def qsize(self) -> int:
        """获取当前等待中的消息数量（估算值）"""
        return sum(1 for lock in self._locks.values() if lock.locked())


_buffer: Optional[SendBuffer] = None


def get_buffer() -> SendBuffer:
    """获取全局发送缓冲区"""
    global _buffer
    if _buffer is None:
        _buffer = SendBuffer(interval_ms=800.0)
    return _buffer


def init_buffer():
    """初始化（在 bot.py 启动时调用）- 新版本无需启动 task"""
    pass
