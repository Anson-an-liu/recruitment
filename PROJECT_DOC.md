# Java vs Python 招聘数据分析项目 — 详细说明文档

> 项目路径：`D:\recruitment1`
> 最后更新：2026-06-21

---

## 一、项目总体概述

本项目对比 **Java 和 Python 程序员**的招聘市场数据，包含 3 个阶段：

```
数据采集 (Scraper) → 数据清洗与分析 (Analysis) → Web 可视化看板 (Backend + Frontend)
```

覆盖 6 个城市（北京、上海、广州、深圳、成都、武汉），数据来源为智联招聘。

---

## 二、完整目录结构

```
D:\recruitment1\
├── scraper/                          # 爬虫模块
│   ├── __init__.py                   # Python 包标记
│   ├── base_scraper.py               # 爬虫基类（requests 方式）
│   ├── job51_scraper.py              # 51job 爬虫（继承 base_scraper）
│   ├── boss_scraper.py               # BOSS直聘爬虫（继承 base_scraper）
│   ├── zhaopin_scraper.py            # 智联招聘 Selenium 爬虫（主力爬虫）
│   ├── mock_data.py                  # 模拟数据生成器
│   └── run_scraper.py                # 爬虫统一入口/编排器
├── analysis/                         # 数据分析模块
│   ├── __init__.py                   # Python 包标记
│   ├── data_cleaner.py               # 数据清洗与预处理
│   └── analysis.py                   # 多维度分析引擎
├── backend/                          # Web 后端
│   ├── __init__.py                   # Python 包标记
│   └── app.py                        # Flask API 服务（端口 5001）
├── frontend/                         # 前端可视化
│   ├── index.html                    # 主页面结构
│   ├── css/
│   │   └── style.css                 # 全局样式（507 行）
│   └── js/
│       ├── echarts.min.js            # ECharts 5.5.0 本地库
│       └── dashboard.js              # 图表渲染逻辑（424 行）
├── data/
│   ├── raw/                          # 原始爬取数据
│   │   ├── java_jobs_zhaopin.json    # Java 岗位数据（301 条，231KB）
│   │   └── python_jobs_zhaopin.json  # Python 岗位数据（285 条，247KB）
│   └── processed/                    # 清洗和分析结果
│       ├── java_jobs_cleaned.json    # 清洗后 Java 数据（205KB）
│       ├── python_jobs_cleaned.json  # 清洗后 Python 数据（196KB）
│       └── analysis_result.json      # 最终分析结果（4.2KB）
├── venv/                             # Python 虚拟环境（Windows Python 3.13 创建）
├── requirements.txt                  # 项目依赖清单
├── HOW_TO_RUN.md                     # 运行指南
├── PROGRESS.md                       # 项目进度文档
└── README.md                         # 项目简介
```

---

## 三、功能与代码对应关系（核心部分）

### 3.1 数据采集功能

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| 爬虫基类（UA池、重试机制） | `scraper/base_scraper.py` | `BaseScraper` 类（第29行起） | 6个UA轮换，3次指数退避重试 |
| 智联招聘页面搜索 | `scraper/zhaopin_scraper.py` | `ZhaopinSeleniumScraper.search()`（第88-162行） | Selenium 驱动浏览器，逐页爬取 |
| Chrome 反反爬配置 | `scraper/zhaopin_scraper.py` | `_init_driver()`（第52-81行） | 隐藏 webdriver 标记、注入 navigator 属性覆盖 |
| 职位列表解析 | `scraper/zhaopin_scraper.py` | `_parse_job_list()`（第164-197行） | 3套 CSS 选择器策略，优先→备用→兜底 |
| 单条职位数据提取 | `scraper/zhaopin_scraper.py` | `_parse_single_job()`（第199-307行） | 每字段独立 try-except，提取标题/薪资/标签/城市/经验/学历/公司/规模 |
| 薪资文本智能解析 | `scraper/zhaopin_scraper.py` | `_parse_salary()`（第309-364行） | 支持 "10K-15K"、"8000-15000元"、"1.2-1.5万"、"面议" 等格式 |
| 多城市批量采集 | `scraper/zhaopin_scraper.py` | `scrape_multiple_cities()`（第401-433行） | 20个城市代码映射，每城市间随机延迟 |
| 爬虫统一编排 | `scraper/run_scraper.py` | `main()`（第145-261行） | 支持 --mode zhaopin/mock/real/all，数据不足时自动补充模拟数据 |
| 模拟数据生成 | `scraper/mock_data.py` | `generate_dataset()` | 多因子薪资模型（角色/经验/城市/学历），200+200条 |
| 51job 爬虫 | `scraper/job51_scraper.py` | `Job51Scraper` 类 | 从页面 `window.__SEARCH_RESULT__` JSON 提取数据 |
| BOSS直聘爬虫 | `scraper/boss_scraper.py` | `BossScraper` 类 | 调用 wapi API 接口获取数据 |

