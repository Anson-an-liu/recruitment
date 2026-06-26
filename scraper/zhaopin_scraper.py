"""
智联招聘 Selenium 爬虫
通过浏览器自动化方式采集招聘数据，模拟"后羿采集器"功能
"""
import re
import json
import time
import random
import logging
import os
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


# 智联招聘城市代码映射
ZHAOPIN_CITY_CODES = {
    '北京': '530', '上海': '538', '广州': '763',
    '深圳': '765', '杭州': '653', '成都': '801',
    '南京': '635', '武汉': '736', '西安': '854',
    '重庆': '854', '长沙': '749', '苏州': '636',
    '天津': '531', '郑州': '719', '合肥': '654',
    '厦门': '682', '福州': '681', '济南': '613',
    '青岛': '609', '大连': '580',
}


class ZhaopinSeleniumScraper:
    """智联招聘 Selenium 爬虫 - 浏览器自动化采集"""

    SEARCH_URL = "https://sou.zhaopin.com/?jl={city}&kw={keyword}&p={page}"

    def __init__(self, headless=True, delay_range=(2, 5), max_pages=5):
        self.headless = headless
        self.delay_range = delay_range
        self.max_pages = max_pages
        self.driver = None
        self.results = []

    def _init_driver(self):
        """初始化 Chrome 浏览器"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=zh-CN')
        # 反反爬设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # 自动管理 ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # 隐藏 webdriver 特征
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            '''
        })

        logger.info("Chrome 浏览器已启动")

    def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def search(self, keyword: str, city: str = None, pages: int = None) -> List[Dict]:
        """
        搜索智联招聘职位
        Args:
            keyword: 搜索关键词（Java、Python等）
            city: 城市名称
            pages: 爬取页数
        Returns:
            标准化的职位信息列表
        """
        if pages is None:
            pages = self.max_pages

        if self.driver is None:
            self._init_driver()

        city_code = ZHAOPIN_CITY_CODES.get(city, '') if city else ''
        results = []

        for page in range(1, pages + 1):
            url = self.SEARCH_URL.format(
                city=city_code,
                keyword=keyword,
                page=page
            )
            logger.info(f"智联招聘 搜索: {keyword} {city or '全国'} 第{page}页")

            try:
                self.driver.get(url)
                self._random_delay()

                # 等待职位列表加载（使用实际页面结构的选择器）
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.joblist-box__item'))
                    )
                except TimeoutException:
                    logger.warning(f"智联招聘 第{page}页加载超时，可能无数据或被反爬")
                    # 保存页面源码用于调试
                    debug_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'raw', f'zhaopin_debug_page{page}.html'
                    )
                    os.makedirs(os.path.dirname(debug_path), exist_ok=True)
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info(f"调试页面已保存: {debug_path}")
                    continue

                # 解析职位列表
                page_results = self._parse_job_list(keyword)
                if not page_results:
                    logger.info(f"智联招聘 第{page}页未解析到数据")
                    # 保存调试页面
                    debug_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'raw', f'zhaopin_debug_empty_page{page}.html'
                    )
                    os.makedirs(os.path.dirname(debug_path), exist_ok=True)
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info(f"空结果调试页面已保存: {debug_path}")
                    break

                results.extend(page_results)
                logger.info(f"智联招聘 第{page}页获取 {len(page_results)} 条记录")

                self._random_delay()

            except WebDriverException as e:
                logger.error(f"智联招聘 浏览器异常: {e}")
                break

        logger.info(f"智联招聘 搜索 {keyword} 完成，共获取 {len(results)} 条")
        return results

    def _parse_job_list(self, role: str) -> List[Dict]:
        """解析当前页面的职位列表"""
        results = []

        # 使用实际页面结构的选择器
        job_items = []
        selectors = [
            (By.CSS_SELECTOR, 'div.joblist-box__item'),
            (By.CSS_SELECTOR, '[ka*="search-job-item"]'),
            (By.CSS_SELECTOR, 'div.job-list-item'),
        ]

        for by, selector in selectors:
            try:
                job_items = self.driver.find_elements(by, selector)
                if job_items:
                    break
            except NoSuchElementException:
                continue

        if not job_items:
            logger.warning("未找到职位列表元素")
            return []

        for item in job_items:
            try:
                normalized = self._parse_single_job(item, role)
                if normalized:
                    results.append(normalized)
            except (StaleElementReferenceException, NoSuchElementException) as e:
                logger.debug(f"解析单个职位失败: {e}")
                continue

        return results

    def _parse_single_job(self, element, role: str) -> Optional[Dict]:
        """解析单个职位信息（基于智联招聘实际页面结构）"""
        result = {
            'title': '',
            'company': '',
            'salary_min': 0,
            'salary_max': 0,
            'salary_avg': 0,
            'city': '',
            'experience': '',
            'education': '',
            'tags': [],
            'company_type': '',
            'company_size': '',
            'description': '',
            'source': '智联招聘',
            'role': role,
            'url': '',
            'publish_date': '',
        }

        # 职位名称 + 链接（实际结构：jobinfo__name-row > a.jobinfo__name）
        try:
            name_el = element.find_element(By.CSS_SELECTOR, 'a.jobinfo__name')
            result['title'] = name_el.text.strip()
            result['url'] = name_el.get_attribute('href') or ''
        except NoSuchElementException:
            pass

        # 薪资（实际结构：jobinfo__top > p.jobinfo__salary）
        try:
            salary_el = element.find_element(By.CSS_SELECTOR, 'p.jobinfo__salary')
            salary_text = salary_el.text.strip()
            if salary_text and salary_text != '面议':
                salary_min, salary_max, salary_avg = self._parse_salary(salary_text)
                result['salary_min'] = salary_min
                result['salary_max'] = salary_max
                result['salary_avg'] = salary_avg
        except NoSuchElementException:
            pass

        # 技术标签（实际结构：jobinfo__tag > div.joblist-box__item-tag）
        try:
            tag_elements = element.find_elements(By.CSS_SELECTOR, 'div.jobinfo__tag div.joblist-box__item-tag')
            raw_tags = [t.text.strip() for t in tag_elements if t.text.strip()]
            # 过滤掉明显不是技术栈的标签
            NON_TECH_TAGS = {
                '本科', '硕士', '博士', '大专', '高中', '中专', '学历不限',
                '不限', '无经验', '在校生', '应届生',
                '1年以下', '1-3年', '3-5年', '5-10年', '10年以上',
                '10k以上', '15k以上', '20k以上', '五险一金', '五险', '六险一金',
                '双休', '弹性工作', '年终奖', '股票期权', '带薪年假',
                '全国可安排', '全国', '线上面试', '全程线上面试',
                '24届', '25届', '26届', '无经验可投', '接受断档',
                '考研失利', '考公失败', '接受小白',
            }
            # 过滤规则：标签太长（超过20字符很可能是职位描述片段）、或者是非技术词
            result['tags'] = [t for t in raw_tags
                             if len(t) <= 20 and t not in NON_TECH_TAGS
                             and not any(x in t for x in ['经验', '以上', '以下', '可投', '全程', '双休', '五险', '六险', '年终', '年薪', '面试', '可安排', '应届', '在校', '考研', '考公'])]
        except NoSuchElementException:
            pass

        # 城市、经验、学历（实际结构：jobinfo__other-info > jobinfo__other-info-item）
        try:
            other_info_items = element.find_elements(By.CSS_SELECTOR, 'div.jobinfo__other-info div.jobinfo__other-info-item')
            for item_el in other_info_items:
                text = item_el.text.strip()
                if not text:
                    continue
                # 城市信息通常包含"·"分隔（如"北京·朝阳·团结湖"）
                if '·' in text or any(c in text for c in ['北京', '上海', '深圳', '广州', '杭州',
                                                          '成都', '南京', '武汉', '西安', '长沙',
                                                          '苏州', '天津', '郑州', '合肥', '厦门',
                                                          '济南', '青岛', '大连', '福州', '重庆']):
                    # 提取城市（取第一个·之前的部分）
                    if '·' in text:
                        result['city'] = text.split('·')[0]
                    else:
                        result['city'] = text
                elif '年' in text or text in ['应届生', '不限', '无经验']:
                    result['experience'] = text
                elif text in ['大专', '本科', '硕士', '博士', '不限', '中专', '高中', '初中']:
                    result['education'] = text
        except NoSuchElementException:
            pass

        # 公司名称（实际结构：companyinfo__top > a.companyinfo__name）
        try:
            company_name_el = element.find_element(By.CSS_SELECTOR, 'a.companyinfo__name')
            result['company'] = company_name_el.text.strip()
        except NoSuchElementException:
            # 短名称版本
            try:
                company_name_el = element.find_element(By.CSS_SELECTOR, 'a.companyinfo__name-short')
                result['company'] = company_name_el.text.strip()
            except NoSuchElementException:
                pass

        # 公司标签：类型、规模、行业（实际结构：companyinfo__tag > div.joblist-box__item-tag）
        try:
            company_tag_elements = element.find_elements(By.CSS_SELECTOR, 'div.companyinfo__tag div.joblist-box__item-tag')
            for tag_el in company_tag_elements:
                text = tag_el.text.strip()
                # 公司规模：必须包含"人"且前面有数字（如"20人以下"、"100-299人"、"少于20人"）
                # 不能只匹配"人"，否则"人力资源"、"人工智能"等行业词会被误判为规模
                import re
                if re.search(r'\d+.*人', text) or '少于' in text:
                    result['company_size'] = text
                elif text in ['民营', '国企', '合资', '外商独资', '上市公司', '事业单位',
                              '股份制企业', '集体企业', '独资企业']:
                    result['company_type'] = text
                # 行业信息也在这里，但暂不单独字段存储
        except NoSuchElementException:
            pass

        # 如果标题为空，说明解析失败
        if not result['title']:
            return None

        # 填补缺失字段
        if not result['city']:
            result['city'] = '未知'
        if not result['role']:
            result['role'] = role

        return result

    def _parse_salary(self, salary_text: str) -> tuple:
        """
        解析智联招聘薪资文本
        如: "10K-15K" -> (10000, 15000, 12500)
            "8000-15000元" -> (8000, 15000, 10000)
            "1.2-1.5万" -> (12000, 15000, 13500)
            "8千-1.2万" -> (8000, 12000, 10000)
            "1.5-2万/月" -> (15000, 20000, 17500)
            "面议" -> (0, 0, 0)
        """
        if not salary_text:
            return 0, 0, 0

        salary_text = salary_text.strip()

        if salary_text == '面议' or salary_text == ' Negotiable':
            return 0, 0, 0

        # 判断月薪/年薪
        is_year = '年' in salary_text and '月' not in salary_text

        # 去掉"元"、"元/月"等后缀
        salary_clean = re.sub(r'[元/月年]', '', salary_text)

        # 确定单位
        unit = 1  # 默认单位是元
        if '万' in salary_clean:
            unit = 10000
        elif 'K' in salary_clean.upper():
            unit = 1000
        elif '千' in salary_clean:
            unit = 1000

        # 提取数字
        numbers = re.findall(r'[\d.]+', salary_clean)
        if not numbers:
            return 0, 0, 0

        if len(numbers) >= 2:
            low = float(numbers[0]) * unit
            high = float(numbers[1]) * unit
        else:
            val = float(numbers[0]) * unit
            if '以下' in salary_text:
                low, high = 0, val
            elif '以上' in salary_text:
                low, high = val, val * 1.5
            else:
                low, high = val, val

        if is_year:
            low = low / 12
            high = high / 12

        avg = (low + high) / 2
        return round(low), round(high), round(avg)

    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            logger.info("Chrome 浏览器已关闭")

    def run(self, keywords: List[str], city: str = None, pages: int = None) -> Dict[str, List[Dict]]:
        """
        批量运行搜索
        Args:
            keywords: 搜索关键词列表
            city: 城市名称
            pages: 每个关键词爬取页数
        Returns:
            {keyword: [positions]}
        """
        if pages is None:
            pages = self.max_pages

        all_results = {}
        try:
            for keyword in keywords:
                logger.info(f"正在搜索: {keyword}")
                results = self.search(keyword, city, pages)
                all_results[keyword] = results
                logger.info(f"搜索 {keyword} 完成，获取 {len(results)} 条记录")
        finally:
            self.close()

        return all_results

    def scrape_multiple_cities(self, keywords: List[str], cities: List[str] = None, pages_per_city: int = 3) -> Dict[str, List[Dict]]:
        """
        多城市采集（类似后羿采集器的批量采集功能）
        Args:
            keywords: 搜索关键词列表
            cities: 城市列表，默认采集主要城市
            pages_per_city: 每个城市每关键词的页数
        Returns:
            {keyword: [positions]}
        """
        if cities is None:
            cities = list(ZHAOPIN_CITY_CODES.keys())

        all_results = {}
        for keyword in keywords:
            all_results[keyword] = []

        try:
            for city in cities:
                logger.info(f"=== 开始采集城市: {city} ===")
                for keyword in keywords:
                    results = self.search(keyword, city, pages_per_city)
                    all_results[keyword].extend(results)
                    logger.info(f"{city} - {keyword}: {len(results)} 条")
                    self._random_delay()
        finally:
            self.close()

        # 汇总
        for keyword in keywords:
            logger.info(f"{keyword} 多城市采集总计: {len(all_results[keyword])} 条")

        return all_results


def quick_scrape(keywords=['Java', 'Python'], city=None, pages=5, headless=True):
    """
    快速采集接口 - 一行代码即可采集数据
    Args:
        keywords: 搜索关键词列表
        city: 城市（可选）
        pages: 爬取页数
        headless: 是否无头模式
    Returns:
        {keyword: [job_list]}
    """
    scraper = ZhaopinSeleniumScraper(headless=headless, max_pages=pages)
    return scraper.run(keywords, city, pages)


def multi_city_scrape(keywords=['Java', 'Python'], cities=None, pages_per_city=3, headless=True):
    """
    多城市批量采集接口
    Args:
        keywords: 搜索关键词列表
        cities: 城市列表
        pages_per_city: 每城市每关键词页数
        headless: 是否无头模式
    Returns:
        {keyword: [job_list]}
    """
    scraper = ZhaopinSeleniumScraper(headless=headless, max_pages=pages_per_city)
    return scraper.scrape_multiple_cities(keywords, cities, pages_per_city)


if __name__ == '__main__':
    # 单城市测试
    import argparse

    parser = argparse.ArgumentParser(description='智联招聘 Selenium 爬虫')
    parser.add_argument('--keywords', nargs='+', default=['Java', 'Python'],
                        help='搜索关键词')
    parser.add_argument('--city', type=str, default=None,
                        help='限定城市，如: 北京、上海')
    parser.add_argument('--pages', type=int, default=5,
                        help='爬取页数')
    parser.add_argument('--multi-city', action='store_true',
                        help='是否多城市采集')
    parser.add_argument('--cities', nargs='+', default=None,
                        help='指定城市列表，如: 北京 上海 深圳')
    parser.add_argument('--no-headless', action='store_true',
                        help='显示浏览器窗口（调试用）')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    headless = not args.no_headless

    if args.multi_city:
        cities = args.cities if args.cities else None
        results = multi_city_scrape(args.keywords, cities=cities, pages_per_city=args.pages, headless=headless)
    else:
        results = quick_scrape(args.keywords, city=args.city, pages=args.pages, headless=headless)

    # 保存结果
    output_dir = args.output or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'raw'
    )
    os.makedirs(output_dir, exist_ok=True)

    for keyword, jobs in results.items():
        role = 'java' if 'java' in keyword.lower() else 'python'
        filepath = os.path.join(output_dir, f'{role}_jobs_zhaopin.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"{keyword}: {len(jobs)} 条 -> {filepath}")
