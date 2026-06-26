"""
数据分析与统计模块
Java vs Python 招聘信息多维度对比分析
"""
import os
import sys
import json
import logging
from collections import Counter, defaultdict
from typing import List, Dict, Any

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.data_cleaner import clean_and_save

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RecruitmentAnalyzer:
    """招聘数据分析器"""

    def __init__(self, processed_dir: str):
        self.processed_dir = processed_dir
        self.java_data = []
        self.python_data = []
        self._load_data()

    def _load_data(self):
        """加载清洗后的数据"""
        java_path = os.path.join(self.processed_dir, 'java_jobs_cleaned.json')
        python_path = os.path.join(self.processed_dir, 'python_jobs_cleaned.json')

        if os.path.exists(java_path):
            with open(java_path, 'r', encoding='utf-8') as f:
                self.java_data = json.load(f)
            logger.info(f"加载Java数据: {len(self.java_data)} 条")

        if os.path.exists(python_path):
            with open(python_path, 'r', encoding='utf-8') as f:
                self.python_data = json.load(f)
            logger.info(f"加载Python数据: {len(self.python_data)} 条")

    def get_summary(self) -> Dict[str, Any]:
        """获取总体概览"""
        java_count = len(self.java_data)
        python_count = len(self.python_data)

        java_avg_salary = self._avg(self.java_data, 'salary_avg')
        python_avg_salary = self._avg(self.python_data, 'salary_avg')

        java_max_salary = max((j.get('salary_max', 0) for j in self.java_data), default=0)
        python_max_salary = max((j.get('salary_max', 0) for j in self.python_data), default=0)

        return {
            'total': java_count + python_count,
            'java_count': java_count,
            'python_count': python_count,
            'java_avg_salary': round(java_avg_salary),
            'python_avg_salary': round(python_avg_salary),
            'java_max_salary': java_max_salary,
            'python_max_salary': python_max_salary,
            'salary_diff': round(python_avg_salary - java_avg_salary),
        }

    def salary_distribution(self) -> Dict[str, Any]:
        """薪资分布对比"""
        ranges = [
            ('5K以下', 0, 5000),
            ('5K-10K', 5000, 10000),
            ('10K-15K', 10000, 15000),
            ('15K-20K', 15000, 20000),
            ('20K-25K', 20000, 25000),
            ('25K-30K', 25000, 30000),
            ('30K-40K', 30000, 40000),
            ('40K以上', 40000, 999999),
        ]

        result = {'categories': [r[0] for r in ranges], 'java': [], 'python': []}

        for label, low, high in ranges:
            result['java'].append(sum(1 for j in self.java_data if low <= j.get('salary_avg', 0) < high))
            result['python'].append(sum(1 for j in self.python_data if low <= j.get('salary_avg', 0) < high))

        return result

    def city_distribution(self) -> Dict[str, Any]:
        """城市分布对比"""
        java_cities = Counter(j.get('city', '未知') for j in self.java_data)
        python_cities = Counter(j.get('city', '未知') for j in self.python_data)

        # 取Top10城市
        all_cities = set(list(java_cities.keys()) + list(python_cities.keys()))
        city_totals = {c: java_cities.get(c, 0) + python_cities.get(c, 0) for c in all_cities}
        top_cities = sorted(city_totals, key=city_totals.get, reverse=True)[:10]

        return {
            'cities': top_cities,
            'java': [java_cities.get(c, 0) for c in top_cities],
            'python': [python_cities.get(c, 0) for c in top_cities],
        }

    def city_salary_comparison(self) -> Dict[str, Any]:
        """各城市平均薪资对比"""
        cities = set(j.get('city', '') for j in self.java_data + self.python_data if j.get('city'))

        result = {'cities': [], 'java_salary': [], 'python_salary': []}

        for city in sorted(cities):
            java_in_city = [j for j in self.java_data if j.get('city') == city]
            python_in_city = [j for j in self.python_data if j.get('city') == city]

            if len(java_in_city) >= 1 and len(python_in_city) >= 1:
                result['cities'].append(city)
                result['java_salary'].append(round(self._avg(java_in_city, 'salary_avg')))
                result['python_salary'].append(round(self._avg(python_in_city, 'salary_avg')))

        # 只保留Top12
        if len(result['cities']) > 12:
            # 按Java薪资排序取Top12
            combined = list(zip(result['cities'], result['java_salary'], result['python_salary']))
            combined.sort(key=lambda x: x[1], reverse=True)
            combined = combined[:12]
            result['cities'], result['java_salary'], result['python_salary'] = zip(*combined)
            result['cities'] = list(result['cities'])
            result['java_salary'] = list(result['java_salary'])
            result['python_salary'] = list(result['python_salary'])

        return result

    def experience_analysis(self) -> Dict[str, Any]:
        """经验要求分析"""
        exp_order = ['应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上', '不限']

        java_exp = Counter(j.get('experience', '不限') for j in self.java_data)
        python_exp = Counter(j.get('experience', '不限') for j in self.python_data)

        return {
            'categories': exp_order,
            'java': [java_exp.get(e, 0) for e in exp_order],
            'python': [python_exp.get(e, 0) for e in exp_order],
        }

    def experience_salary(self) -> Dict[str, Any]:
        """不同经验级别的平均薪资对比"""
        exp_order = ['应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上']

        result = {'categories': exp_order, 'java': [], 'python': []}

        for exp in exp_order:
            java_sal = [j['salary_avg'] for j in self.java_data if j.get('experience') == exp and j.get('salary_avg', 0) > 0]
            python_sal = [j['salary_avg'] for j in self.python_data if j.get('experience') == exp and j.get('salary_avg', 0) > 0]

            result['java'].append(round(self._avg_list(java_sal)))
            result['python'].append(round(self._avg_list(python_sal)))

        return result

    def education_analysis(self) -> Dict[str, Any]:
        """学历要求分析"""
        edu_order = ['大专', '本科', '硕士', '博士', '不限']

        java_edu = Counter(j.get('education', '不限') for j in self.java_data)
        python_edu = Counter(j.get('education', '不限') for j in self.python_data)

        return {
            'categories': edu_order,
            'java': [java_edu.get(e, 0) for e in edu_order],
            'python': [python_edu.get(e, 0) for e in edu_order],
        }

    def education_salary(self) -> Dict[str, Any]:
        """不同学历的平均薪资对比"""
        edu_order = ['大专', '本科', '硕士']

        result = {'categories': edu_order, 'java': [], 'python': []}

        for edu in edu_order:
            java_sal = [j['salary_avg'] for j in self.java_data if j.get('education') == edu and j.get('salary_avg', 0) > 0]
            python_sal = [j['salary_avg'] for j in self.python_data if j.get('education') == edu and j.get('salary_avg', 0) > 0]

            result['java'].append(round(self._avg_list(java_sal)))
            result['python'].append(round(self._avg_list(python_sal)))

        return result

    def top_tags(self) -> Dict[str, Any]:
        """热门技术标签对比"""
        java_tags = Counter()
        for j in self.java_data:
            for tag in j.get('tags', []):
                java_tags[tag] += 1

        python_tags = Counter()
        for j in self.python_data:
            for tag in j.get('tags', []):
                python_tags[tag] += 1

        java_top = java_tags.most_common(15)
        python_top = python_tags.most_common(15)

        return {
            'java_tags': [t[0] for t in java_top],
            'java_values': [t[1] for t in java_top],
            'python_tags': [t[0] for t in python_top],
            'python_values': [t[1] for t in python_top],
        }

    def company_size_analysis(self) -> Dict[str, Any]:
        """公司规模分布"""
        # 智联招聘实际使用的大小分类
        size_order = ['20人以下', '20-99人', '100-299人', '300-499人', '500-999人',
                      '1000-9999人', '10000人以上']

        java_size = Counter(j.get('company_size', '') for j in self.java_data)
        python_size = Counter(j.get('company_size', '') for j in self.python_data)

        # 收集实际存在的其他规模标签
        all_sizes = set(list(java_size.keys()) + list(python_size.keys()))
        extra = sorted([s for s in all_sizes if s and s not in size_order])
        size_order = size_order + extra

        return {
            'categories': size_order,
            'java': [java_size.get(s, 0) for s in size_order],
            'python': [python_size.get(s, 0) for s in size_order],
        }

    def full_analysis(self) -> Dict[str, Any]:
        """执行完整分析"""
        return {
            'summary': self.get_summary(),
            'salary_distribution': self.salary_distribution(),
            'city_distribution': self.city_distribution(),
            'city_salary_comparison': self.city_salary_comparison(),
            'experience_analysis': self.experience_analysis(),
            'experience_salary': self.experience_salary(),
            'education_analysis': self.education_analysis(),
            'education_salary': self.education_salary(),
            'top_tags': self.top_tags(),
            'company_size': self.company_size_analysis(),
        }

    @staticmethod
    def _avg(data: List[Dict], key: str) -> float:
        """计算平均值（排除零值）"""
        values = [d.get(key, 0) for d in data if d.get(key, 0) > 0]
        return sum(values) / len(values) if values else 0

    @staticmethod
    def _avg_list(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0


def main():
    """主分析流程"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    processed_dir = os.path.join(base_dir, 'data', 'processed')

    # Step 1: 清洗数据
    logger.info("Step 1: 数据清洗...")
    clean_and_save(raw_dir, processed_dir)

    # Step 2: 分析
    logger.info("Step 2: 数据分析...")
    analyzer = RecruitmentAnalyzer(processed_dir)
    results = analyzer.full_analysis()

    # Step 3: 保存分析结果
    output_path = os.path.join(processed_dir, 'analysis_result.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Step 4: 打印摘要
    summary = results['summary']
    logger.info("=" * 50)
    logger.info("分析完成!")
    logger.info("=" * 50)
    logger.info(f"Java岗位总数: {summary['java_count']}")
    logger.info(f"Python岗位总数: {summary['python_count']}")
    logger.info(f"Java平均月薪: ¥{summary['java_avg_salary']:,}")
    logger.info(f"Python平均月薪: ¥{summary['python_avg_salary']:,}")
    logger.info(f"薪资差异: ¥{summary['salary_diff']:,}")
    logger.info(f"分析结果已保存: {output_path}")

    return results


if __name__ == '__main__':
    main()
