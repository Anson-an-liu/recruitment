/**
 * 招聘数据分析看板 - 主脚本
 * 设计系统: Data-Dense Dashboard
 * 配色: Blue Data + Amber Highlights
 */

const API_BASE = '/api';
let charts = {};

// ========== 设计系统配色 ==========
const COLORS = {
  java: '#E74C3C',
  javaGradient: ['#E74C3C', '#F1948A'],
  python: '#10B981',
  pythonGradient: ['#10B981', '#6EE7B7'],
  primary: '#1E40AF',
  primaryLight: '#3B82F6',
  accent: '#D97706',
  text: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',
  border: '#E2E8F0',
  bg: '#F8FAFC',
};

// ========== 工具函数 ==========

async function fetchAPI(endpoint) {
  try {
    const response = await fetch(`${API_BASE}/${endpoint}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (err) {
    console.error(`[API] ${endpoint} 失败:`, err);
    return null;
  }
}

function formatSalary(val) {
  if (!val || val === 0) return '--';
  if (val >= 10000) return '¥' + (val / 1000).toFixed(0) + 'K';
  return '¥' + val.toLocaleString();
}

function $(id) { return document.getElementById(id); }

function safeText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function safeHtml(id, html) {
  const el = $(id);
  if (el) el.innerHTML = html;
}

function initChart(domId) {
  const dom = $(domId);
  if (!dom) { console.warn('[Chart] 找不到容器 #' + domId); return null; }
  dom.style.width = '100%';
  dom.style.minHeight = '350px';
  if (charts[domId]) { try { charts[domId].dispose(); } catch(e) {} }
  try {
    var chart = echarts.init(dom);
    charts[domId] = chart;
    return chart;
  } catch(e) {
    console.error('[Chart] 初始化失败 #' + domId + ':', e);
    dom.innerHTML = '<div class="empty-state"><p>图表加载失败</p></div>';
    return null;
  }
}

// ========== 通用样式辅助 ==========

function mergeStyle(base, extra) {
  var result = {};
  for (var k in base) { if (base.hasOwnProperty(k)) result[k] = base[k]; }
  for (var k in extra) { if (extra.hasOwnProperty(k)) result[k] = extra[k]; }
  return result;
}

// 通用的 tooltip 样式
const tooltipStyle = {
  backgroundColor: 'rgba(15, 23, 42, 0.92)',
  borderColor: 'rgba(255,255,255,0.08)',
  borderWidth: 1,
  textStyle: { color: '#F8FAFC', fontSize: 13 },
  extraCssText: 'border-radius:8px;padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.2);backdrop-filter:blur(8px);',
};

// 通用的图例样式
const legendStyle = {
  top: 0,
  textStyle: { fontSize: 13, color: COLORS.textSecondary },
  itemWidth: 14,
  itemHeight: 10,
};

// 通用的 grid 样式
function gridStyle(topOffset) {
  return {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: topOffset || '36px',
    containLabel: true,
  };
}

window.addEventListener('resize', function() {
  Object.values(charts).forEach(function(c) { try { c.resize(); } catch(e){} });
});

// ========== 概览卡片 ==========

async function renderOverview() {
  var data = await fetchAPI('summary');
  if (!data) return;

  safeText('total-count', data.total.toLocaleString());
  safeText('java-count', data.java_count.toLocaleString());
  safeText('python-count', data.python_count.toLocaleString());

  var salDiff = data.salary_diff || 0;
  safeText('java-avg-salary', formatSalary(data.java_avg_salary));
  safeText('python-avg-salary', formatSalary(data.python_avg_salary));

  if (salDiff > 0) {
    safeHtml('salary-diff', 'Python 高出 <span class="up">¥' + salDiff.toLocaleString() + '</span>');
    safeHtml('salary-value', formatSalary(data.python_avg_salary) + ' <span style="font-size:14px;color:#94A3B8;font-weight:400;font-family:var(--font-sans);">Python 平均</span>');
  } else if (salDiff < 0) {
    safeHtml('salary-diff', 'Java 高出 <span class="down">¥' + Math.abs(salDiff).toLocaleString() + '</span>');
    safeHtml('salary-value', formatSalary(data.java_avg_salary) + ' <span style="font-size:14px;color:#94A3B8;font-weight:400;font-family:var(--font-sans);">Java 平均</span>');
  } else {
    safeText('salary-diff', '两者持平');
    safeText('salary-value', formatSalary(data.python_avg_salary));
  }
}

// ========== 薪资分布图 ==========

async function renderSalaryDistribution() {
  var data = await fetchAPI('salary_distribution');
  if (!data) return;
  var chart = initChart('chart-salary-dist');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.categories, axisLabel: { fontSize: 12, color: COLORS.textSecondary, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '岗位数量', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'bar', data: data.java, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 11, color: COLORS.java, fontWeight: 600 } },
      { name: 'Python', type: 'bar', data: data.python, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 11, color: COLORS.python, fontWeight: 600 } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 城市分布图 ==========

async function renderCityDistribution() {
  var data = await fetchAPI('city_distribution');
  if (!data) return;
  var chart = initChart('chart-city-dist');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.cities, axisLabel: { fontSize: 12, color: COLORS.textSecondary, rotate: data.cities.length > 6 ? 30 : 0, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '岗位数量', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'bar', data: data.java, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 28, label: { show: false } },
      { name: 'Python', type: 'bar', data: data.python, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 28, label: { show: false } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 城市薪资对比 ==========

async function renderCitySalary() {
  var data = await fetchAPI('city_salary');
  if (!data) return;
  var chart = initChart('chart-city-salary');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis' }),
    legend: mergeStyle(legendStyle, { data: ['Java平均薪资', 'Python平均薪资'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.cities, axisLabel: { fontSize: 11, color: COLORS.textSecondary, rotate: data.cities.length > 4 ? 25 : 0, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '月薪', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted, formatter: function(v){return (v/1000).toFixed(0)+'K';} }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java平均薪资', type: 'bar', data: data.java_salary, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 26, label: { show: true, position: 'top', fontSize: 10, color: COLORS.textSecondary } },
      { name: 'Python平均薪资', type: 'bar', data: data.python_salary, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 26, label: { show: true, position: 'top', fontSize: 10, color: COLORS.textSecondary } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 经验要求分布 ==========

async function renderExperience() {
  var data = await fetchAPI('experience');
  if (!data) return;
  var chart = initChart('chart-experience');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.categories, axisLabel: { fontSize: 12, color: COLORS.textSecondary, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '岗位数量', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'bar', data: data.java, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 11, color: COLORS.java, fontWeight: 600 } },
      { name: 'Python', type: 'bar', data: data.python, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 11, color: COLORS.python, fontWeight: 600 } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 经验薪资对比 ==========

async function renderExperienceSalary() {
  var data = await fetchAPI('experience_salary');
  if (!data) return;
  var chart = initChart('chart-experience-salary');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis' }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.categories, axisLabel: { fontSize: 12, color: COLORS.textSecondary }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '平均月薪', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted, formatter: function(v){return (v/1000).toFixed(0)+'K';} }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'line', data: data.java, smooth: true, lineStyle: { color: COLORS.java, width: 3 }, itemStyle: { color: COLORS.java }, symbol: 'circle', symbolSize: 8, label: { show: true, fontSize: 10, color: COLORS.java, fontWeight: 600 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(231,76,60,0.15)' }, { offset: 1, color: 'rgba(231,76,60,0)' }] } } },
      { name: 'Python', type: 'line', data: data.python, smooth: true, lineStyle: { color: COLORS.python, width: 3 }, itemStyle: { color: COLORS.python }, symbol: 'circle', symbolSize: 8, label: { show: true, fontSize: 10, color: COLORS.python, fontWeight: 600 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16,185,129,0.15)' }, { offset: 1, color: 'rgba(16,185,129,0)' }] } } }
    ],
    animationDuration: 800,
    animationEasing: 'cubicOut',
  });
}

// ========== 学历分布 ==========

async function renderEducation() {
  var data = await fetchAPI('education');
  if (!data) return;
  var chart = initChart('chart-education');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: gridStyle('40px'),
    xAxis: { type: 'category', data: data.categories, axisLabel: { fontSize: 12, color: COLORS.textSecondary, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '岗位数量', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'bar', data: data.java, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 36, label: { show: true, position: 'top', fontSize: 11, color: COLORS.java, fontWeight: 600 } },
      { name: 'Python', type: 'bar', data: data.python, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 36, label: { show: true, position: 'top', fontSize: 11, color: COLORS.python, fontWeight: 600 } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 学历薪资雷达图 ==========

async function renderEducationSalary() {
  var data = await fetchAPI('education_salary');
  if (!data) return;
  var chart = initChart('chart-education-salary');
  if (!chart) return;

  var allVals = (data.java||[]).concat(data.python||[]);
  var maxVal = Math.max.apply(null, allVals.filter(function(v){return v>0;}));
  if (!maxVal || maxVal < 10000) maxVal = 30000;
  maxVal = Math.ceil(maxVal / 5000) * 5000 + 5000;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis' }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    radar: {
      center: ['50%', '55%'],
      radius: '65%',
      indicator: data.categories.map(function(c){ return { name: c, max: maxVal }; }),
      axisName: { fontSize: 13, color: COLORS.text },
      splitArea: { areaStyle: { color: ['rgba(30,64,175,0.02)', 'rgba(30,64,175,0.04)'] } },
      splitLine: { lineStyle: { color: COLORS.border } },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    series: [{
      type: 'radar',
      data: [
        { name: 'Java', value: data.java, lineStyle: { color: COLORS.java, width: 2.5 }, areaStyle: { color: 'rgba(231,76,60,0.12)' }, itemStyle: { color: COLORS.java }, symbol: 'circle', symbolSize: 6 },
        { name: 'Python', value: data.python, lineStyle: { color: COLORS.python, width: 2.5 }, areaStyle: { color: 'rgba(16,185,129,0.12)' }, itemStyle: { color: COLORS.python }, symbol: 'circle', symbolSize: 6 }
      ]
    }],
    animationDuration: 700,
    animationEasing: 'cubicOut',
  });
}

// ========== 技术标签 ==========

async function renderTags() {
  var data = await fetchAPI('tags');
  if (!data) return;

  var cj = initChart('chart-tags-java');
  if (cj && data.java_tags) {
    cj.setOption({
      tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
      grid: { left: '3%', right: '10%', bottom: '3%', top: '5px', containLabel: true },
      xAxis: { type: 'value', name: '出现次数', nameTextStyle: { fontSize: 11, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
      yAxis: { type: 'category', data: data.java_tags.slice().reverse(), inverse: true, axisLabel: { fontSize: 12, color: COLORS.textSecondary, fontWeight: 500 }, axisLine: { lineStyle: { color: COLORS.border } } },
      series: [{
        type: 'bar',
        data: data.java_values.slice().reverse().map(function(v){
          return { value: v, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: COLORS.java }, { offset: 1, color: '#F1948A' }] }, borderRadius: [0, 4, 4, 0] } };
        }),
        barMaxWidth: 20,
        label: { show: true, position: 'right', fontSize: 11, color: COLORS.textSecondary, fontWeight: 500 }
      }]
    });
  }

  var cp = initChart('chart-tags-python');
  if (cp && data.python_tags) {
    cp.setOption({
      tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
      grid: { left: '3%', right: '10%', bottom: '3%', top: '5px', containLabel: true },
      xAxis: { type: 'value', name: '出现次数', nameTextStyle: { fontSize: 11, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
      yAxis: { type: 'category', data: data.python_tags.slice().reverse(), inverse: true, axisLabel: { fontSize: 12, color: COLORS.textSecondary, fontWeight: 500 }, axisLine: { lineStyle: { color: COLORS.border } } },
      series: [{
        type: 'bar',
        data: data.python_values.slice().reverse().map(function(v){
          return { value: v, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: COLORS.python }, { offset: 1, color: '#6EE7B7' }] }, borderRadius: [0, 4, 4, 0] } };
        }),
        barMaxWidth: 20,
        label: { show: true, position: 'right', fontSize: 11, color: COLORS.textSecondary, fontWeight: 500 }
      }]
    });
  }
}

// ========== 公司规模 ==========

async function renderCompanySize() {
  var data = await fetchAPI('company_size');
  if (!data) return;
  var chart = initChart('chart-company-size');
  if (!chart) return;

  chart.setOption({
    tooltip: mergeStyle(tooltipStyle, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    legend: mergeStyle(legendStyle, { data: ['Java', 'Python'] }),
    grid: { left: '3%', right: '4%', bottom: '12%', top: '50px', containLabel: true },
    xAxis: { type: 'category', data: data.categories, axisLabel: { fontSize: 11, color: COLORS.textSecondary, rotate: 30, interval: 0 }, axisLine: { lineStyle: { color: COLORS.border } } },
    yAxis: { type: 'value', name: '岗位数量', nameTextStyle: { fontSize: 12, color: COLORS.textMuted }, axisLabel: { fontSize: 11, color: COLORS.textMuted }, splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } } },
    series: [
      { name: 'Java', type: 'bar', data: data.java, itemStyle: { color: COLORS.java, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 10, color: COLORS.textSecondary } },
      { name: 'Python', type: 'bar', data: data.python, itemStyle: { color: COLORS.python, borderRadius: [4,4,0,0] }, barMaxWidth: 32, label: { show: true, position: 'top', fontSize: 10, color: COLORS.textSecondary } }
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  });
}

// ========== 主入口 ==========

async function initDashboard() {
  if (typeof echarts === 'undefined') {
    document.body.innerHTML = '<div style="padding:60px;text-align:center;color:#DC2626;font-size:16px;font-family:sans-serif;">ECharts 库未加载！请检查 js/echarts.min.js 文件是否存在。</div>';
    console.error('[FATAL] echarts 未定义！');
    return;
  }
  console.log('[Dashboard] ECharts 已就绪, 版本: ' + echarts.version);

  try {
    await renderOverview();

    var tasks = [
      renderSalaryDistribution(),
      renderCityDistribution(),
      renderCitySalary(),
      renderExperience(),
      renderExperienceSalary(),
      renderEducation(),
      renderEducationSalary(),
      renderTags(),
      renderCompanySize()
    ];

    var results = await Promise.allSettled(tasks);
    var ok = results.filter(function(r){return r.status==='fulfilled'}).length;
    var fail = results.length - ok;
    console.log('[Dashboard] 图表渲染完成: ' + ok + '/' + results.length + ' 成功');

    if (fail > 0) {
      results.forEach(function(r, i){
        if (r.status === 'rejected') {
          console.error('[Dashboard] 图表#' + i + ' 失败:', r.reason);
        }
      });
    }

  } catch(err) {
    console.error('[Dashboard] 初始化致命错误:', err);
  }
}

document.addEventListener('DOMContentLoaded', initDashboard);
