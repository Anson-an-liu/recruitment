"""
爬虫主运行脚本
协调多源爬虫和模拟数据生成
支持: 51job、BOSS直聘、智联招聘（Selenium）、模拟数据
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.job51_scraper import Job51Scraper
from scraper.boss_scraper import BossScraper
from scraper.zhaopin_scraper import ZhaopinSeleniumScraper, multi_city_scrape
from scraper.mock_data import generate_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_results(results: dict, output_dir: str, source: str):
    """保存爬取结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    for keyword, jobs in results.items():
        role = 'java' if 'java' in keyword.lower() else 'python'
        filename = f"{role}_jobs_{source}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 如果已有数据，合并去重
        existing = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        # 简单去重（按title+company+publish_date）
        existing_keys = {(j['title'], j.get('company', ''), j.get('publish_date', '')) for j in existing}
        new_jobs = [j for j in jobs if (j['title'], j.get('company', ''), j.get('publish_date', '')) not in existing_keys]
        
        all_jobs = existing + new_jobs
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存 {keyword}: {len(all_jobs)} 条记录 -> {filepath}")


def run_real_scraping(keywords: list, city: str = None, pages: int = 3) -> dict:
    """运行真实爬虫（51job + BOSS直聘）"""
    all_results = {}
    
    # 尝试51job
    logger.info("=" * 50)
    logger.info("开始爬取 51job...")
    logger.info("=" * 50)
    try:
        scraper = Job51Scraper(delay_range=(2, 4))
        for keyword in keywords:
            logger.info(f"51job 搜索: {keyword}")
            results = scraper.search(keyword, city, pages)
            key = keyword.lower()
            if key not in all_results:
                all_results[key] = []
            all_results[key].extend(results)
            logger.info(f"51job {keyword}: {len(results)} 条")
    except Exception as e:
        logger.error(f"51job 爬取失败: {e}")

    # 尝试BOSS直聘
    logger.info("=" * 50)
    logger.info("开始爬取 BOSS直聘...")
    logger.info("=" * 50)
    try:
        scraper = BossScraper(delay_range=(3, 6))
        for keyword in keywords:
            logger.info(f"BOSS直聘 搜索: {keyword}")
            results = scraper.search(keyword, city, pages)
            key = keyword.lower()
            if key not in all_results:
                all_results[key] = []
            all_results[key].extend(results)
            logger.info(f"BOSS直聘 {keyword}: {len(results)} 条")
    except Exception as e:
        logger.error(f"BOSS直聘 爬取失败: {e}")

    return all_results


def run_zhaopin_scraping(keywords: list, city: str = None, pages: int = 5,
                         multi_city: bool = False, cities: list = None,
                         headless: bool = True) -> dict:
    """
    运行智联招聘 Selenium 爬虫
    Args:
        keywords: 搜索关键词
        city: 单城市
        pages: 页数
        multi_city: 是否多城市采集
        cities: 多城市列表
        headless: 是否无头模式
    """
    logger.info("=" * 50)
    logger.info("开始爬取 联招聘 (Selenium)...")
    logger.info("=" * 50)

    all_results = {}

    try:
        if multi_city:
            logger.info(f"多城市采集模式，城市: {cities or '默认20个主要城市'}")
            all_results = multi_city_scrape(
                keywords=keywords,
                cities=cities,
                pages_per_city=pages,
                headless=headless
            )
        else:
            scraper = ZhaopinSeleniumScraper(headless=headless, max_pages=pages)
            all_results = scraper.run(keywords, city, pages)

        for keyword in keywords:
            key = keyword.lower()
            if key in all_results:
                logger.info(f"智联招聘 {keyword}: {len(all_results[key])} 条")
            else:
                all_results[key] = []

    except Exception as e:
        logger.error(f"智联招聘 爬取失败: {e}")
        for keyword in keywords:
            key = keyword.lower()
            if key not in all_results:
                all_results[key] = []

    return all_results


