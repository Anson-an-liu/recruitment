"""
基础爬虫类 - 提供通用功能
"""
import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 常用User-Agent池
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
]


class BaseScraper(ABC):
    """爬虫基类"""

    def __init__(self, delay_range=(1, 3), max_retries=3, timeout=15):
        self.session = self._create_session(max_retries, timeout)
        self.delay_range = delay_range
        self.results: List[Dict] = []

    def _create_session(self, max_retries: int, timeout: int) -> requests.Session:
        """创建带重试机制的Session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.timeout = timeout
        return session

    def _get_headers(self, referer: str = None) -> Dict[str, str]:
        """生成随机请求头"""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        if referer:
            headers['Referer'] = referer
        return headers

    def _random_delay(self):
        """随机延迟，避免被封"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def safe_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """带重试和异常处理的安全GET请求"""
        for attempt in range(3):
            try:
                self._random_delay()
                headers = self._get_headers(kwargs.pop('referer', None))
                headers.update(kwargs.pop('headers', {}))
                response = self.session.get(url, headers=headers, **kwargs)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/3): {url} - {e}")
                if attempt == 2:
                    logger.error(f"请求最终失败: {url}")
                    return None
                time.sleep(2 ** attempt)

    def safe_post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """带重试和异常处理的安全POST请求"""
        for attempt in range(3):
            try:
                self._random_delay()
                headers = self._get_headers(kwargs.pop('referer', None))
                headers.update(kwargs.pop('headers', {}))
                response = self.session.post(url, headers=headers, **kwargs)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"POST请求失败 (尝试 {attempt + 1}/3): {url} - {e}")
                if attempt == 2:
                    return None
                time.sleep(2 ** attempt)

    @abstractmethod
    def search(self, keyword: str, city: str = None, pages: int = 5) -> List[Dict]:
        """
        搜索职位
        Args:
            keyword: 搜索关键词（如 Java、Python）
            city: 城市（可选）
            pages: 爬取页数
        Returns:
            标准化的职位信息列表
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: Dict) -> Dict:
        """
        标准化数据格式
        Args:
            raw_data: 原始数据
        Returns:
            {title, company, salary_min, salary_max, salary_avg, city, experience, education, 
             tags, description, source, url, publish_date}
        """
        pass

    def run(self, keywords: List[str], city: str = None, pages: int = 5) -> Dict[str, List[Dict]]:
        """
        批量运行搜索
        Returns: {keyword: [positions]}
        """
        all_results = {}
        for keyword in keywords:
            logger.info(f"正在搜索: {keyword}")
            results = self.search(keyword, city, pages)
            all_results[keyword] = results
            logger.info(f"搜索 {keyword} 完成，获取 {len(results)} 条记录")
        return all_results
