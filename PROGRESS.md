# 招聘信息数据分析项目 - 进度文档

> **项目路径**：`D:\recruitment1`  
> **最后更新**：2026-06-21  
> **当前状态**：✅ 全部正常！后端 API + 前端 ECharts 图表均运行正常；智联招聘 Selenium 爬虫已编写

---

## 一、项目概述

对比 Java 和 Python 程序员招聘数据，包含：爬虫 → 数据清洗 → 数据分析 → Web 可视化看板。

---

## 二、已完成

### ✅ 1. 项目结构
```
recruitment1/
├── scraper/
│   ├── base_scraper.py      # 爬虫基类（UA池、重试、延迟）
│   ├── job51_scraper.py     # ⚠️ 桩代码，requests方式，易被反爬
│   ├── boss_scraper.py      # ⚠️ 桩代码，requests方式，易被反爬
│   ├── zhaopin_scraper.py   # ✅ 新增！智联招聘 Selenium 浏览器自动化爬虫
│   ├── mock_data.py         # ✅ 模拟数据生成器
│   └── run_scraper.py      # ✅ 爬虫入口（已更新，支持--mode zhaopin）
├── analysis/
│   ├── data_cleaner.py     # ✅ 数据清洗
│   └── analysis.py         # ✅ 多维度分析引擎
├── backend/
│   └── app.py              # ✅ Flask API（10个接口）
├── frontend/
│   ├── index.html          # ✅ 主页面
│   ├── css/style.css      # ✅ 样式
│   └── js/
│       ├── dashboard.js     # ✅ 正常，9 个图表正常渲染
│       └── echarts.min.js  # ✅ 本地 ECharts 5.5.0
├── data/
│   ├── raw/                # 模拟数据（Java 198条，Python 200条）
│   └── processed/          # 清洗后数据 + analysis_result.json
├── venv/                   # Python 虚拟环境（已重建，含selenium+webdriver-manager）
├── requirements.txt        # ✅ 已更新，新增selenium和webdriver-manager
└── README.md
```

### ✅ 2. 模拟数据
- `python -m scraper.mock_data` 生成
- `data/raw/java_jobs_raw.json`：198 条
- `data/raw/python_jobs_raw.json`：200 条

### ✅ 3. 数据清洗与分析
- 清洗后 → `data/processed/java_jobs_cleaned.json`（198条）
- 清洗后 → `data/processed/python_jobs_cleaned.json`（200条）
- 分析结果 → `data/processed/analysis_result.json`
- 分析维度：薪资分布、城市分布、城市薪资、经验分布、经验薪资、学历分布、学历薪资、技术标签、公司规模

### ✅ 4. Flask 后端（正常运行 ✅）
- 启动命令：`python -m backend.app 5001`
- 访问：`http://localhost:5001`
- 所有 API 接口均正常返回数据（已用 curl 验证）
- **注意**：`debug=True` 在 Windows 后台运行会卡死，已改为 `debug=False`

### ✅ 5. 前端页面可访问
- `http://localhost:5001` 可打开页面
- 概览卡片数字正常显示（`/api/summary` 正常）
- **所有 9 个 ECharts 图表均正常渲染** ✅

### ✅ 6. 联招聘 Selenium 爬虫（新增！）
- 文件：`scraper/zhaopin_scraper.py`
- 技术方案：Selenium + ChromeDriver（webdriver-manager自动管理）
- 核心特性：
  - 浏览器自动化采集，模拟真实用户行为（类似后羿采集器）
  - 反反爬措施：隐藏webdriver特征、随机UA、随机延迟
  - 支持单城市和多城市批量采集（20个主要城市）
  - 自动调试：解析失败时保存页面源码供排查
  - 多选择器策略：适配智联招聘页面结构变化
- 快速接口：
  - `quick_scrape()` — 单城市一行采集
  - `multi_city_scrape()` — 多城市批量采集
