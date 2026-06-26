# 招聘数据分析项目 — 遇到的问题及解决方案

> 项目：D:\recruitment1 | Java vs Python 招聘数据对比看板
> 数据来源：智联招聘 | 覆盖城市：北京、上海、广州、深圳、成都、武汉

---

## 一、数据采集阶段

### 1. 反爬限制导致无法获取数据

**问题描述：**
使用 requests 直接请求智联招聘页面时，返回的 HTML 中不包含招聘列表数据（JS 动态渲染），或被反爬机制拦截（验证码、IP 封禁）。

**解决方案：**
- 放弃 requests 方式，改用 **Selenium + ChromeDriver** 浏览器自动化采集，模拟真实用户行为
- 添加反反爬措施：通过 `execute_cdp_cmd` 隐藏 `navigator.webdriver` 标记，注入属性覆盖让页面无法检测自动化工具
- 随机化 User-Agent（维护 6 个 UA 轮换）+ 每次请求间随机延迟 2~5 秒
- 见文件：`scraper/zhaopin_scraper.py` → `_init_driver()` 方法（第 52-81 行）

---

### 2. 爬取结果为 0 条（CSS 选择器不匹配）

**问题描述：**
虽有数据返回，但解析逻辑中使用的 CSS 选择器与实际页面结构不匹配，导致提取不到任何职位信息。

**解决方案：**
- 打开浏览器手动审查智联招聘实际页面结构，找到真实 DOM 选择器
- 改为 3 套 CSS 选择器策略逐级降级：优先选择器 → 备用选择器 → 兜底选择器
- 解析失败时自动保存页面 HTML 源码到 `data/raw/` 供排查
- 见文件：`scraper/zhaopin_scraper.py` → `_parse_job_list()` 方法（第 164-197 行）

---

### 3. ChromeDriver 下载锁文件冲突

**问题描述：**
`webdriver-manager` 自动下载 ChromeDriver 时报错 `FileExistsError: .wdm-lock-chromedriver-win64`，无法继续。

