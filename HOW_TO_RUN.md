# 招聘数据分析项目 - 运行指南

> 项目路径：D:\recruitment1
> 最后更新：2026-06-21

---

## 一、项目结构简述

```
recruitment1/
├── scraper/             # 爬虫模块
│   ├── zhaopin_scraper.py   # 智联招聘爬虫（主力，Selenium浏览器自动化）
│   ├── mock_data.py         # 模拟数据生成（备用）
│   ├── run_scraper.py       # 爬虫统一入口
│   ├── job51_scraper.py     # 前程无忧爬虫（桩代码，暂不可用）
│   └── boss_scraper.py      # BOSS直聘爬虫（桩代码，暂不可用）
│   └── base_scraper.py      # 爬虫基类
├── analysis/            # 数据处理模块
│   ├── data_cleaner.py      # 数据清洗（去重、标准化）
│   └── analysis.py          # 多维度分析（薪资、城市、经验、学历等）
├── backend/             # 后端服务
│   └── app.py               # Flask API（10个接口，端口5001）
├── frontend/            # 前端页面
│   ├── index.html           # 主页面
│   ├── css/style.css        # 样式
│   └── js/dashboard.js      # 图表逻辑（ECharts）
│   └── js/echarts.min.js    # ECharts本地库
├── data/
│   ├── raw/                 # 爬取的原始数据
│   │   ├── java_jobs_zhaopin.json    # Java岗位数据
│   │   ├── python_jobs_zhaopin.json  # Python岗位数据
│   └── processed/           # 清洗和分析后的数据
│       ├── java_jobs_cleaned.json    # 清洗后的Java数据
│       ├── python_jobs_cleaned.json  # 清洗后的Python数据
│       ├── analysis_result.json      # 最终分析结果（前端读取这个）
├── venv/                 # Python虚拟环境（已配置好）
├── requirements.txt      # 依赖列表
└── PROGRESS.md           # 项目进度文档
```

---

## 二、完整运行流程（从零开始）

整个项目有3个阶段：采集 → 分析 → 展示

### 第1步：打开终端，进入项目目录

打开 CMD 或 PowerShell，执行：

```
cd D:\recruitment1
```

### 第2步：激活虚拟环境

```
.\venv\Scripts\activate
```

激活后你会看到终端前面出现 `(venv)` 标记，说明虚拟环境已激活。
退出虚拟环境的命令是 `deactivate`，但运行项目时不要退出。

### 第3步：采集数据（爬虫）

#### 方式A：采集智联招聘真实数据（推荐）

单城市采集（建议先这样测试）：

```
python -m scraper.zhaopin_scraper --keywords Java --city 北京 --pages 2 --no-headless
```

参数说明：
- --keywords：搜索关键词，可以写 Java 或 Python 或两个都写
- --city：城市名，如 北京、上海、深圳
- --pages：爬几页，每页大约20条数据
- --no-headless：显示浏览器窗口，能看到采集过程。去掉这个参数就是无头模式（后台跑，看不到浏览器）

采集Python岗位：

```
python -m scraper.zhaopin_scraper --keywords Python --city 北京 --pages 3 --no-headless
```

多城市批量采集（无头模式，速度更快）：

```
python -m scraper.zhaopin_scraper --keywords Java Python --multi-city --pages 3
```

这会自动采集20个主要城市的Java和Python岗位数据。

#### 方式B：生成模拟数据（备用，如果爬虫不工作）

```
python -m scraper.mock_data
```

这会在 data/raw/ 下生成 java_jobs_raw.json 和 python_jobs_raw.json

#### 方式C：通过统一入口运行

```
python -m scraper.run_scraper --mode zhaopin --keywords Java Python --city 北京 --pages 5
```

---

**常见问题：**

Q: 报错 TimeoutError: Timed out waiting for webdriver-manager lock
A: 删除锁文件：
```
del "C:\Users\29875\.wdm\.wdm-lock-chromedriver-win64"
```
然后重新运行爬虫命令。

Q: 第一次运行很慢（下载ChromeDriver）
A: 正常现象，第一次要下载浏览器驱动（约7分钟），下载完缓存到本地，之后秒启动。

Q: 采集到0条数据
A: 智联招聘可能改了页面结构，需要看调试页面。爬虫会自动保存空结果页面到 data/raw/zhaopin_debug_empty_page*.html

---

### 第4步：运行数据分析

采集完数据后，必须运行分析才能生成看板需要的结果文件：

```
python -m analysis.analysis
```

