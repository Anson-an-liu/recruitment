"""
模拟招聘数据生成器
当真实爬取遇到反爬限制时，生成高质量的模拟数据用于项目演示和分析
"""
import random
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict


# 城市及权重（模拟招聘分布）
CITIES = {
    '北京': 18, '上海': 16, '深圳': 14, '广州': 10, '杭州': 9,
    '成都': 8, '南京': 6, '武汉': 5, '西安': 4, '长沙': 3,
    '苏州': 3, '天津': 2, '重庆': 2, '合肥': 2, '厦门': 2,
    '郑州': 2, '济南': 2, '青岛': 1, '大连': 1, '福州': 1,
}

# Java相关技术标签
JAVA_TAGS = [
    'Spring Boot', 'Spring Cloud', 'MyBatis', 'Hibernate', '微服务',
    'Dubbo', 'ZooKeeper', 'Kafka', 'RabbitMQ', 'Redis', 'MySQL',
    'Oracle', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'Maven',
    'Nginx', 'Tomcat', 'Elasticsearch', '分布式', '高并发', 'JVM调优',
    '多线程', 'Netty', 'Spring MVC', 'Shiro', 'JPA', 'gRPC'
]

# Python相关技术标签
PYTHON_TAGS = [
    'Django', 'Flask', 'FastAPI', 'Tornado', 'Celery', 'Scrapy',
    'Pandas', 'NumPy', 'TensorFlow', 'PyTorch', 'Scikit-learn',
    'Docker', 'Kubernetes', 'Redis', 'PostgreSQL', 'MongoDB',
    'RabbitMQ', 'Kafka', 'Git', 'Linux', 'Nginx', 'RESTful API',
    'GraphQL', '微服务', '数据分析', '机器学习', 'NLP', 'CV',
    '自然语言处理', '推荐系统'
]

# 公司规模分布
COMPANY_SIZES = ['50-150人', '150-500人', '500-1000人', '1000-5000人', '5000-10000人', '10000人以上']

# 学历要求
EDUCATIONS = ['大专', '本科', '硕士', '不限']

# 经验要求
EXPERIENCES = ['应届生', '1-3年', '3-5年', '5-10年', '10年以上', '不限']

# Java公司名称
JAVA_COMPANIES = [
    '字节跳动', '阿里巴巴', '腾讯', '美团', '京东', '华为', '百度', '网易',
    '滴滴', '快手', '小米', '蚂蚁集团', '携程', '哔哩哔哩', 'Shopee',
    '中兴通讯', '用友网络', '金蝶软件', '神州数码', '浪潮集团', '东软集团',
    '恒生电子', '华宇信息', '中软国际', '软通动力', '博彦科技', '文思海辉',
    '数字政通', '亚信科技', '太极股份', '科大讯飞', '商汤科技'
]

# Python公司名称
PYTHON_COMPANIES = [
    '字节跳动', '腾讯', '阿里巴巴', '百度', '小红书', '商汤科技', '旷视科技',
    '依图科技', '第四范式', '明略科技', '科大讯飞', '网易', '美团', '滴滴',
    '快手', 'B站', '知乎', '汽车之家', '贝壳找房', '作业帮', '猿辅导',
    '好未来', 'VIPKID', '平安科技', '众安保险', '蚂蚁集团', '微众银行',
    '京东数科', '度小满', '快手', '拼多多', 'Soul', '得物'
]


def weighted_choice(choices: Dict[str, float]) -> str:
    """按权重随机选择"""
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_salary(role: str, experience: str, city: str, education: str) -> tuple:
    """
    根据角色、经验、城市、学历生成合理的薪资范围
    返回: (min_salary, max_salary, avg_salary)
    """
    # 基础薪资（月薪，千元）
    if role == 'Java':
        base = {
            '应届生': (6, 10), '1-3年': (10, 18), '3-5年': (18, 30),
            '5-10年': (28, 45), '10年以上': (40, 60), '不限': (10, 25),
        }
    else:  # Python
        base = {
            '应届生': (7, 12), '1-3年': (12, 22), '3-5年': (20, 35),
            '5-10年': (30, 50), '10年以上': (45, 70), '不限': (12, 30),
        }
    
    low, high = base.get(experience, (10, 20))

    # 城市系数
    city_coeff = {
        '北京': 1.2, '上海': 1.15, '深圳': 1.1, '广州': 1.0,
        '杭州': 1.05, '成都': 0.85, '南京': 0.9, '武汉': 0.8,
        '西安': 0.75, '长沙': 0.75,
    }.get(city, 0.8)

    # 学历加成
    edu_bonus = {'硕士': 1.15, '本科': 1.0, '大专': 0.85, '不限': 1.0}.get(education, 1.0)

    # 随机波动
    low = low * city_coeff * edu_bonus * random.uniform(0.9, 1.1)
    high = high * city_coeff * edu_bonus * random.uniform(0.9, 1.1)
    
    # 确保low < high
    if low > high:
        low, high = high, low
    
    avg = (low + high) / 2
    
    # 转换为元
    return round(low * 1000), round(high * 1000), round(avg * 1000)