def main():
    parser = argparse.ArgumentParser(description='招聘信息爬虫')
    parser.add_argument('--mode', choices=['real', 'mock', 'zhaopin', 'all'], default='all',
                       help='爬取模式: real(51job+BOSS)、mock(模拟数据)、zhaopin(智联招聘Selenium)、all(全部)')
    parser.add_argument('--keywords', nargs='+', default=['Java', 'Python'],
                       help='搜索关键词，默认: Java Python')
    parser.add_argument('--city', type=str, default=None,
                       help='限定城市，如: 北京、上海')
    parser.add_argument('--pages', type=int, default=3,
                       help='每个关键词爬取页数，默认3')
    parser.add_argument('--min-count', type=int, default=50,
                       help='每类最少数据量，不足时用模拟数据补充')
    parser.add_argument('--output', type=str, default=None,
                       help='输出目录，默认 data/raw')
    # 智联招聘专用参数
    parser.add_argument('--multi-city', action='store_true',
                       help='智联招聘多城市采集')
    parser.add_argument('--cities', nargs='+', default=None,
                       help='智联招聘多城市采集的城市列表，如: 北京 上海 深圳')
    parser.add_argument('--no-headless', action='store_true',
                       help='显示浏览器窗口（调试用）')
    
    args = parser.parse_args()
    
    # 输出目录
    if args.output:
        raw_dir = args.output
        processed_dir = os.path.join(os.path.dirname(raw_dir), 'processed')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_dir = os.path.join(base_dir, 'data', 'raw')
        processed_dir = os.path.join(base_dir, 'data', 'processed')
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    logger.info(f"输出目录: {raw_dir}")
    logger.info(f"搜索关键词: {args.keywords}")
    logger.info(f"城市: {args.city or '全国'}")
    logger.info(f"模式: {args.mode}")

    headless = not args.no_headless
    
    if args.mode in ('real', 'all'):
        # 51job + BOSS 爬取
        logger.info("\n>>> 开始真实数据爬取 (51job + BOSS)...")
        real_results = run_real_scraping(args.keywords, args.city, args.pages)
        for keyword, jobs in real_results.items():
            save_results({keyword: jobs}, raw_dir, 'real')

    if args.mode in ('zhaopin', 'all'):
        # 智联招聘 Selenium 爬取
        logger.info("\n>>> 开始智联招聘 Selenium 数据爬取...")
        zhaopin_results = run_zhaopin_scraping(
            keywords=args.keywords,
            city=args.city,
            pages=args.pages,
            multi_city=args.multi_city,
            cities=args.cities,
            headless=headless
        )
        for keyword, jobs in zhaopin_results.items():
            save_results({keyword: jobs}, raw_dir, 'zhaopin')
    
    if args.mode in ('mock', 'all'):
        # 检查是否需要模拟数据
        need_mock = False
        
        if args.mode == 'mock':
            need_mock = True
        else:
            # 检查真实数据量是否足够
            for keyword in args.keywords:
                key = keyword.lower()
                role = 'java' if 'java' in key else 'python'
                total = 0
                for source in ['real', 'zhaopin']:
                    filepath = os.path.join(raw_dir, f"{role}_jobs_{source}.json")
                    if os.path.exists(filepath):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            total += len(json.load(f))
                if total < args.min_count:
                    logger.info(f"{keyword} 真实数据仅 {total} 条，需要模拟数据补充")
                    need_mock = True
        
        if need_mock:
            logger.info("\n>>> 生成模拟数据...")
            java_mock, python_mock = generate_dataset(raw_dir)
            
            for role, jobs in [('java', java_mock), ('python', python_mock)]:
                keyword = 'Java' if role == 'java' else 'Python'
                save_results({keyword: jobs}, raw_dir, 'mock')
    
    # 汇总信息
    logger.info("\n" + "=" * 50)
    logger.info("爬取完成! 数据汇总:")
    logger.info("=" * 50)
    
    for keyword in args.keywords:
        key = keyword.lower()
        role = 'java' if 'java' in key else 'python'
        total = 0
        for source in ['real', 'zhaopin', 'mock']:
            filepath = os.path.join(raw_dir, f"{role}_jobs_{source}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    count = len(json.load(f))
                total += count
                logger.info(f"  {keyword} ({source}): {count} 条")
        logger.info(f"  {keyword} 总计: {total} 条")
    
    logger.info(f"\n数据文件位置: {raw_dir}")
    logger.info("下一步: 运行 python -m analysis.analysis 进行数据分析")


if __name__ == '__main__':
    main()