**解决方案：**
- 手动删除 `C:\Users\<用户名>\.wdm\` 目录下的 `.wdm-lock-*` 锁文件
- 重新运行爬虫，`webdriver-manager` 会自动完成下载

---

### 4. 薪资文本格式多样导致解析困难

**问题描述：**
招聘网站上薪资格式不统一，存在 "10K-15K"、"8000-15000元"、"1.2-1.5万"、"面议" 等多种写法。

**解决方案：**
- 编写专用的多格式薪资解析器，统一转换为 (min, max, avg) 三元组
- 依次尝试匹配：千分位格式 → K 单位 → 万单位 → 单值 → 面议
- 每种格式独立 try-except 容错，解析失败不丢整条数据
- 见文件：`scraper/zhaopin_scraper.py` → `_parse_salary()` 方法（第 309-364 行）

---

## 二、数据处理阶段

### 5. 薪资平均值计算错误

**问题描述：**
清洗逻辑中 `salary_avg` 被错误赋值为 `salary_max`（只取区间最大值），导致平均薪资虚高。

**解决方案：**
- 改为 `salary_avg = (salary_min + salary_max) / 2`，取区间中位数
- 见文件：`analysis/data_cleaner.py` → `clean_salary()` 方法

---

### 6. 薪资异常值污染分析结果

**问题描述：**
部分数据存在薪资 ≤0、月薪 >10 万、min > max 等异常情况，直接参与分析会扭曲统计结果。

**解决方案：**
- 薪资 ≤0 → 标记为"面议"，不参与薪资类分析
- min > max → 自动交换两个值
- 月薪 >10 万 → 标记为异常值，排除
- 见文件：`analysis/data_cleaner.py` → `clean_salary()` 方法（第 16-39 行）

---

### 7. 城市 / 经验 / 学历名称不统一

**问题描述：**
爬取数据中同一含义的字段存在多种写法，例如城市 "北京市" / "北京"、经验 "1-3年经验" / "1-3年"、学历 "学历不限" / "不限"。

**解决方案：**
- 建立 20 个城市标准名称映射表，去除区级信息和多余后缀
- 经验级别合并为 7 档（应届生、1-3年、3-5年、5-10年、10年以上、不限）
- 学历合并为 5 档（大专、本科、硕士、博士、不限），"高中/中专"归入"其他"
- 见文件：`analysis/data_cleaner.py` → `normalize_*()` 系列方法（第 41-82 行）

---

## 三、后端开发阶段

### 8. 页面只有裸 SVG 图标，无样式无数据

**问题描述：**
启动 Flask 后访问页面，HTML 结构正常，但 CSS 全部失效、JS 不执行，页面只显示裸 SVG 图标和文字。

**根本原因：**
Windows 系统下 Flask 自动检测的 MIME 类型不正确：CSS 被返回为 `application/x-css`、JS 被返回为 `text/plain`，浏览器拒绝加载。

**解决方案：**
- 自定义 MIME_TYPES 字典，显式指定 CSS 为 `text/css; charset=utf-8`、JS 为 `application/javascript; charset=utf-8`
- 创建专用路由 `/css/<path>` 和 `/js/<path>`，通过 `send_static_file()` 确保正确 Content-Type
- 见文件：`backend/app.py` → `MIME_TYPES` 字典（第 20-31 行）+ `send_static_file()`（第 34-43 行）

---

### 9. Google Fonts 被屏蔽导致 CSS 加载中断

**问题描述：**
CSS 文件第一行 `@import url('https://fonts.googleapis.com/...')` 在国内被 GFW 阻断，浏览器等待超时，整个 CSS 文件无法加载。

**解决方案：**
- 删除所有 Google Fonts 引用
- 替换为系统原生字体栈：`PingFang SC, Microsoft YaHei, system-ui, sans-serif`
- 见文件：`frontend/css/style.css`

---

### 10. debug=True 在 Windows 后台运行卡死

**问题描述：**
Flask 以 `debug=True` 模式运行在 Windows CMD 后台时，reloader 进程会异常占用导致主进程卡死。

**解决方案：**
- 生产/测试环境统一使用 `debug=False`
- 见文件：`backend/app.py` 第 157 行

---

### 11. WSL venv 在 Windows 下不可用

**问题描述：**
在 WSL2（Linux）中创建的 Python 虚拟环境，回到 Windows 下激活失败或运行异常。

**解决方案：**
- 删除原有 venv 目录，用 Windows 本地 Python 重新创建
- 命令：`python -m venv venv`（在 Windows CMD 中执行）
- 激活方式改为：`venv\Scripts\activate`

---

## 四、前端开发阶段

### 12. 直接打开 HTML 文件导致图表全部空白

**问题描述：**
双击 `index.html` 以 `file://` 协议打开，ECharts 加载成功，但所有图表区域均为空白。

**根本原因：**
`dashboard.js` 通过 `fetch('/api/...')` 从 Flask 后端获取数据。`file://` 协议下，`/api/...` 路径无法解析到 Flask 服务器，所有 fetch 请求返回 404。每个渲染函数中 `if (!data) return;` 静默退出，图表不画任何内容。

**解决方案：**
- **必须通过 Flask 访问**，不能直接双击 HTML 文件
- 启动命令：`cd /d D:\recruitment1 && venv\Scripts\python.exe -m backend.app`
- 访问地址：`http://localhost:5001/`

---

### 13. ECharts 从 CDN 改为本地文件

**问题描述：**
最初 ECharts 通过 CDN 远程引用，在离线或网络不稳定时无法加载，且国内 CDN 速度慢。

**解决方案：**
- 下载 ECharts 5.5.0 完整版到本地 `frontend/js/echarts.min.js`
- HTML 改为引用本地路径，无需网络即可运行

---

## 五、问题分类汇总

| 类别 | 数量 | 典型问题 |
|------|------|----------|
| 反爬与数据采集 | 4 个 | 反爬拦截、选择器失效、薪资解析、ChromeDriver 锁 |
| 数据清洗 | 3 个 | 薪资计算错误、异常值、名称不统一 |
| 后端服务 | 3 个 | MIME 类型、Google Fonts、debug 卡死 |
| 环境兼容 | 1 个 | WSL venv 不兼容 |
| 前端加载 | 2 个 | 直接打开 HTML 空白、CDN 改为本地 |

**合计：13 个问题，全部已解决。**

---

## 六、正确的启动方式

```bash
# 一行命令启动（推荐）
cd /d D:\recruitment1 && venv\Scripts\python.exe -m backend.app

# 浏览器访问
http://localhost:5001/
```

**⚠️ 不要双击 index.html 打开页面，图表不会显示。**

---

*文档生成时间：2026-06-22*