### 3.2 数据清洗功能

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| 薪资异常值清洗 | `analysis/data_cleaner.py` | `DataCleaner.clean_salary()`（第16-39行） | ≤0 标记为面议，min>max 交换，>10万/月 标记异常，重新计算平均值 |
| 城市名称标准化 | `analysis/data_cleaner.py` | `DataCleaner.normalize_city()`（第41-54行） | "北京市"→"北京"等 20 个城市映射，去除区级信息 |
| 经验要求标准化 | `analysis/data_cleaner.py` | `DataCleaner.normalize_experience()`（第56-70行） | "应届毕业生"/"在校生"/"1年以内"→"应届生"，"1-3年经验"→"1-3年" |
| 学历要求标准化 | `analysis/data_cleaner.py` | `DataCleaner.normalize_education()`（第72-82行） | "学历不限"→"不限"，"高中"/"中专"→"其他" |
| 单条数据完整清洗 | `analysis/data_cleaner.py` | `DataCleaner.clean()`（第84-94行） | 串联以上4步，任何一步异常则丢弃该条数据 |
| 多源数据加载与去重 | `analysis/data_cleaner.py` | `load_and_merge_data()`（第97-119行） | 按(标题,公司,发布日期)三元组去重合并 |
| 清洗流水线执行 | `analysis/data_cleaner.py` | `clean_and_save()`（第122-140行） | 加载→清洗→保存为 `*_jobs_cleaned.json` |

### 3.3 数据分析功能

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| 数据加载 | `analysis/analysis.py` | `_load_data()`（第30-43行） | 从 processed 目录加载 Java 和 Python 清洗数据 |
| 总体概览统计 | `analysis/analysis.py` | `get_summary()`（第45-65行） | 岗位总数、各角色数量、平均薪资、最高薪资、薪资差异 |
| 薪资区间分布 | `analysis/analysis.py` | `salary_distribution()`（第67-86行） | 8档区间（5K以下→40K以上），统计每档 Java/Python 岗位数 |
| 城市岗位分布 | `analysis/analysis.py` | `city_distribution()`（第88-102行） | 统计所有城市→按总数排序→取 Top10 |
| 各城市薪资对比 | `analysis/analysis.py` | `city_salary_comparison()`（第104-130行） | 仅纳入两角色都有≥1条数据的城市，按 Java 薪资降序取 Top12 |
| 经验要求分布 | `analysis/analysis.py` | `experience_analysis()`（第132-143行） | 7档经验级别（应届生→10年以上→不限） |
| 不同经验薪资趋势 | `analysis/analysis.py` | `experience_salary()`（第145-158行） | 仅统计 salary_avg>0 的数据，计算各经验级别平均薪资 |
| 学历要求分布 | `analysis/analysis.py` | `education_analysis()`（第160-171行） | 5档学历（大专→博士→不限） |
| 不同学历薪资雷达图数据 | `analysis/analysis.py` | `education_salary()`（第173-186行） | 仅含大专/本科/硕士（排除博士和不限） |
| 热门技术标签 | `analysis/analysis.py` | `top_tags()`（第188-208行） | 对每条数据的 tags 字段所有标签计数，取各角色 Top15 |
| 公司规模分布 | `analysis/analysis.py` | `company_size_analysis()`（第210-228行） | 7档规模（20人以下→10000人以上），动态追加实际存在的其他标签 |
| 全维度聚合分析 | `analysis/analysis.py` | `full_analysis()`（第230-243行） | 一次调用返回包含以上所有维度的大字典 |
| 平均值计算辅助 | `analysis/analysis.py` | `_avg()`/`_avg_list()`（第245-253行） | 排除零值计算平均值 |
| 完整流程执行 | `analysis/analysis.py` | `main()`（第256-288行） | 清洗→分析→保存 `analysis_result.json`→打印摘要 |

