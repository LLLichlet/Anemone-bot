"""
网络请求工具 - HTTP 客户端封装

提供异步 HTTP 请求工具，支持重试机制和错误处理。

注意：此模块需要 httpx，导入失败时相关函数不可用。
"""

from typing import Optional, Dict
import logging

# 导入保护
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore

logger = logging.getLogger("plugins.utils.network")


def _check_httpx():
    """检查 httpx 是否可用"""
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is not available. Install with: pip install httpx")

# 默认请求头
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


async def fetch_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[str]:
    """异步获取网页 HTML"""
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"Request failed [{url}]: {e}")
        return None


async def fetch_binary(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[bytes]:
    """异步获取二进制数据"""
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as e:
        logger.error(f"Request failed [{url}]: {e}")
        return None


async def download_file(
    url: str,
    save_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> bool:
    """
    异步下载文件到本地
    
    Args:
        url: 文件 URL
        save_path: 保存路径
        headers: 自定义请求头
        timeout: 超时时间（秒）
    
    Returns:
        是否下载成功
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        logger.info(f"Downloaded file to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Download failed [{url}]: {e}")
        return False


class HttpClient:
    """
    HTTP 客户端类 - 支持连接池和复用
    
    适用于需要频繁请求同一主机的场景。
    
    Example:
        >>> client = HttpClient(timeout=10.0)
        >>> html = await client.get("https://api.example.com/data")
        >>> await client.close()
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        follow_redirects: bool = True
    ):
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=self.follow_redirects
            )
        return self._client
    
    async def get(self, url: str, **kwargs) -> Optional[str]:
        """GET 请求，返回文本"""
        try:
            client = await self._get_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"GET failed [{url}]: {e}")
            return None
    
    async def get_bytes(self, url: str, **kwargs) -> Optional[bytes]:
        """GET 请求，返回二进制"""
        try:
            client = await self._get_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"GET failed [{url}]: {e}")
            return None
    
    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """POST 请求"""
        try:
            client = await self._get_client()
            response = await client.post(url, data=data, json=json, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST failed [{url}]: {e}")
            return None
    
    async def close(self) -> None:
        """关闭客户端，释放资源"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self) -> 'HttpClient':
        """异步上下文管理器入口"""
        await self._get_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()
