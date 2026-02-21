"""
工具模块 - 纯函数工具集合

提供与业务逻辑无关的通用工具函数。

Note: 这不是一个 NoneBot 插件，只是工具集合。
"""

# 阻止 NoneBot 将其识别为插件
__plugin_meta__ = None

from .message import build_at_message, build_reply_message, ensure_message
from .network import (
    fetch_html, 
    fetch_binary, 
    fetch_html_async,
    fetch_binary_async,
    download_file,
    DEFAULT_HEADERS,
    HttpClient,
)
from .image import (
    download_image,
    download_image_sync,
    download_image_async,
    image_to_message,
    merge_images,
    resize_image,
    crop_image,
    create_placeholder_image,
    compress_image,
    ImageProcessor,
)
from .prompt import read_prompt, read_prompt_with_fallback

__all__ = [
    # 消息构建
    "build_at_message",
    "build_reply_message",
    "ensure_message",
    
    # 网络请求 - 同步
    "fetch_html",
    "fetch_binary",
    # 网络请求 - 异步（推荐）
    "fetch_html_async",
    "fetch_binary_async",
    "download_file",
    "DEFAULT_HEADERS",
    "HttpClient",
    
    # 图片处理
    "download_image",  # 异步下载（别名）
    "download_image_sync",
    "download_image_async",
    "image_to_message",
    "merge_images",
    "resize_image",
    "crop_image",
    "create_placeholder_image",
    "compress_image",
    "ImageProcessor",
    
    # 提示词读取
    "read_prompt",
    "read_prompt_with_fallback",
]
