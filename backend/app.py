"""
Flask后端API - 提供招聘数据分析接口
"""
import os
import sys
import json

from flask import Flask, jsonify, send_from_directory, Response
from flask_cors import CORS

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.analysis import RecruitmentAnalyzer

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# 修复 MIME 类型映射
MIME_TYPES = {
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
}


def send_static_file(filename):
    """发送静态文件并设置正确的 Content-Type"""
    file_path = os.path.join(app.static_folder, filename)
    ext = os.path.splitext(filename)[1].lower()
    mime_type = MIME_TYPES.get(ext, 'application/octet-stream')
    return Response(
        open(file_path, 'rb').read(),
        mimetype=mime_type,
        headers={'Cache-Control': 'no-cache'}
    )

# 初始化分析器
processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
analyzer = RecruitmentAnalyzer(processed_dir)


@app.route('/')
def index():
    """返回前端页面"""
    return send_static_file('index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """返回CSS文件（正确的MIME类型）"""
    return send_static_file(os.path.join('css', filename))


@app.route('/js/<path:filename>')
def serve_js(filename):
    """返回JS文件（正确的MIME类型）"""
    return send_static_file(os.path.join('js', filename))


@app.route('/api/summary')
def api_summary():
    """总体概览"""
    return jsonify(analyzer.get_summary())


@app.route('/api/salary_distribution')
def api_salary_distribution():
    """薪资分布"""
    return jsonify(analyzer.salary_distribution())


@app.route('/api/city_distribution')
def api_city_distribution():
    """城市分布"""
    return jsonify(analyzer.city_distribution())


@app.route('/api/city_salary')
def api_city_salary():
    """各城市薪资对比"""
    return jsonify(analyzer.city_salary_comparison())


@app.route('/api/experience')
def api_experience():
    """经验要求分析"""
    return jsonify(analyzer.experience_analysis())


@app.route('/api/experience_salary')
def api_experience_salary():
    """不同经验级别薪资"""
    return jsonify(analyzer.experience_salary())


@app.route('/api/education')
def api_education():
    """学历要求分析"""
    return jsonify(analyzer.education_analysis())


@app.route('/api/education_salary')
def api_education_salary():
    """不同学历薪资"""
    return jsonify(analyzer.education_salary())


@app.route('/api/tags')
def api_tags():
    """热门技术标签"""
    return jsonify(analyzer.top_tags())


@app.route('/api/company_size')
def api_company_size():
    """公司规模分布"""
    return jsonify(analyzer.company_size_analysis())


@app.route('/api/full_analysis')
def api_full_analysis():
    """完整分析结果"""
    return jsonify(analyzer.full_analysis())


@app.route('/api/raw_data')
def api_raw_data():
    """原始数据（支持分页）"""
    # 读取清洗后的数据
    all_data = []
    for role in ['java', 'python']:
        filepath = os.path.join(processed_dir, f'{role}_jobs_cleaned.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                all_data.extend(json.load(f))

    return jsonify({'total': len(all_data), 'data': all_data})


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    print("=" * 50)
    print("招聘数据分析后端服务")
    print("=" * 50)
    print(f"访问地址: http://localhost:{port}")
    print(f"API文档: http://localhost:{port}/api/summary")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
