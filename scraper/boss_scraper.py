"""
BOSS直聘爬虫
"""
import re
import json
import logging
from typing import List, Dict, Optional

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BossScraper(BaseScraper):
    """BOSS直聘爬虫"""

    SEARCH_URL = "https://www.zhipin.com/web/geek/job"
    API_URL = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"

    def __init__(self, delay_range=(3, 6)):
        super().__init__(delay_range=delay_range)

    def search(self, keyword: str, city: str = None, pages: int = 5) -> List[Dict]:
        """搜索BOSS直聘职位"""
        results = []

        # BOSS直聘城市代码映射（常用城市）
        city_code = self._get_city_code(city) if city else '100010000'  # 默认全国

        for page in range(1, pages + 1):
            params = {
                'query': keyword,
                'city': city_code,
                'page': page,
                'pageSize': 30,
            }

            headers = {
                'Referer': 'https://www.zhipin.com/web/geek/job',
                'Origin': 'https://www.zhipin.com',
                'x-requested-with': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }

            logger.info(f"BOSS直聘 搜索: {keyword} 第{page}页")

            response = self.safe_get(
                self.API_URL,
                params=params,
                headers=headers,
                referer='https://www.zhipin.com/'
            )

            if not response:
                logger.warning(f"BOSS直聘 第{page}页获取失败")
                continue

            try:
                data = response.json()
                if data.get('code') != 0:
                    logger.warning(f"BOSS直聘 API返回错误: {data.get('message', '')}")
                    # 可能触发反爬，使用模拟数据
                    break

                job_list = data.get('zpData', {}).get('jobList', [])
                if not job_list:
                    logger.info(f"BOSS直聘 第{page}页无数据")
                    break

                for item in job_list:
                    normalized = self.normalize(item)
                    if normalized:
                        results.append(normalized)

                logger.info(f"BOSS直聘 第{page}页获取 {len(job_list)} 条记录")

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"BOSS直聘 解析第{page}页失败: {e}")
                continue

        return results

    def normalize(self, raw_data: Dict) -> Optional[Dict]:
        """标准化BOSS直聘数据"""
        try:
            salary_min, salary_max, salary_avg = self._parse_salary(raw_data.get('salaryDesc', ''))

            return {
                'title': raw_data.get('jobName', ''),
                'company': raw_data.get('brandName', ''),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_avg': salary_avg,
                'city': raw_data.get('cityName', raw_data.get('businessDistrict', '')),
                'experience': raw_data.get('jobExperience', ''),
                'education': raw_data.get('jobDegree', ''),
                'tags': raw_data.get('skills', []) if isinstance(raw_data.get('skills'), list) else [],
                'company_type': raw_data.get('brandIndustry', ''),
                'company_size': raw_data.get('brandScaleName', ''),
                'description': raw_data.get('jobDescription', '')[:500] if raw_data.get('jobDescription') else '',
                'source': 'BOSS直聘',
                'url': f"https://www.zhipin.com/job_detail/{raw_data.get('encryptJobId', '')}.html",
                'publish_date': raw_data.get('activeTimeDesc', ''),
            }
        except Exception as e:
            logger.debug(f"BOSS直聘数据标准化失败: {e}")
            return None

    def _parse_salary(self, salary_text: str) -> tuple:
        """
        解析BOSS直聘薪资
        如: "15K-25K" -> (15000, 25000, 20000)
            "8K-12K·13薪" -> (8000, 12000, 10000)
        """
        if not salary_text:
            return 0, 0, 0

        numbers = re.findall(r'[\d.]+', salary_text)
        if not numbers:
            return 0, 0, 0

        if len(numbers) >= 2:
            low = float(numbers[0]) * 1000
            high = float(numbers[1]) * 1000
        else:
            high = float(numbers[0]) * 1000
            low = high

        avg = (low + high) / 2
        return round(low), round(high), round(avg)

    @staticmethod
    def _get_city_code(city_name: str) -> str:
        """获取BOSS直聘城市代码"""
        city_map = {
            '北京': '101010100', '上海': '101020100', '广州': '101280100',
            '深圳': '101280600', '杭州': '101210100', '成都': '101270100',
            '南京': '101190100', '武汉': '101200100', '西安': '101110100',
            '重庆': '101040100', '长沙': '101250100', '苏州': '101190400',
            '天津': '101030100', '郑州': '101180100', '合肥': '101220100',
            '厦门': '101230200', '福州': '101230100', '济南': '101120100',
            '青岛': '101120200', '大连': '101070200',
        }
        return city_map.get(city_name, '100010000')
