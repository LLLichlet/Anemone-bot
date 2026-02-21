"""
配置提供者服务 - 实现配置访问接口

此模块实现 ConfigProviderProtocol，为其他层提供配置查询功能。
"""

from typing import Any, Optional

from ..base import ServiceBase
from ..config import config
from ..protocols import ServiceLocator, ConfigProviderProtocol


class ConfigProvider(ServiceBase, ConfigProviderProtocol):
    """
    配置提供者服务
    
    实现 ConfigProviderProtocol，提供配置查询功能。
    管理功能开关等配置项的查询。
    
    单例模式：通过 ConfigProvider.get_instance() 获取实例
    """
    
    def __init__(self) -> None:
        """初始化配置提供者"""
        super().__init__()
    
    def initialize(self) -> None:
        """初始化配置提供者（延迟初始化）"""
        if self._initialized:
            return
        
        self._initialized = True
        # 注册到 ServiceLocator
        ServiceLocator.register(ConfigProviderProtocol, self)
    
    # ========== ConfigProviderProtocol 实现 ==========
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项名称
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        return getattr(config, key, default)
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        检查功能是否开启
        
        Args:
            feature_name: 功能名称
            
        Returns:
            如果功能开启或没有对应配置，返回 True
        """
        if not feature_name:
            return True
        
        try:
            return getattr(config, f"{feature_name}_enabled", True)
        except AttributeError:
            return True
    
    # ========== 配置访问方法 ==========
    
    @property
    def debug_mode(self) -> bool:
        """是否开启调试模式"""
        return getattr(config, 'debug_mode', False)
    
    @property
    def admin_user_ids(self) -> list[int]:
        """获取管理员用户ID列表"""
        try:
            if config.admin_user_ids:
                return [int(x.strip()) for x in config.admin_user_ids.split(',')]
            return []
        except (ValueError, AttributeError):
            return []
