"""
配置模块 - 统一配置管理

基于 Pydantic Settings 的配置管理，支持 .env 文件和环境变量。

配置加载优先级（从高到低）:
    1. 环境变量
    2. .env 文件
    3. 默认值

使用示例:
    >>> from plugins.common import config
    >>> 
    >>> # 读取配置
    >>> api_key = config.deepseek_api_key
    >>> is_enabled = config.math_enabled
    >>> 
    >>> # 修改配置（运行时生效，不保存到文件）
    >>> config.math_enabled = not config.math_enabled

环境变量:
    所有配置项都可通过环境变量设置，前缀为 QUERY_:
    - QUERY_DEEPSEEK_API_KEY
    - QUERY_MATH_ENABLED
    - QUERY_RANDOM_REPLY_PROBABILITY
    - ...

扩展指南:
    如需添加新配置项:
    1. 在 PluginConfig 类中添加字段
    2. 使用 Field(default=xxx) 设置默认值和验证
    3. 添加文档注释说明用途
    4. 如需运行时开关，在功能插件中检查该配置
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# 计算项目根目录
_CURRENT_DIR = Path(__file__).parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
_ENV_FILE_PATH = _PROJECT_ROOT / ".env"


class PluginConfig(BaseSettings):
    """
    插件配置类
    
    所有配置项的集中定义，支持从 .env 文件和环境变量加载。
    
    配置项分类:
        - AI API: 密钥、模型、基础 URL
        - 功能开关: 各功能的启用/禁用
        - 随机回复: 概率、冷却、长度限制
        - AI 参数: 各功能的温度、token 限制等
        - 系统设置: 数据目录、管理员密码等
    
    使用方式:
        >>> from plugins.common import config
        >>> print(config.deepseek_api_key)
        >>> print(config.math_enabled)
    """
    
    # ==================== AI API 配置 ====================
    deepseek_api_key: str = Field(
        default="",
        description="DeepSeek API 密钥"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API 基础 URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="使用的模型名称"
    )
    
    # ==================== 功能开关 ====================
    math_enabled: bool = Field(
        default=True,
        description="数学定义查询功能开关"
    )
    random_enabled: bool = Field(
        default=True,
        description="随机回复功能开关"
    )
    highnoon_enabled: bool = Field(
        default=True,
        description="午时已到游戏功能开关"
    )
    pjskpartiton_enabled: bool = Field(
        default=True,
        description="PJSK 随机谱面功能开关"
    )
    math_soup_enabled: bool = Field(
        default=True,
        description="数学海龟汤游戏功能开关"
    )
    
    # ==================== 调试配置 ====================
    debug_mode: bool = Field(
        default=False,
        description="全局调试模式开关"
    )
    debug_highnoon: bool = Field(
        default=False,
        description="午时已到插件调试模式"
    )
    debug_math_soup: bool = Field(
        default=False,
        description="数学谜题插件调试模式"
    )
    debug_concurrent: bool = Field(
        default=False,
        description="并发调试模式：在消息中附加buffer队列数量"
    )
    
    # ==================== 随机回复配置 ====================
    random_reply_probability: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="普通消息随机回复概率 (0-1)"
    )
    random_reply_probability_at: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="被@时随机回复概率 (0-1)"
    )
    random_reply_cooldown: int = Field(
        default=30,
        gt=0,
        description="随机回复冷却时间（秒）"
    )
    random_reply_min_length: int = Field(
        default=3,
        ge=0,
        description="触发随机回复的最小消息长度"
    )
    
    # ==================== 路径配置 ====================
    data_dir: str = Field(
        default="data",
        description="数据存储目录"
    )
    
    # ==================== 管理员配置 ====================
    admin_user_ids: str = Field(
        default="",
        description="管理员QQ号列表，逗号分隔"
    )
    
    @property
    def admin_user_ids_set(self) -> set[int]:
        """获取管理员QQ号集合"""
        if not self.admin_user_ids:
            return set()
        try:
            return {int(x.strip()) for x in self.admin_user_ids.split(",") if x.strip()}
        except (ValueError, TypeError):
            return set()
    
    # 保留旧配置兼容
    admin_password: str = Field(
        default="admin123",
        description="管理员命令密码（已弃用，使用令牌）"
    )
    
    # ==================== AI 参数 - 数学定义 ====================
    math_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="数学定义 AI 温度参数"
    )
    math_max_tokens: int = Field(
        default=512,
        gt=0,
        description="数学定义 AI 最大 token 数"
    )
    math_top_p: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="数学定义 AI top-p 参数"
    )
    
    # ==================== AI 参数 - 随机回复 ====================
    random_temperature: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="随机回复 AI 温度参数"
    )
    random_max_tokens_min: int = Field(
        default=30,
        gt=0,
        description="随机回复 AI 最小 token 数"
    )
    random_max_tokens_max: int = Field(
        default=100,
        gt=0,
        description="随机回复 AI 最大 token 数"
    )
    random_top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="随机回复 AI top-p 参数"
    )
    
    # ==================== 系统设置 ====================
    max_history_per_group: int = Field(
        default=50,
        gt=0,
        description="每群最大聊天记录保存数量"
    )
    max_ban_per_group: int = Field(
        default=10,
        gt=0,
        description="午时已到游戏每群最大参与人数"
    )
    
    # ==================== AI 参数 - 数学海龟汤 ====================
    math_soup_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="数学海龟汤 AI 判定温度参数"
    )
    
    # Pydantic 配置
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE_PATH),
        env_prefix="QUERY_",
        case_sensitive=False,
        extra="ignore",
        env_file_encoding="utf-8"
    )
    
    def __init__(self, **kwargs):
        """
        初始化配置
        
        确保数据目录存在。
        """
        super().__init__(**kwargs)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_banned_file_path(self) -> str:
        """获取黑名单文件完整路径"""
        return os.path.join(self.data_dir, "banned.json")
    
    def is_enabled(self, feature: str) -> bool:
        """
        检查功能是否开启
        
        Args:
            feature: 功能名称，如 "math", "highnoon"
            
        Returns:
            功能是否开启（默认 True）
        """
        if not feature:
            return True
        return getattr(self, f"{feature}_enabled", True)


# 全局配置实例
# 导入时自动加载 .env 文件
config = PluginConfig()