### 3.4 Flask 后端 API

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| Flask 应用初始化 | `backend/app.py` | 第15-17行 | static_folder 指向 frontend，启用 CORS |
| MIME 类型修复（关键修复） | `backend/app.py` | `MIME_TYPES` 字典（第20-31行） + `send_static_file()`（第34-43行） | 修复 Windows 下 CSS 被标为 `application/x-css`、JS 被标为 `text/plain` 的浏览器拒绝问题 |
| CSS/JS 专用路由 | `backend/app.py` | `/css/<path>`（第56-59行）、`/js/<path>`（第62-65行） | 通过专用路由确保正确 Content-Type |
| 主页路由 | `backend/app.py` | `/` → `index()`（第50-53行） | 返回 `frontend/index.html` |
| 概览数据 API | `backend/app.py` | `/api/summary`（第68-71行） | 调用 `analyzer.get_summary()` |
| 薪资分布 API | `backend/app.py` | `/api/salary_distribution`（第74-77行） | 调用 `analyzer.salary_distribution()` |
| 城市分布 API | `backend/app.py` | `/api/city_distribution`（第80-83行） | 调用 `analyzer.city_distribution()` |
| 城市薪资 API | `backend/app.py` | `/api/city_salary`（第86-89行） | 调用 `analyzer.city_salary_comparison()` |
| 经验分布 API | `backend/app.py` | `/api/experience`（第92-95行） | 调用 `analyzer.experience_analysis()` |
| 经验薪资 API | `backend/app.py` | `/api/experience_salary`（第98-101行） | 调用 `analyzer.experience_salary()` |
| 学历分布 API | `backend/app.py` | `/api/education`（第104-107行） | 调用 `analyzer.education_analysis()` |
| 学历薪资 API | `backend/app.py` | `/api/education_salary`（第110-113行） | 调用 `analyzer.education_salary()` |
| 技术标签 API | `backend/app.py` | `/api/tags`（第116-119行） | 调用 `analyzer.top_tags()` |
| 公司规模 API | `backend/app.py` | `/api/company_size`（第122-125行） | 调用 `analyzer.company_size_analysis()` |
| 全分析 API | `backend/app.py` | `/api/full_analysis`（第128-131行） | 调用 `analyzer.full_analysis()` |
| 原始数据 API | `backend/app.py` | `/api/raw_data`（第134-145行） | 直接读取 `*_jobs_cleaned.json` 合并返回 |
| 服务启动入口 | `backend/app.py` | `__main__`（第148-157行） | 默认端口 5001，监听 0.0.0.0 |

