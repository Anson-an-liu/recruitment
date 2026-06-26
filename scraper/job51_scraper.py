"""
51job（前程无忧）爬虫
"""
import re
import json
import logging
from typing import List, Dict, Optional

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class Job51Scraper(BaseScraper):
    """51job爬虫"""

    BASE_URL = "https://search.51job.com/list/000000,000000,0000,00,9,99,{},2,{}.html"
    DETAIL_URL = "https://jobs.51job.com/{}/{}.html"
    API_URL = "https://search.51job.com/list/000000,000000,0000,00,9,99,{},2,{}.html"

    def __init__(self, delay_range=(2, 4)):
        super().__init__(delay_range=delay_range)

    def search(self, keyword: str, city: str = None, pages: int = 5) -> List[Dict]:
        """搜索51job职位"""
        results = []
        keyword_encoded = keyword

        for page in range(1, pages + 1):
            url = self.API_URL.format(keyword_encoded, page)
            logger.info(f"51job 搜索: {keyword} 第{page}页")

            response = self.safe_get(url, referer="https://www.51job.com/")
            if not response:
                logger.warning(f"51job 第{page}页获取失败，尝试下一页")
                continue

            try:
                # 51job页面数据在window.__SEARCH_RESULT__中
                match = re.search(r'window\.__SEARCH_RESULT__\s*=\s*({.*?});', response.text, re.DOTALL)
                if not match:
                    # 尝试另一种匹配
                    match = re.search(r'window\.__SEARCH_RESULT__\s*=\s*(\{.*?\});</script>', response.text, re.DOTALL)
                if not match:
                    logger.warning(f"51job 第{page}页未找到搜索数据")
                    continue

                data = json.loads(match.group(1))
                engine_search_result = data.get('engine_search_result', [])
                
                if not engine_search_result:
                    logger.info(f"51job 第{page}页无数据，搜索结束")
                    break

                for item in engine_search_result:
                    normalized = self.normalize(item)
                    if normalized:
                        results.append(normalized)

                logger.info(f"51job 第{page}页获取 {len(engine_search_result)} 条记录")

            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.error(f"51job 解析第{page}页失败: {e}")
                continue

        return results

    def normalize(self, raw_data: Dict) -> Optional[Dict]:
        """标准化51job数据"""
        try:
            # 解析薪资
            salary_text = raw_data.get('providesalary_text', '')
            salary_min, salary_max, salary_avg = self._parse_salary(salary_text)

            # 解析城市
            workarea = raw_data.get('workarea_text', '')
            city = workarea.split('-')[0] if workarea else '未知'

            return {
                'title': raw_data.get('job_name', ''),
                'company': raw_data.get('company_name', ''),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_avg': salary_avg,
                'city': city,
                'experience': raw_data.get('attribute_text', [''])[-2] if len(raw_data.get('attribute_text', [])) >= 2 else '',
                'education': raw_data.get('attribute_text', [''])[-1] if raw_data.get('attribute_text', []) else '',
                'tags': raw_data.get('jobwelf', '').split(',') if raw_data.get('jobwelf') else [],
                'company_type': raw_data.get('companytype_text', ''),
                'company_size': raw_data.get('companysize_text', ''),
                'description': raw_data.get('job_info', '')[:500] if raw_data.get('job_info') else '',
                'source': '51job',
                'url': raw_data.get('job_href', ''),
                'publish_date': raw_data.get('updatedate', ''),
            }
        except Exception as e:
            logger.debug(f"51job数据标准化失败: {e}")
            return None

    def _parse_salary(self, salary_text: str) -> tuple:
        """
        解析薪资文本
        如: "1.5-2.5万/月" -> (15000, 25000, 20000)
            "8千-1.2万/月" -> (8000, 12000, 10000)
            "2-3万/年" -> (20000, 30000, 25000) 然后除以12
            "5千以下/月" -> (0, 5000, 2500)
        """
        if not salary_text:
            return 0, 0, 0

        salary_text = salary_text.strip()

        # 判断是月薪还是年薪
        is_year = '年' in salary_text
        is_day = '天' in salary_text
        is_hour = '时' in salary_text

        # 提取数字
        numbers = re.findall(r'[\d.]+', salary_text)
        if not numbers:
            return 0, 0, 0

        # 判断单位
        unit = 1
        if '万' in salary_text:
            unit = 10000
        elif '千' in salary_text:
            unit = 1000

        if len(numbers) >= 2:
            low = float(numbers[0]) * unit
            high = float(numbers[1]) * unit
        else:
            high = float(numbers[0]) * unit
            if '以下' in salary_text:
                low = 0
            else:
                low = high

        # 年薪/日薪转月薪
        if is_year:
            low = low / 12
            high = high / 12
        elif is_day:
            low = low * 22
            high = high * 22
        elif is_hour:
            low = low * 8 * 22
            high = high * 8 * 22

        avg = (low + high) / 2
        return round(low), round(high), round(avg)
