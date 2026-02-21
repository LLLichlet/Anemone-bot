"""
AI 服务模块 - DeepSeek API 封装

服务层 - 实现 AIServiceProtocol 协议
"""

from typing import Optional, Any
import logging

from openai import AsyncOpenAI

from ..base import ServiceBase, Result
from ..config import config
from ..protocols import (
    AIServiceProtocol,
    ServiceLocator,
)


class AIService(ServiceBase, AIServiceProtocol):
    """
    AI 服务类 - 封装 DeepSeek API 调用
    
    实现 AIServiceProtocol 协议，在 initialize() 完成后注册到 ServiceLocator。
    """
    
    def __init__(self) -> None:
        """初始化服务，客户端延迟加载"""
        super().__init__()
        self._client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger("plugins.common.services.ai")
    
    def initialize(self) -> None:
        """
        初始化 OpenAI 客户端
        
        注意：初始化完成后才注册到 ServiceLocator。
        """
        if self._initialized:
            return
        
        if config.deepseek_api_key:
            self._client = AsyncOpenAI(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url
            )
            self.logger.info("AI Service initialized")
        else:
            self.logger.warning("AI Service not initialized: API key not set")
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(AIServiceProtocol, self)
    
    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """获取 OpenAI 客户端"""
        self.ensure_initialized()
        return self._client
    
    # ========== AIServiceProtocol 实现 ==========
    
    @property
    def is_available(self) -> bool:
        """检查 AI 服务是否可用"""
        return self.client is not None
    
    async def chat(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.5,
        max_tokens: int = 512,
        top_p: float = 0.9
    ) -> Result[str]:
        """调用 AI 聊天接口"""
        if not self.is_available:
            return Result.fail("AI服务未初始化")
        
        try:
            response = await self.client.chat.completions.create(  # type: ignore
                model=config.deepseek_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
            content = response.choices[0].message.content.strip()
            return Result.success(content)
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return Result.fail(f"AI服务暂时不可用: {e}")
    
    # ========== 额外方法（不在协议中）==========
    
    async def chat_simple(
        self,
        system_prompt: str,
        user_input: str,
        **kwargs: Any
    ) -> str:
        """简化版聊天接口，直接返回字符串"""
        result = await self.chat(system_prompt, user_input, **kwargs)
        return result.unwrap_or("AI服务暂时不可用")


def get_ai_service() -> AIService:
    """获取 AI 服务单例实例（向后兼容）"""
    return AIService.get_instance()
