"""基础爬虫类"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from ..config import REQUEST_TIMEOUT, REQUEST_RETRY_TIMES, REQUEST_HEADERS


class BaseCrawler(ABC):
    """爬虫基类，定义通用接口"""

    def __init__(self, name: str, api_available: bool = False):
        self.name = name
        self.api_available = api_available
        self.client = None
        logger.info(f"初始化爬虫: {name}, API可用: {api_available}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers=REQUEST_HEADERS,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()

    async def fetch_with_retry(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """带重试的HTTP请求"""
        last_error = None

        for attempt in range(REQUEST_RETRY_TIMES):
            try:
                logger.debug(f"请求 {url} (尝试 {attempt + 1}/{REQUEST_RETRY_TIMES})")
                response = await self.client.get(url, **kwargs)
                response.raise_for_status()
                return response

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"请求失败 {url}: {e}")
                if attempt < REQUEST_RETRY_TIMES - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"HTTP错误 {url}: {e.response.status_code}")
                if e.response.status_code in [429, 503]:  # 限流或服务不可用
                    if attempt < REQUEST_RETRY_TIMES - 1:
                        await asyncio.sleep(2 ** attempt)
                else:
                    break  # 其他HTTP错误不重试

        logger.error(f"请求最终失败 {url}: {last_error}")
        return None

    @abstractmethod
    async def crawl(self) -> List[Dict[str, Any]]:
        """爬取数据的抽象方法，子类必须实现"""
        pass

    def format_item(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化单条数据为标准格式"""
        return {
            'name': raw_data.get('name', 'Unknown'),
            'url': raw_data.get('url', '#'),
            'description': raw_data.get('description', ''),
            'source': self.name,
            'crawled_at': self._get_current_time()
        }

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def validate_response(self, response: httpx.Response) -> bool:
        """验证响应是否有效"""
        if response.status_code != 200:
            return False

        content_type = response.headers.get('content-type', '')
        if 'json' in content_type:
            try:
                response.json()
                return True
            except:
                return False
        elif 'html' in content_type:
            return len(response.text) > 0

        return True