def generate_description(role: str, tags: List[str]) -> str:
    """生成模拟职位描述"""
    role_desc = {
        'Java': '负责后端服务的设计、开发与维护，参与系统架构设计和技术选型。',
        'Python': '负责数据分析平台/后端服务的开发，参与算法模型的工程化落地。',
    }
    
    tag_descs = {
        'Java': [
            '参与高并发分布式系统的设计与开发',
            '负责核心业务模块的编码实现与性能优化',
            '编写技术文档，参与代码评审',
            '与产品、前端团队紧密协作，推动项目落地',
            '解决生产环境中的技术问题，保障系统稳定性',
        ],
        'Python': [
            '负责数据处理流水线的搭建与优化',
            '参与机器学习模型的训练、评估与部署',
            '编写自动化脚本，提升开发效率',
            '与数据团队协作完成数据分析需求',
            '持续优化系统性能，保障服务可用性',
        ],
    }

    desc = role_desc.get(role, '')
    desc += '\\n'.join(random.sample(tag_descs.get(role, ['']), min(3, len(tag_descs.get(role, [''])))))

    if tags:
        desc += f'\\n\\n技术要求：{", ".join(random.sample(tags, min(6, len(tags))))}'
    
    return desc


def generate_company_name(role: str) -> str:
    """生成公司名称"""
    pool = JAVA_COMPANIES if role == 'Java' else PYTHON_COMPANIES
    # 70%使用知名公司，30%随机命名
    if random.random() < 0.7:
        return random.choice(pool)
    else:
        prefixes = ['创达', '睿智', '星辰', '飞腾', '瀚海', '卓远', '鼎新', '凌云']
        suffixes = ['科技', '信息', '软件', '数据', '互联', '智能']
        return random.choice(prefixes) + random.choice(suffixes) + '有限公司'


def generate_jobs(role: str, count: int = 200) -> List[Dict]:
    """
    生成指定角色的模拟招聘数据
    """
    tags_pool = JAVA_TAGS if role == 'Java' else PYTHON_TAGS
    jobs = []
    
    base_date = datetime.now()
    
    for i in range(count):
        city = weighted_choice(CITIES)
        experience = random.choices(
            EXPERIENCES, 
            weights=[8, 30, 35, 20, 5, 2], 
            k=1
        )[0]
        education = random.choices(
            EDUCATIONS, 
            weights=[15, 65, 15, 5], 
            k=1
        )[0]
        
        salary_min, salary_max, salary_avg = generate_salary(role, experience, city, education)
        
        # 选择技术标签
        num_tags = random.randint(3, 8)
        selected_tags = random.sample(tags_pool, min(num_tags, len(tags_pool)))
        
        # 生成发布日期
        days_ago = random.randint(1, 30)
        publish_date = (base_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        company = generate_company_name(role)
        company_size = random.choice(COMPANY_SIZES)
        
        # 职位名称变体
        title_variants = {
            'Java': [
                f'{role}开发工程师', f'高级{role}开发工程师', f'{role}后端工程师',
                f'{role}架构师', f'{role}技术专家', f'资深{role}开发',
                f'{role}工程师（{city}）', f'{role}研发工程师',
            ],
            'Python': [
                f'{role}开发工程师', f'高级{role}开发工程师', f'{role}后端工程师',
                f'{role}数据分析师', f'{role}算法工程师', f'{role}全栈工程师',
                f'{role}爬虫工程师', f'{role}自动化测试工程师',
            ],
        }
        
        job = {
            'title': random.choice(title_variants.get(role, [f'{role}工程师'])),
            'company': company,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_avg': salary_avg,
            'city': city,
            'experience': experience,
            'education': education,
            'tags': selected_tags,
            'company_type': '互联网/IT',
            'company_size': company_size,
            'description': generate_description(role, selected_tags),
            'source': '模拟数据',
            'role': role,
            'url': '',
            'publish_date': publish_date,
        }
        jobs.append(job)
    
    return jobs


def generate_dataset(output_dir: str = None):
    """生成完整数据集"""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    
    os.makedirs(output_dir, exist_ok=True)
    
    java_jobs = generate_jobs('Java', count=200)
    python_jobs = generate_jobs('Python', count=200)
    
    java_file = os.path.join(output_dir, 'java_jobs_raw.json')
    python_file = os.path.join(output_dir, 'python_jobs_raw.json')
    
    with open(java_file, 'w', encoding='utf-8') as f:
        json.dump(java_jobs, f, ensure_ascii=False, indent=2)
    
    with open(python_file, 'w', encoding='utf-8') as f:
        json.dump(python_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"模拟数据已生成:")
    print(f"  Java岗位: {len(java_jobs)} 条 -> {java_file}")
    print(f"  Python岗位: {len(python_jobs)} 条 -> {python_file}")
    
    return java_jobs, python_jobs


if __name__ == '__main__':
    generate_dataset()
