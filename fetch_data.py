import json, requests

apis = {
    'summary': 'http://localhost:5001/api/summary',
    'salary_distribution': 'http://localhost:5001/api/salary_distribution',
    'city_distribution': 'http://localhost:5001/api/city_distribution',
    'city_salary': 'http://localhost:5001/api/city_salary',
    'experience': 'http://localhost:5001/api/experience',
    'experience_salary': 'http://localhost:5001/api/experience_salary',
    'education': 'http://localhost:5001/api/education',
    'education_salary': 'http://localhost:5001/api/education_salary',
    'tags': 'http://localhost:5001/api/tags',
    'company_size': 'http://localhost:5001/api/company_size',
}

all_data = {}
for name, url in apis.items():
    r = requests.get(url, timeout=5)
    all_data[name] = r.json()
    print(f'{name}: OK')

with open(r'D:\recruitment1\frontend\data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False)
print('data.json saved!')
