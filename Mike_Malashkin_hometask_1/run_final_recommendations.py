import glob
from analyze_sober_reviews import generate_recommendations
import json
import os

def get_latest_file(pattern):
    files = glob.glob(os.path.join('output', pattern))
    if not files:
        print(f'Файл не найден по маске: {pattern}')
        return None
    files.sort(key=os.path.getctime, reverse=True)
    return os.path.basename(files[0])

# Находим последние файлы по маске
classified_file = get_latest_file('classified_reviews_*.json')
bug_discussion_file = get_latest_file('discussion_bug_reports_*.json')
feature_discussion_file = get_latest_file('discussion_feature_requests_*.json')
bug_summary_file = get_latest_file('discussion_summary_bug_reports_*.txt')
feature_summary_file = get_latest_file('discussion_summary_feature_requests_*.txt')

if not classified_file:
    raise FileNotFoundError('Не найден файл с классифицированными отзывами!')

# Загружаем классифицированные отзывы
with open(os.path.join('output', classified_file), 'r', encoding='utf-8') as f:
    classified_reviews = json.load(f)['categories']

# Запускаем генерацию рекомендаций
generate_recommendations(
    classified_reviews,
    bug_discussion_file,
    feature_discussion_file,
    bug_summary_file,
    feature_summary_file
)