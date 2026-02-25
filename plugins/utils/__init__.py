"""
工具模块 - 纯函数工具集合

提供与业务逻辑无关的通用工具函数。

Note: 这不是一个 NoneBot 插件，只是工具集合。
"""

# 阻止 NoneBot 将其识别为插件
__plugin_meta__ = None

from .message import build_at_message
from .network import (
    fetch_html,
    fetch_binary,
    download_file,
    DEFAULT_HEADERS,
    HttpClient,
)
try:
    from .image import (
        download_image,
        image_to_message,
        merge_images,
        resize_image,
        crop_image,
        create_placeholder_image,
        compress_image,
        ImageProcessor,
    )
    PIL_AVAILABLE = True
except ImportError:
    # PIL 不可用（例如测试环境）
    PIL_AVAILABLE = False
    download_image = None
    image_to_message = None
    merge_images = None
    resize_image = None
    crop_image = None
    create_placeholder_image = None
    compress_image = None
    ImageProcessor = None
from .prompt import read_prompt, read_prompt_with_fallback
from .text import (
    normalize_text,
    normalize_texts,
    calculate_similarity,
    find_best_match,
    is_text_match,
    SimilarityConstants,
)

__all__ = [
    # 消息构建
    "build_at_message",
    
    # 网络请求
    "fetch_html",
    "fetch_binary",
    "download_file",
    "DEFAULT_HEADERS",
    "HttpClient",
    
    # 图片处理
    "download_image",
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
    
    # 文本处理
    "normalize_text",
    "normalize_texts",
    "calculate_similarity",
    "find_best_match",
    "is_text_match",
    "SimilarityConstants",
]