### 3.5 前端页面结构

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| 页面骨架 | `frontend/index.html` | 全文（216行） | 语义化 HTML5：header → overview → 7个 chart section → footer |
| 概览卡片（岗位总数） | `frontend/index.html` | 第48-58行 | `<div class="overview-card total">`，SVG 图标 + 数值 + 副标题 |
| 概览卡片（Java岗位） | `frontend/index.html` | 第60-69行 | `<div class="overview-card java">`，显示数量+平均薪资 |
| 概览卡片（Python岗位） | `frontend/index.html` | 第70-82行 | `<div class="overview-card python">`，显示数量+平均薪资 |
| 概览卡片（薪资差异） | `frontend/index.html` | 第83-93行 | `<div class="overview-card salary">`，显示差异值+方向 |
| 薪资区间分布图容器 | `frontend/index.html` | 第97-106行 | `#chart-salary-dist` |
| 城市岗位分布图容器 | `frontend/index.html` | 第109-118行 | `#chart-city-dist` |
| 城市薪资对比图容器 | `frontend/index.html` | 第119-126行 | `#chart-city-salary` |
| 经验分布图容器 | `frontend/index.html` | 第129-136行 | `#chart-experience` |
| 经验薪资趋势图容器 | `frontend/index.html` | 第137-144行 | `#chart-experience-salary` |
| 学历分布图容器 | `frontend/index.html` | 第149-156行 | `#chart-education` |
| 学历薪资雷达图容器 | `frontend/index.html` | 第157-164行 | `#chart-education-salary` |
| Java 技术标签图容器 | `frontend/index.html` | 第170-173行 | `#chart-tags-java` |
| Python 技术标签图容器 | `frontend/index.html` | 第174-177行 | `#chart-tags-python` |
| 公司规模分布图容器 | `frontend/index.html` | 第181-188行 | `#chart-company-size` |
| JS 加载 | `frontend/index.html` | 第205-206行 | `echarts.min.js` + `dashboard.js` |
| 无 JS 提示 | `frontend/index.html` | 第208-212行 | `<noscript>` 兜底提示 |

