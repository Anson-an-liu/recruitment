"""
数据分析模块 - 数据清洗与预处理
"""
import os
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_salary(job: Dict) -> Dict:
        """清洗薪资数据"""
        salary_min = job.get('salary_min', 0)
        salary_max = job.get('salary_max', 0)
        salary_avg = job.get('salary_avg', 0)

        # 异常值处理
        if salary_min <= 0 or salary_max <= 0:
            salary_min = salary_max = salary_avg = 0
        if salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min

        # 极端值处理（月薪超过10万视为异常）
        if salary_max > 100000:
            logger.debug(f"异常高薪: {job.get('title')} {salary_max}")
        
        # 计算真实平均值（如果已有salary_avg且>0则保留，否则重新计算）
        if salary_avg <= 0 and salary_min > 0 and salary_max > 0:
            salary_avg = (salary_min + salary_max) / 2
        job['salary_min'] = salary_min
        job['salary_max'] = salary_max
        job['salary_avg'] = round(salary_avg)
        return job

    @staticmethod
    def normalize_city(job: Dict) -> Dict:
        """标准化城市名称"""
        city = job.get('city', '').strip()
        # 去除区级信息
        city_map = {
            '北京市': '北京', '上海市': '上海', '广州市': '广州', '深圳市': '深圳',
            '杭州市': '杭州', '成都市': '成都', '南京市': '南京', '武汉市': '武汉',
            '西安市': '西安', '长沙市': '长沙', '苏州市': '苏州', '天津市': '天津',
            '重庆市': '重庆', '合肥市': '合肥', '厦门市': '厦门', '郑州市': '郑州',
            '济南市': '济南', '青岛市': '青岛', '大连市': '大连', '福州市': '福州',
        }
        job['city'] = city_map.get(city, city)
        return job

    @staticmethod
    def normalize_experience(job: Dict) -> Dict:
        """标准化经验要求"""
        exp = job.get('experience', '').strip()
        exp_map = {
            '应届生': '应届生', '应届毕业生': '应届生', '在校生': '应届生',
            '1年以内': '应届生', '1年以下': '应届生',
            '1-3年': '1-3年', '1-3年经验': '1-3年',
            '3-5年': '3-5年', '3-5年经验': '3-5年',
            '5-10年': '5-10年', '5-10年经验': '5-10年',
            '10年以上': '10年以上',
            '经验不限': '不限', '不限': '不限',
        }
        job['experience'] = exp_map.get(exp, exp if exp else '不限')
        return job

    @staticmethod
    def normalize_education(job: Dict) -> Dict:
        """标准化学历要求"""
        edu = job.get('education', '').strip()
        edu_map = {
            '大专': '大专', '本科': '本科', '硕士': '硕士',
            '博士': '博士', '学历不限': '不限', '不限': '不限',
            '高中': '其他', '中专': '其他', '中技': '其他',
        }
        job['education'] = edu_map.get(edu, edu if edu else '不限')
        return job

    @staticmethod
    def normalize_company_size(job: Dict) -> Dict:
        """标准化公司规模"""
        import re
        size = job.get('company_size', '').strip()
        # 合法的公司规模必须包含"数字+人"的模式
        # 例如："20人以下"、"100-299人"、"少于20人"、"10000人以上"
        # 排除"人力资源"、"人工智能"等行业词
        if size and re.search(r'\d+.*人', size):
            job['company_size'] = size
        else:
            job['company_size'] = ''  # 非法值置空
        return job

    @staticmethod
    def clean_tags(job: Dict) -> Dict:
        """清洗技术标签，过滤非技术栈词"""
        NON_TECH_TAGS = {
            # 学历
            '本科', '硕士', '博士', '大专', '高中', '中专', '学历不限', '不限', '其他',
            # 经验
            '无经验', '在校生', '应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上',
            # 福利/招聘词
            '10k以上', '15k以上', '20k以上', '五险一金', '五险', '六险一金',
            '双休', '弹性工作', '年终奖', '股票期权', '带薪年假', '全额社保',
            '全国可安排', '全国', '线上面试', '全程线上面试',
            '24届', '25届', '26届', '无经验可投', '接受断档',
            '考研失利', '考公失败', '接受小白',
            # 职位描述片段
            '软件开发', '后端开发', '前端开发', '全栈开发', '算法开发', '测试',
            'Web开发', '嵌入式开发', '图形图像处理', 'Linux开发', 'QT开发',
            '模块开发与调试', '团队协作', '软件开发与测试',
        }
        # 过滤规则：长度超过20字符很可能是描述片段
        tags = job.get('tags', [])
        # "C语言"是从职位标题"C/C++/..."错误解析出来的碎片
        # 判断依据：职位标题中包含 C/C++/GO/JS 等多语言关键词
        title = job.get('title', '')
        title_lower = title.lower()
        has_multi_lang_in_title = any(x in title_lower for x in ['c/c++', 'c++', 'java/c', 'python/c', 'go/', 'js/'])

        role = job.get('role', '').lower()
        # 过滤掉与职位角色同名的标签（标题被解析成标签的碎片）
        # 例如：Java岗位的标签里有"Java"，Python岗位的标签里有"Python"
        role_tag = role.lower() if role else ''
        if role_tag == 'java':
            exclude_role_lang = {'java', 'JAVA', 'Java'}
        elif role_tag == 'python':
            exclude_role_lang = {'python', 'Python', 'PYTHON'}
        else:
            exclude_role_lang = set()

        job['tags'] = [t for t in tags
                      if len(t) <= 20
                      and t not in NON_TECH_TAGS
                      and t not in exclude_role_lang
                      and not any(x in t for x in [
                          '以上', '以下', '可投', '全程', '可安排', '无经验',
                          '应届', '在校', '考研', '考公', '断档', '小白',
                          '软件开发', '后端开发', '前端开发', '全栈', '算法',
                          'Web开发', '嵌入式', '线上面试', '五险', '六险',
                          '年终', '年薪', '双休', '带薪', '全国', '团队',
                          '模块', '调试', 'QT', 'GIS', 'MFC',
                      ])
                      # 如果职位标题含有多语言格式，"C语言"是标题碎片，过滤掉
                      and not (t == 'C语言' and has_multi_lang_in_title)]
        return job

    def clean(self, job: Dict) -> Optional[Dict]:
        """完整清洗单条数据"""
        try:
            job = self.clean_salary(job)
            job = self.normalize_city(job)
            job = self.normalize_experience(job)
            job = self.normalize_education(job)
            job = self.normalize_company_size(job)
            job = self.clean_tags(job)
            return job
        except Exception as e:
            logger.debug(f"数据清洗失败: {e}")
            return None


def load_and_merge_data(raw_dir: str, role: str) -> List[Dict]:
    """加载并合并某个角色的所有数据源"""
    all_jobs = []
    
    for filename in os.listdir(raw_dir):
        if role.lower() in filename.lower() and filename.endswith('.json'):
            filepath = os.path.join(raw_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            all_jobs.extend(jobs)
            logger.info(f"加载 {filename}: {len(jobs)} 条")
    
    # 去重
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get('title', ''), job.get('company', ''), job.get('publish_date', ''))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    logger.info(f"{role} 去重后: {len(unique_jobs)} 条")
    return unique_jobs


def clean_and_save(raw_dir: str, processed_dir: str):
    """清洗数据并保存"""
    os.makedirs(processed_dir, exist_ok=True)
    cleaner = DataCleaner()
    
    for role in ['java', 'python']:
        jobs = load_and_merge_data(raw_dir, role)
        
        cleaned = []
        for job in jobs:
            result = cleaner.clean(job)
            if result:
                cleaned.append(result)
        
        output_path = os.path.join(processed_dir, f'{role}_jobs_cleaned.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        
        logger.info(f"{role} 清洗完成: {len(cleaned)} 条 -> {output_path}")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    clean_and_save(raw_dir, processed_dir)