- 命令行运行：
  - 单城市：`python -m scraper.zhaopin_scraper --keywords Java Python --city 北京 --pages 5`
  - 多城市：`python -m scraper.zhaopin_scraper --keywords Java Python --multi-city --pages 3`
  - 调试模式：`python -m scraper.zhaopin_scraper --no-headless`（显示浏览器窗口）
- 数据格式：与现有项目完全兼容（title, company, salary_min/max/avg, city, experience, education, tags, etc.)

---

## 三、当前核心问题 ✅

### 问题：前端图表不显示（已解决）

**现象**：
- 浏览器打开 `http://localhost:5001`，概览数字显示正常
- 所有图表区域均为空白

**根本原因（已定位）**：
用户直接双击 `index.html` 以 `file://` 协议打开，JS 中的 `fetch('/api/...')` 无法解析到 Flask 后端，
所有 API 返回 null，图表函数静默退出。

**解决方案**：
- 必须通过 Flask 服务访问：`cd /d D:\recruitment1 && venv\Scripts\python.exe -m backend.app`
- 访问 `http://localhost:5001/` 即可看到全部 9 个图表正常渲染
- 已验证：Node --check 无语法错误，Playwright 实机测试 9/9 图表成功

---

## 四、待完成任务

### 🔴 P0 - 已完成 ✅
- [x] **修复 `dashboard.js` 的所有 JS 语法错误** → 经检查无语法错误，问题为 file:// 协议导致
- [x] 验证 10 个图表是否都能正常渲染 → 全部 9 个图表正常渲染
- [x] 检查后端 API 返回的数据格式 → 字段名一致，数据正常

### 🟡 P1 - 重要
- [ ] **运行智联招聘爬虫，采集真实数据**
  - 先单城市测试：`python -m scraper.zhaopin_scraper --keywords Java --city 北京 --pages 3 --no-headless`
  - 如成功，再批量多城市采集
- [ ] 将真实数据接入清洗和分析流程
- [ ] `job51_scraper.py` 和 `boss_scraper.py` 可考虑也改为 Selenium 方式

### 🟢 P2 - 可选
- [ ] 增加城市筛选功能
- [ ] 增加数据导出（CSV/Excel）
- [ ] Docker 部署配置

---

## 五、启动步骤（下次继续时使用）

```bash
cd D:\recruitment1

# 1. 激活虚拟环境
.\venv\Scripts\activate

# 2. 如数据丢失，重新生成模拟数据
python -m scraper.mock_data
python -m analysis.analysis

# 3. 运行智联招聘爬虫（单城市测试）
python -m scraper.zhaopin_scraper --keywords Java --city 北京 --pages 3 --no-headless

# 4. 运行智联招聘爬虫（多城市批量采集）
python -m scraper.zhaopin_scraper --keywords Java Python --multi-city --pages 3

# 5. 通过 run_scraper.py 统一运行（支持所有模式）
python -m scraper.run_scraper --mode zhaopin --keywords Java Python --city 北京 --pages 5
python -m scraper.run_scraper --mode zhaopin --multi-city --pages 3

# 6. 重新运行分析（如有新数据）
python -m analysis.analysis

# 7. 启动后端（端口 5001）
python -m backend.app 5001

# 8. 浏览器访问
# http://localhost:5001
```

---

## 六、关键文件说明

| 文件 | 说明 |
|------|------|
| `backend/app.py` | Flask 后端，修改端口改这里 |
| `frontend/js/dashboard.js` | **✅ 正常**，通过 Flask 访问时图表正常渲染 |
| `scraper/zhaopin_scraper.py` | **✅ 新增** 智联招聘 Selenium 爬虫 |
| `scraper/run_scraper.py` | 爬虫统一入口，已支持 --mode zhaopin |
| `data/processed/analysis_result.json` | 分析结果，后端 API 的数据来源 |

---

*最后更新：2026-06-22 21:45*