这会做两件事：
1. 清洗原始数据（去重、标准化字段）→ 生成 data/processed/java_jobs_cleaned.json 和 python_jobs_cleaned.json
2. 多维度分析 → 生成 data/processed/analysis_result.json

analysis_result.json 是前端看板的直接数据来源。

---

### 第5步：启动后端服务

```
python -m backend.app
```

默认端口5001。如果想用其他端口：

```
python -m backend.app 8080
```

启动后终端会显示：

```
==================================================
招聘数据分析后端服务
==================================================
访问地址: http://localhost:5001
API文档: http://localhost:5001/api/summary
==================================================
```

**注意**：后端运行期间不要关闭这个终端窗口！关闭窗口服务就停了。

---

### 第6步：浏览器查看

在浏览器地址栏输入：

```
http://localhost:5001
```

就能看到招聘数据分析看板页面。

---

## 三、API接口一览（调试用）

在浏览器里直接访问这些URL可以看到原始JSON数据：

| URL | 说明 |
|-----|------|
| http://localhost:5001/api/summary | 总体概览（岗位数、平均薪资） |
| http://localhost:5001/api/salary_distribution | 薪资分布 |
| http://localhost:5001/api/city_distribution | 城市分布 |
| http://localhost:5001/api/city_salary | 各城市薪资对比 |
| http://localhost:5001/api/experience | 经验要求分布 |
| http://localhost:5001/api/experience_salary | 不同经验薪资 |
| http://localhost:5001/api/education | 学历要求分布 |
| http://localhost:5001/api/education_salary | 不同学历薪资 |
| http://localhost:5001/api/tags | 热门技术标签 |
| http://localhost:5001/api/company_size | 公司规模分布 |
| http://localhost:5001/api/full_analysis | 全部分析结果 |
| http://localhost:5001/api/raw_data | 原始数据列表 |

---

## 四、日常使用（最简流程）

如果你只是想启动看板看数据，不需要重新爬虫和分析（数据已经有了），只需两步：

```
cd D:\recruitment1
.\venv\Scripts\activate
python -m backend.app
```

然后浏览器打开 http://localhost:5001

---

## 五、重新采集数据的完整流程

如果你想更新数据（比如采集更多城市或更多页），完整流程是：

```
cd D:\recruitment1
.\venv\Scripts\activate

# 1. 爬虫采集
python -m scraper.zhaopin_scraper --keywords Java --city 北京 --pages 3 --no-headless
python -m scraper.zhaopin_scraper --keywords Python --city 北京 --pages 3 --no-headless

# 2. 数据分析
python -m analysis.analysis

# 3. 启动服务（如果之前的服务还在运行，先关掉那个终端窗口）
python -m backend.app
```

浏览器打开 http://localhost:5001

---

## 六、停止服务

直接关闭运行 `python -m backend.app` 的那个终端窗口即可。

或者在终端里按 Ctrl+C 停止Flask服务。

---

## 七、数据文件说明

| 文件路径 | 内容 | 什么时候用 |
|----------|------|-----------|
| data/raw/java_jobs_zhaopin.json | 爬取的原始Java数据 | 爬虫产出 |
| data/raw/python_jobs_zhaopin.json | 爬取的原始Python数据 | 爬虫产出 |
| data/processed/java_jobs_cleaned.json | 清洗后的Java数据 | 分析流程产出 |
| data/processed/python_jobs_cleaned.json | 清洗后的Python数据 | 分析流程产出 |
| data/processed/analysis_result.json | 最终分析结果 | 分析流程产出，前端直接读取 |

**关键**：前端看板读取的是 analysis_result.json，所以每次重新爬虫后必须运行 `python -m analysis.analysis` 更新分析结果。

---

## 八、遇到问题怎么办

1. **页面打开但图表空白** → 按 F12 打开浏览器开发者工具，看 Console 选项卡有没有红色报错

2. **API返回空数据** → 确认 data/processed/analysis_result.json 是否存在且有内容。如果不存在，运行 `python -m analysis.analysis`

3. **爬虫报错** → 查看 data/raw/ 下的 debug HTML文件，那是爬虫保存的页面源码

4. **虚拟环境损坏** → 重建：
```
cd D:\recruitment1
python -m venv venv
.\venv\Scripts\activate
pip install flask flask-cors requests beautifulsoup4 lxml selenium webdriver-manager
```

5. **端口被占用** → 用其他端口启动：`python -m backend.app 8080`，浏览器访问 http://localhost:8080