### 3.6 前端 CSS 样式

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| CSS 变量系统（设计令牌） | `frontend/css/style.css` | `:root`（第10-64行） | 颜色/阴影/圆角/字体/间距/过渡全套变量 |
| 全局重置与基础 | `frontend/css/style.css` | 第66-81行 | 系统字体栈（PingFang SC、Microsoft YaHei），抗锯齿 |
| 顶部导航栏 | `frontend/css/style.css` | `.header`（第83-148行） | 深色渐变背景(#0F172A→#1E293B)，sticky 定位，logo+badge |
| 概览卡片网格 | `frontend/css/style.css` | `.overview`（第157-250行） | 4列网格，4种色彩主题(total蓝/java红/python绿/salary琥珀)，hover 上浮动效 |
| 图表两列网格 | `frontend/css/style.css` | `.chart-grid.cols-2`（第253-265行） | 2列并列布局 |
| 图表卡片 | `frontend/css/style.css` | `.chart-card`（第267-319行） | 白色卡片+阴影，header 带色点标识，hover 阴影增强 |
| 技术标签区 | `frontend/css/style.css` | `.tag-section`（第321-351行） | 两列网格，独立标签卡片 |
| 页脚 | `frontend/css/style.css` | `.footer`（第353-376行） | 居中对齐，分隔点 |
| 响应式适配 | `frontend/css/style.css` | `@media`（第379-431行） | 1200px→2列，768px→1列，480px→卡片调整 |
| 滚动条美化 | `frontend/css/style.css` | 第434-447行 | 自定义 webkit 滚动条 |
| 加载动画 | `frontend/css/style.css` | `.loading`（第449-471行） | spinner 旋转动画 |

### 3.7 前端 JS 图表渲染

| 功能 | 实现文件 | 代码位置 | 说明 |
|------|----------|----------|------|
| 设计配色常量 | `frontend/js/dashboard.js` | `COLORS`（第11-24行） | java红#E74C3C, python绿#10B981, primary蓝#1E40AF, accent琥珀#D97706 |
| API 异步请求 | `frontend/js/dashboard.js` | `fetchAPI()`（第28-37行） | fetch + 错误处理 |
| 薪资格式化 | `frontend/js/dashboard.js` | `formatSalary()`（第39-43行） | ≥10000显示K，<10000显示完整数字 |
| ECharts 实例管理 | `frontend/js/dashboard.js` | `initChart()`（第57-72行） | 销毁旧实例防重复，失败时显示提示 |
| 窗口自适应 | `frontend/js/dashboard.js` | 第111-113行 | resize 事件触发所有图表自适应 |
| 概览卡片渲染 | `frontend/js/dashboard.js` | `renderOverview()`（第117-138行） | 调用 `/api/summary`，填充4个卡片数值 |
| 薪资分布图渲染 | `frontend/js/dashboard.js` | `renderSalaryDistribution()`（第142-161行） | 分组柱状图，8档区间 |
| 城市分布图渲染 | `frontend/js/dashboard.js` | `renderCityDistribution()`（第165-184行） | 分组柱状图，>8城市时标签旋转30° |
| 城市薪资对比图渲染 | `frontend/js/dashboard.js` | `renderCitySalary()`（第188-207行） | 分组柱状图，Y轴K单位 |
| 经验分布图渲染 | `frontend/js/dashboard.js` | `renderExperience()`（第211-230行） | 分组柱状图 |
| 经验薪资趋势图渲染 | `frontend/js/dashboard.js` | `renderExperienceSalary()`（第234-253行） | 折线图+面积渐变区域 |
| 学历分布图渲染 | `frontend/js/dashboard.js` | `renderEducation()`（第257-276行） | 分组柱状图 |
| 学历薪资雷达图渲染 | `frontend/js/dashboard.js` | `renderEducationSalary()`（第280-313行） | 雷达图，动态计算 max 值 |
| Java 技术标签图渲染 | `frontend/js/dashboard.js` | `renderTags()`（第317-356行） | 横向柱状图，渐变色，Top15 |
| Python 技术标签图渲染 | `frontend/js/dashboard.js` | `renderTags()`（第317-356行） | 同上，独立容器 |
| 公司规模分布图渲染 | `frontend/js/dashboard.js` | `renderCompanySize()`（第360-379行） | 分组柱状图 |
| 看板初始化入口 | `frontend/js/dashboard.js` | `initDashboard()`（第383-422行） | 检查 echarts→渲染概览→Promise.allSettled 并发渲染9图表 |
| 自动启动 | `frontend/js/dashboard.js` | 第424行 | `DOMContentLoaded` 事件触发 `initDashboard()` |

---

## 四、数据流与模块连接图

```
┌──────────────────── 数据采集层 (scraper/) ────────────────────┐
│                                                                │
│  base_scraper.py (基类: UA池/重试)                             │
│      │                                                         │
│  ├─── job51_scraper.py (51job爬虫)                             │
│  ├─── boss_scraper.py (BOSS直聘爬虫)                           │
│  └─── zhaopin_scraper.py (智联Selenium爬虫 ★主力)              │
│          ├── _init_driver()      → Chrome反反爬配置              │
│          ├── search()            → 逐页搜索+解析                 │
│          ├── _parse_single_job() → 8字段独立提取                  │
│          ├── _parse_salary()     → 多格式薪资文本解析             │
│          └── scrape_multiple_cities() → 6城市批量采集             │
│                                                                │
│  run_scraper.py (编排器，统一CLI入口)                            │
│      └── --mode zhaopin/mock/real/all                          │
│                                                                │
│  mock_data.py (模拟数据生成器，数据不足时自动补充)                │
│                                                                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
                 data/raw/*.json (原始爬取数据)
                             │
┌──────────────────── 数据处理层 (analysis/) ───────────────────┐
│                                                                │
│  data_cleaner.py                                               │
│      ├── DataCleaner.clean_salary()      → 薪资异常值修复       │
│      ├── DataCleaner.normalize_city()    → 城名标准化           │
│      ├── DataCleaner.normalize_experience() → 经验标准化         │
│      ├── DataCleaner.normalize_education()  → 学历标准化        │
│      ├── DataCleaner.clean()             → 单条完整清洗          │
│      ├── load_and_merge_data()           → 多源加载+去重        │
│      └── clean_and_save()                → 清洗流水线           │
│                                                                │
│          ↓ 输出: *_jobs_cleaned.json                            │
│                                                                │
│  analysis.py                                                   │
│      ├── RecruitmentAnalyzer.__init__() → 加载清洗数据           │
│      ├── get_summary()               → 总体概览                 │
│      ├── salary_distribution()       → 薪资区间分布              │
│      ├── city_distribution()         → 城市岗位分布              │
│      ├── city_salary_comparison()    → 城市薪资对比              │
│      ├── experience_analysis()       → 经验要求分布              │
│      ├── experience_salary()         → 经验薪资趋势              │
│      ├── education_analysis()        → 学历要求分布              │
│      ├── education_salary()          → 学历薪资雷达              │
│      ├── top_tags()                  → 技术标签Top15             │
│      ├── company_size_analysis()     → 公司规模分布              │
│      ├── full_analysis()             → 全维度聚合                │
│      └── main()                      → 清洗→分析→保存结果        │
│                                                                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
                 data/processed/analysis_result.json
                             │
┌──────────────────── 展示层 ───────────────────────────────────┐
│                                                                │
│  backend/app.py (Flask API: 12个接口, 端口5001)                │
│      ├── send_static_file() → MIME类型修复 ★关键修复            │
│      ├── /css/ /js/ 路由    → 正确Content-Type                  │
│      ├── /api/summary       → 概览数据                          │
│      ├── /api/salary_distribution → 薪资分布                    │
│      ├── /api/city_distribution   → 城市分布                    │
│      ├── /api/city_salary         → 城市薪资                    │
│      ├── /api/experience          → 经验分布                    │
│      ├── /api/experience_salary   → 经验薪资                    │
│      ├── /api/education           → 学历分布                    │
│      ├── /api/education_salary    → 学历薪资                    │
│      ├── /api/tags                → 技术标签                    │
│      ├── /api/company_size        → 公司规模                    │
│      ├── /api/full_analysis       → 全分析数据                  │
│      └── /api/raw_data            → 清洗后原始数据              │
│                                                                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌──────────────────── 前端可视化 (frontend/) ───────────────────┐
│                                                                │
│  index.html (页面骨架: 4卡片+9图表容器)                          │
│                                                                │
│  css/style.css (Data-Dense Dashboard 设计系统)                  │
│      ├── CSS变量令牌   → 统一颜色/阴影/圆角/间距                 │
│      ├── 系统字体栈    → PingFang SC / Microsoft YaHei          │
│      ├── 概览卡片      → 4色主题+hover动效                      │
│      ├── 响应式适配    → 1200/768/480三档                       │
│                                                                │
│  js/dashboard.js (ECharts图表渲染)                              │
│      ├── renderOverview()           → 4概览卡片数值填充           │
│      ├── renderSalaryDistribution() → 薪资区间分组柱状图         │
│      ├── renderCityDistribution()   → 城市岗位分组柱状图         │
│      ├── renderCitySalary()         → 城市薪资分组柱状图         │
│      ├── renderExperience()         → 经验分布分组柱状图         │
│      ├── renderExperienceSalary()   → 经验薪资折线+面积图        │
│      ├── renderEducation()          → 学历分布分组柱状图         │
│      ├── renderEducationSalary()    → 学历薪资雷达图             │
│      ├── renderTags()               → 技术标签横向柱状图(×2)    │
│      ├── renderCompanySize()        → 公司规模分组柱状图         │
│      └── initDashboard()            → DOMContentLoaded入口      │
│                                                                │
│  js/echarts.min.js (ECharts 5.5.0 本地库)                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 五、已修复的关键 Bug 记录

| Bug | 根因 | 修复位置 | 修复方式 |
|-----|------|----------|----------|
| 页面只有裸SVG图标无样式无数据 | Flask 将 CSS 标为 `application/x-css`、JS 标为 `text/plain`，浏览器拒绝加载/执行 | `backend/app.py` 第20-65行 | 自定义 `send_static_file()` + MIME_TYPES 字典 + `/css/` `/js/` 专用路由 |
| CSS 全部失效 | `@import url('fonts.googleapis.com/...')` 在中国被 GFW 阻断 | `frontend/css/style.css` 第1行 | 移除 Google Fonts import |
| 字体不可用 | Fira Sans/Fira Code 无本地 fallback | `frontend/css/style.css` `:root` 字体变量 | 替换为系统字体栈（PingFang SC, Microsoft YaHei 等） |
| 薪资平均值错误 | `salary_avg = salary_max`（只取最大值） | `analysis/data_cleaner.py` `clean_salary()` | 改为 `salary_avg = (salary_min + salary_max) / 2` |
| ChromeDriver 下载锁文件冲突 | `FileExistsError: .wdm-lock-chromedriver-win64` | `C:\Users\29875\.wdm\` | 手动删除 lock 文件 |
| venv 跨平台不兼容 | WSL Linux Python 创建的 venv 在 Windows 无法运行 | `D:\recruitment1\venv\` | 用 Windows Python 重建 venv |
| 爬虫0条结果 | CSS 选择器不匹配智联实际页面 | `zhaopin_scraper.py` `_parse_job_list()` | 改为 `div.joblist-box__item` 等真实选择器 |

---

## 六、启动方式

### 方式一：三行命令（推荐）

```bash
cd /d D:\recruitment1
.\venv\Scripts\activate
python -m backend.app
```

访问 **http://localhost:5001**

### 方式二：一行命令

```bash
cd /d D:\recruitment1 && venv\Scripts\python.exe -m backend.app
```

### 重新爬取数据后的完整流程

```bash
# 1. 爬取数据
cd D:\recruitment1
.\venv\Scripts\activate
python -m scraper.zhaopin_scraper --keywords java python --multi-city --cities 北京 上海 广州 深圳 成都 武汉

# 2. 清洗和分析
python -m analysis.analysis

# 3. 启动看板
python -m backend.app
```

---

## 七、API 接口一览

| 接口路径 | 返回内容 | 对应分析方法 |
|----------|----------|-------------|
| `/api/summary` | 岗位总数、平均薪资、薪资差异 | `analyzer.get_summary()` |
| `/api/salary_distribution` | 8档薪资区间分布 | `analyzer.salary_distribution()` |
| `/api/city_distribution` | Top10城市岗位分布 | `analyzer.city_distribution()` |
| `/api/city_salary` | Top12城市平均薪资 | `analyzer.city_salary_comparison()` |
| `/api/experience` | 7档经验要求分布 | `analyzer.experience_analysis()` |
| `/api/experience_salary` | 各经验级别平均薪资 | `analyzer.experience_salary()` |
| `/api/education` | 5档学历要求分布 | `analyzer.education_analysis()` |
| `/api/education_salary` | 大专/本科/硕士平均薪资 | `analyzer.education_salary()` |
| `/api/tags` | Java/Python 各Top15技术标签 | `analyzer.top_tags()` |
| `/api/company_size` | 7档公司规模分布 | `analyzer.company_size_analysis()` |
| `/api/full_analysis` | 包含所有维度的聚合结果 | `analyzer.full_analysis()` |
| `/api/raw_data` | 清洗后的完整职位列表 | 直接读取 JSON 文件 |

---

## 八、当前数据状态

| 数据项 | Java | Python | 合计 |
|--------|------|--------|------|
| 原始数据条数 | 301 | 285 | 586 |
| 覆盖城市 | 广州、上海、深圳、北京、成都、武汉 | 同上 | 6城市 |
| 平均月薪 | ¥15,898 | ¥15,856 | — |
| 最高月薪 | ¥50,000 | ¥50,000 | — |
| 薪资差异 | — | — | Python 仅高出 ¥42（基本持平） |

---

## 九、项目依赖

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| flask | ≥3.0.0 | Web API 后端框架 |
| flask-cors | ≥4.0.0 | 跨域请求支持 |
| requests | ≥2.31.0 | HTTP 请求（基类爬虫） |
| beautifulsoup4 | ≥4.12.0 | HTML 解析（基类爬虫） |
| lxml | ≥5.0.0 | XML/HTML 解析器 |
| selenium | ≥4.20.0 | 浏览器自动化（智联爬虫） |
| webdriver-manager | ≥4.0.0 | ChromeDriver 自动下载管理 |
