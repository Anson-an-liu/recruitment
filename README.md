# 招聘信息数据分析项目

## 📊 Java vs Python 程序员招聘数据对比分析

一个完整的招聘数据爬取、分析和可视化项目，对比 Java 和 Python 程序员的岗位需求。

### 项目结构

```
recruitment1/
├── scraper/                # 数据爬取模块
│   ├── base_scraper.py     # 爬虫基类（UA池、重试、延迟）
│   ├── job51_scraper.py    # 51job爬虫
│   ├── boss_scraper.py     # BOSS直聘爬虫
│   ├── mock_data.py        # 模拟数据生成器
│   └── run_scraper.py      # 爬虫入口
├── analysis/               # 数据分析模块
│   ├── data_cleaner.py     # 数据清洗
│   └── analysis.py         # 多维度分析
├── backend/                # Flask后端
│   └── app.py              # API服务
├── frontend/               # 前端可视化
│   ├── index.html          # 主页面
│   ├── css/style.css       # 样式
│   └── js/dashboard.js     # ECharts图表
├── data/                   # 数据目录
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后的数据
└── requirements.txt        # Python依赖
```

### 快速开始

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 生成数据
```bash
# 方式一：生成模拟数据（推荐，数据质量稳定）
python -m scraper.mock_data

# 方式二：运行完整爬虫（含真实爬取+模拟数据补充）
python -m scraper.run_scraper --mode all

# 方式三：仅真实爬取
python -m scraper.run_scraper --mode real --keywords Java Python --city 北京 --pages 3
```

#### 3. 执行数据分析
```bash
python -m analysis.analysis
```

#### 4. 启动Web服务
```bash
python -m backend.app
```

#### 5. 打开浏览器
访问 http://localhost:5000

### 分析维度

| 维度 | 说明 |
|------|------|
| 薪资分布 | 各薪资区间的岗位数量对比 |
| 城市分布 | Top10城市的岗位数量和平均薪资 |
| 经验要求 | 不同经验级别的需求分布和薪资趋势 |
| 学历要求 | 学历要求和对应薪资水平 |
| 技术标签 | 热门技术栈词频统计 |
| 公司规模 | 不同规模公司的招聘偏好 |

### API接口

| 接口 | 说明 |
|------|------|
| GET /api/summary | 总体概览 |
| GET /api/salary_distribution | 薪资分布 |
| GET /api/city_distribution | 城市分布 |
| GET /api/city_salary | 城市薪资对比 |
| GET /api/experience | 经验要求 |
| GET /api/experience_salary | 经验薪资趋势 |
| GET /api/education | 学历要求 |
| GET /api/education_salary | 学历薪资对比 |
| GET /api/tags | 技术标签 |
| GET /api/company_size | 公司规模 |
| GET /api/full_analysis | 完整分析结果 |

### 技术栈

- **后端**: Python + Flask + Flask-CORS
- **前端**: HTML5 + CSS3 + ECharts 5
- **爬虫**: requests + BeautifulSoup4
- **分析**: 自定义分析引擎
