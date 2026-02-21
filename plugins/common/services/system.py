"""
系统监控服务

服务层 - 实现 SystemMonitorProtocol 协议

提供 bot 进程资源使用情况查询，包括 CPU、内存、运行时间等。
"""

import os
import time
import platform
from typing import Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..protocols import (
    SystemMonitorProtocol,
    ServiceLocator,
)


@dataclass
class ProcessStatus:
    """进程状态信息"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    threads: int
    uptime_seconds: float
    platform: str
    python_version: str


class SystemMonitorService(ServiceBase, SystemMonitorProtocol):
    """
    系统监控服务
    
    实现 SystemMonitorProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        self._start_time = time.time()
        self._psutil_available = False
        self._process = None
        self.logger = logging.getLogger("plugins.common.services.system")
        
        # 尝试导入 psutil
        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
            self._process = psutil.Process()
        except ImportError:
            self.logger.warning("psutil not installed, system monitoring limited")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注意：初始化完成后才注册到 ServiceLocator。
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(SystemMonitorProtocol, self)
        self.logger.info("System Monitor Service initialized")
    
    def is_available(self) -> bool:
        """检查是否可用（psutil 是否安装）"""
        return self._psutil_available
    
    def get_status(self) -> ProcessStatus:
        """获取进程状态"""
        if self._psutil_available and self._process:
            return self._get_status_with_psutil()
        else:
            return self._get_status_basic()
    
    def _get_status_with_psutil(self) -> ProcessStatus:
        """使用 psutil 获取进程状态"""
        cpu_percent = self._process.cpu_percent(interval=0.1)
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        memory_percent = self._process.memory_percent()
        threads = self._process.num_threads()
        uptime_seconds = time.time() - self._start_time
        
        return ProcessStatus(
            cpu_percent=round(cpu_percent, 1),
            memory_mb=round(memory_mb, 1),
            memory_percent=round(memory_percent, 1),
            threads=threads,
            uptime_seconds=uptime_seconds,
            platform=platform.platform(),
            python_version=platform.python_version()
        )
    
    def _get_status_basic(self) -> ProcessStatus:
        """基础状态（无 psutil 时）"""
        uptime_seconds = time.time() - self._start_time
        
        return ProcessStatus(
            cpu_percent=-1,
            memory_mb=0,
            memory_percent=-1,
            threads=0,
            uptime_seconds=uptime_seconds,
            platform=platform.platform(),
            python_version=platform.python_version()
        )
    
    def format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}分钟")
        
        return "".join(parts)
    
    # ========== SystemMonitorProtocol 实现 ==========
    
    def get_status_text(self) -> str:
        """获取格式化的状态文本"""
        status = self.get_status()
        
        lines = []
        lines.append(f"进程: query_bot")
        
        if status.cpu_percent >= 0:
            lines.append(f"CPU: {status.cpu_percent}%")
        else:
            lines.append("CPU: N/A (psutil not installed)")
        
        if status.memory_percent >= 0:
            lines.append(f"Memory: {status.memory_mb}MB ({status.memory_percent}%)")
        else:
            lines.append("Memory: N/A")
        
        if status.threads > 0:
            lines.append(f"Threads: {status.threads}")
        
        uptime_str = self.format_uptime(status.uptime_seconds)
        lines.append(f"Runtime: {uptime_str}")
        
        return "\n".join(lines)


def get_system_monitor_service() -> SystemMonitorService:
    """获取系统监控服务实例（向后兼容）"""
    return SystemMonitorService.get_instance()
