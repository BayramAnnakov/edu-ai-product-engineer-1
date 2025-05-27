import asyncio
import json
import os
from datetime import datetime
from app_reviews_scraper import AppReviewsScraper
from persona_generator import PersonaGenerator
from group_discussion import run_group_discussion
from summarizer import DiscussionSummarizer
from recommendations import Recommendations
from review_classifier import ReviewClassifier
from telegram_notifier import TelegramNotifier
from dotenv import load_dotenv
from openai import OpenAI
import glob

# Загружаем переменные окружения
load_dotenv()

# Параметры приложения Sober
APP_NAME = "Sober"
GOOGLE_PLAY_ID = "com.osu.cleanandsobertoolboxandroid"  # Корректный ID в Google Play
MONTHS = 12  # Период для анализа - 12 месяцев (1 год)

async def run_sober_analysis():
    """Основная функция для анализа отзывов приложения Sober"""
    print("Начинаем анализ отзывов приложения Sober...")
    
    # Текущий timestamp для именования файлов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Шаг 1: Сбор отзывов
    print("\n1. Сбор отзывов из Google Play...")
    scraper = AppReviewsScraper()
    reviews_data = scraper.get_app_reviews(
        app_name=APP_NAME,
        google_play_id=GOOGLE_PLAY_ID,
        months=MONTHS
    )
    
    # Сохраняем отзывы в файл
    reviews_file = scraper.save_reviews(reviews_data)
    reviews_path = os.path.join('output', reviews_file)
    
    # Загружаем сохраненные отзывы
    with open(reviews_path, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)
    
    # Проверяем, что есть отзывы для анализа
    all_reviews = []
    for site_name, site_data in reviews_data['sites'].items():
        all_reviews.extend(site_data['reviews'])
    
    if not all_reviews:
        print("Ошибка: не удалось собрать отзывы для анализа")
        return
    
    # Шаг 2: Определение темы приложения
    print("\n2. Определение темы приложения...")
    category, item_type, item_name = analyze_reviews_topic(all_reviews[:20])
    
    # Если определенное название не содержит имя приложения, добавляем его
    if APP_NAME.lower() not in item_name.lower():
        item_name = f"{APP_NAME} ({item_name})"
    
    print(f"Определена тема: {category}, {item_type}, {item_name}")
    
    # Шаг 3: Классификация отзывов
    print("\n3. Классификация отзывов на категории...")
    classifier = ReviewClassifier()
    classified_reviews = classifier.process_reviews(all_reviews)
    
    # Сохраняем классифицированные отзывы
    classified_file = f"classified_reviews_{timestamp}.json"
    with open(os.path.join('output', classified_file), 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'app_name': APP_NAME,
            'category': category,
            'item_type': item_type,
            'item_name': item_name,
            'categories': classified_reviews
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Классифицированные отзывы сохранены в файл: {classified_file}")

    # Шаг 4: Обработка отчетов о багах
    print("\n4. Обработка отчетов о багах...")
    
    # Инициализируем Telegram notifier (с обработкой ошибок)
    telegram_notifier = None
    try:
        telegram_notifier = TelegramNotifier()
        print("✅ Telegram notifier инициализирован")
    except Exception as e:
        print(f"⚠️  Telegram notifier не удалось инициализировать: {str(e)}")
        print("   Баг-репорты будут сохраняться только в файлы")
    
    if classified_reviews['bug_reports']['raw']:
        # Проверка каждого бага в баг-трекере (заглушка)
        for i, bug in enumerate(classified_reviews['bug_reports']['raw'], 1):
            bug_text = bug['text'] if isinstance(bug, dict) and 'text' in bug else str(bug)
            check_result = check_similar_bug_in_tracker(bug_text)
            print(f"   {i}. {check_result}")
            
            # Генерируем баг-репорт по шаблону
            timestamp_bug = datetime.now().strftime("%Y%m%d_%H%M%S")
            bug_report = generate_bug_report_via_openai(bug_text, i, timestamp_bug)
            
            # Сохраняем баг-репорт в файл
            bugreport_file = os.path.join('output', f'bugreport_{i}_{timestamp_bug}.md')
            with open(bugreport_file, 'w', encoding='utf-8') as f:
                f.write(bug_report)
            print(f"   Баг-репорт сохранен в {bugreport_file}")
            
            # Отправляем баг-репорт в Telegram
            if telegram_notifier:
                try:
                    response = telegram_notifier.send_bug_report(bug_report, i)
                    if response and response.get('ok'):
                        print(f"   📤 Баг-репорт #{i} отправлен в Telegram")
                    else:
                        print(f"   ❌ Ошибка отправки баг-репорта #{i} в Telegram")
                except Exception as e:
                    print(f"   ❌ Ошибка при отправке в Telegram: {str(e)}")
        
        # Создаем персоны и запускаем дискуссию о багах
        bug_personas = create_personas(
            classified_reviews['bug_reports']['raw'], 
            'bug_reports', 
            timestamp, 
            category
        )
        bug_discussion_file, bug_summary_file = run_category_discussion(
            bug_personas, 
            f"{item_name} (отчеты о багах)", 
            item_type,
            summary_type='bug_reports'
        )
        print(f"Обсуждение багов сохранено в файл: {bug_discussion_file}")
        print(f"Резюме обсуждения багов сохранено в файл: {bug_summary_file}")
        
        # Отправляем резюме дискуссии о багах в Telegram
        if telegram_notifier and bug_summary_file:
            try:
                with open(os.path.join('output', bug_summary_file), 'r', encoding='utf-8') as f:
                    summary_content = f.read()
                response = telegram_notifier.send_summary_report(summary_content, "bugs")
                if response and response.get('ok'):
                    print(f"   📤 Резюме дискуссии о багах отправлено в Telegram")
                else:
                    print(f"   ❌ Ошибка отправки резюме в Telegram")
            except Exception as e:
                print(f"   ❌ Ошибка при отправке резюме в Telegram: {str(e)}")
    else:
        print("Отчеты о багах не найдены")
        bug_discussion_file = None
        bug_summary_file = None

    # Шаг 5: Обработка запросов функций
    print("\n5. Обработка запросов новых функций...")
    if classified_reviews['feature_requests']['raw']:
        # Создаем список улучшений из запросов на функции
        improvements_from_features = []
        for i, feature in enumerate(classified_reviews['feature_requests']['raw'], 1):
            feature_text = feature['text'] if isinstance(feature, dict) and 'text' in feature else str(feature)
            improvements_from_features.append({
                "category": "feature_improvements",
                "title": f"Запрос на новую функцию #{i}",
                "description": feature_text,
                "priority": "medium"
            })
        
        # Анализируем улучшения на дубликаты
        if improvements_from_features:
            print("   Анализ предложений по улучшениям на дубликаты...")
            unique_improvements = find_duplicate_improvements(improvements_from_features)
            print(f"   После анализа осталось {len(unique_improvements)} уникальных предложений")
            
            # Создаем детальные планы реализации для каждого улучшения
            print("   Создание планов реализации...")
            timestamp_imp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Сохраняем уникальные улучшения в JSON-файл
            unique_improvements_file = os.path.join('output', f'unique_improvements_{timestamp_imp}.json')
            with open(unique_improvements_file, 'w', encoding='utf-8') as f:
                json.dump(unique_improvements, f, ensure_ascii=False, indent=2)
            print(f"   Уникальные улучшения сохранены в {unique_improvements_file}")
            
            # Создаем планы реализации для каждого улучшения
            for i, imp in enumerate(unique_improvements, 1):
                print(f"   Создание плана реализации для улучшения {i} из {len(unique_improvements)}...")
                proposal = generate_improvement_proposal(imp)
                
                # Сохраняем предложение в отдельный файл
                imp_title = imp.get('title', f'improvement_{i}').replace(' ', '_').lower()[:30]  # Ограничиваем длину
                proposal_file = os.path.join('output', f'improvement_proposal_{imp_title}_{timestamp_imp}.md')
                with open(proposal_file, 'w', encoding='utf-8') as f:
                    f.write(proposal)
                print(f"   Предложение сохранено в {proposal_file}")
        
        # Продолжаем обычный пайплайн с созданием персон и дискуссией
        feature_personas = create_personas(
            classified_reviews['feature_requests']['raw'], 
            'feature_requests', 
            timestamp, 
            category
        )
        feature_discussion_file, feature_summary_file = run_category_discussion(
            feature_personas, 
            f"{item_name} (запросы функций)", 
            item_type,
            summary_type='feature_requests'
        )
        print(f"Обсуждение запросов функций сохранено в файл: {feature_discussion_file}")
        print(f"Резюме обсуждения функций сохранено в файл: {feature_summary_file}")
        
        # Отправляем резюме дискуссии о функциях в Telegram
        if telegram_notifier and feature_summary_file:
            try:
                with open(os.path.join('output', feature_summary_file), 'r', encoding='utf-8') as f:
                    summary_content = f.read()
                response = telegram_notifier.send_summary_report(summary_content, "features")
                if response and response.get('ok'):
                    print(f"   📤 Резюме дискуссии о функциях отправлено в Telegram")
                else:
                    print(f"   ❌ Ошибка отправки резюме о функциях в Telegram")
            except Exception as e:
                print(f"   ❌ Ошибка при отправке резюме о функциях в Telegram: {str(e)}")
    else:
        print("Запросы новых функций не найдены")
        feature_discussion_file = None
        feature_summary_file = None

    # Шаг 6: Генерация финальных рекомендаций
    print("\n6. Генерация финальных рекомендаций...")
    recommendations_file = generate_recommendations(
        classified_reviews, bug_discussion_file, feature_discussion_file, bug_summary_file, feature_summary_file
    )
    
    print("\nАнализ завершен успешно!")
    print("\nСгенерированные файлы:")
    print(f"1. Отзывы: output/{reviews_file}")
    print(f"2. Классифицированные отзывы: output/{classified_file}")
    
    if bug_discussion_file:
        print(f"3. Обсуждение багов: output/{bug_discussion_file}")
    
    if feature_discussion_file:
        print(f"4. Обсуждение запросов функций: output/{feature_discussion_file}")
    
    if recommendations_file:
        print(f"5. Рекомендации: output/{recommendations_file}")

def analyze_reviews_topic(reviews):
    """Анализирует тему отзывов и определяет категорию товара/услуги и название
    
    Args:
        reviews: Список отзывов для анализа
        
    Returns:
        tuple: (category, item_type, item_name)
    """
    # Объединяем некоторые отзывы для анализа (не все, чтобы экономить токены)
    sample_reviews = reviews[:15]
    
    # Преобразуем словари в строки, если нужно
    review_texts = []
    for review in sample_reviews:
        if isinstance(review, dict) and 'text' in review:
            review_texts.append(review['text'])
        elif isinstance(review, str):
            review_texts.append(review)
    
    review_text = "\n\n".join(review_texts)
    
    # Ограничиваем длину текста
    if len(review_text) > 3000:
        review_text = review_text[:3000] + "..."
    
    prompt = f"""Проанализируй следующие отзывы о приложении и определи:
    1. Категорию приложения (например: health, lifestyle, productivity, social, и т.д.)
    2. Конкретный тип приложения (например: fitness tracker, meditation app, habit tracker и т.д.)
    3. Основное назначение приложения на основе отзывов
    
    Отзывы:
    {review_text}
    
    Верни ответ в формате JSON, строго следуя этой структуре:
    {{"category": "категория", "type": "тип_приложения", "name": "краткое_описание_назначения"}}
    """
    
    try:
        # Создаем клиент OpenAI с базовыми параметрами
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1"
        )
        
        # Делаем запрос к OpenAI для определения темы
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты - эксперт по анализу отзывов приложений. Всегда отвечай только в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Получаем ответ и преобразуем его в JSON
        result_text = response.choices[0].message.content.strip()
        
        # Извлекаем JSON из ответа (иногда модель может добавить лишний текст)
        import re
        json_pattern = r'\{.*\}'
        json_match = re.search(json_pattern, result_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
        else:
            # Запасной вариант, если регулярное выражение не сработало
            try:
                result = json.loads(result_text)
            except:
                # Если всё ещё ошибка, используем значения по умолчанию
                result = {"category": "app", "type": "health", "name": "Sober App"}
        
        print(f"Определена тема отзывов: категория '{result['category']}', тип '{result['type']}', назначение '{result['name']}'")
        return (result['category'], result['type'], result['name'])
        
    except Exception as e:
        print(f"Ошибка при определении темы отзывов: {str(e)}")
        # Возвращаем значения по умолчанию в случае ошибки
        return ("app", "health", "Sober App")

def create_personas(reviews, category_name, timestamp, app_category="app"):
    """Создает персоны на основе отзывов из конкретной категории
    
    Args:
        reviews: Список отзывов
        category_name: Название категории отзывов
        timestamp: Временная метка для именования файлов
        app_category: Категория приложения
        
    Returns:
        list: Список созданных персон
    """
    print(f"\nСоздание персон на основе отзывов из категории '{category_name}'...")
    
    # Создаем генератор персон
    persona_gen = PersonaGenerator()
    
    # Разбиваем отзывы на две части для создания разных персон
    mid = len(reviews) // 2
    reviews_part1 = reviews[:mid]
    reviews_part2 = reviews[mid:]
    
    # Проверяем, не слишком ли много отзывов для анализа
    max_reviews_per_part = 100
    if len(reviews_part1) > max_reviews_per_part:
        print(f"Слишком много отзывов ({len(reviews_part1)}), ограничиваем до {max_reviews_per_part}")
        reviews_part1 = reviews_part1[:max_reviews_per_part]
    
    if len(reviews_part2) > max_reviews_per_part:
        print(f"Слишком много отзывов ({len(reviews_part2)}), ограничиваем до {max_reviews_per_part}")
        reviews_part2 = reviews_part2[:max_reviews_per_part]
    
    # Обрабатываем каждую часть
    personas = []
    
    for part, part_reviews in enumerate([reviews_part1, reviews_part2], 1):
        print(f"Обработка части {part}...")
        
        # Ограничиваем длину текста отзывов
        max_text_length = 10000
        all_text = ""
        for review in part_reviews:
            if isinstance(review, dict) and 'text' in review:
                all_text += review['text'] + " "
        if len(all_text) > max_text_length:
            print(f"Текст отзывов слишком длинный ({len(all_text)} символов), обрезаем до {max_text_length}")
        
        # Генерируем персону на основе отзывов
        persona = persona_gen.generate_persona(part_reviews, category=app_category)
        if persona:
            personas.append({
                'category': category_name,
                'part': part,
                'based_on_reviews': len(part_reviews),
                'persona': persona
            })
        else:
            print(f"Не удалось сгенерировать персону для категории {category_name}, часть {part}")
    
    # Сохраняем персоны в файл
    personas_file = f"personas_{category_name}_{timestamp}.json"
    with open(os.path.join('output', personas_file), 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'category': category_name,
            'total_personas': len(personas),
            'personas': personas
        }, f, ensure_ascii=False, indent=4)
    
    print(f"Персоны для категории '{category_name}' сохранены в файл: {personas_file}")
    return personas

def run_category_discussion(personas, discussion_topic, item_type, summary_type=None):
    """Запускает групповую дискуссию для конкретной категории отзывов
    Args:
        personas: Список персон
        discussion_topic: Тема для обсуждения
        item_type: Тип объекта
        summary_type: Строка для типа резюме (например, 'bug_reports' или 'feature_requests')
    Returns:
        tuple: (имя файла дискуссии, имя файла резюме)
    """
    print(f"\nЗапуск групповой дискуссии по теме '{discussion_topic}'...")
    personas_for_discussion = [persona_data['persona'] for persona_data in personas]
    discussion_file = run_group_discussion(
        item_type=item_type,
        item_name=discussion_topic,
        custom_personas=personas_for_discussion
    )
    # Формируем имя файла для резюме
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if summary_type:
        summary_file = f"discussion_summary_{summary_type}_{timestamp}.txt"
    else:
        summary_file = f"discussion_summary_{timestamp}.txt"
    summarizer = DiscussionSummarizer()
    summary_file_actual = summarizer.summarize_discussion(file_path=discussion_file, output_file_name=summary_file)
    return discussion_file, summary_file_actual

def generate_recommendations(classified_reviews, bug_discussion_file, feature_discussion_file, bug_summary_file=None, feature_summary_file=None):
    """Генерирует итоговые рекомендации на основе всех анализов
    Args:
        classified_reviews: Классифицированные отзывы
        bug_discussion_file: Файл с дискуссией по багам
        feature_discussion_file: Файл с дискуссией по функциям
        bug_summary_file: Файл с резюме баг-дискуссии
        feature_summary_file: Файл с резюме фич-дискуссии
    Returns:
        str: Имя файла с рекомендациями
    """
    print("\nГенерация итоговых рекомендаций...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recommendations_file = f"recommendations_{timestamp}.json"
    analysis_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'bug_reports': {
            'count': len(classified_reviews['bug_reports']['raw']),
            'summarized': classified_reviews['bug_reports']['summarized']
        },
        'feature_requests': {
            'count': len(classified_reviews['feature_requests']['raw']),
            'summarized': classified_reviews['feature_requests']['summarized']
        },
        'appreciation': {
            'count': len(classified_reviews['appreciation']['raw'])
        }
    }
    if bug_summary_file:
        try:
            with open(os.path.join('output', bug_summary_file), 'r', encoding='utf-8') as f:
                bug_summary = f.read()
            analysis_data['bug_discussion_summary'] = bug_summary
        except Exception as e:
            print(f"Ошибка при чтении резюме дискуссии о багах: {str(e)}")
    if feature_summary_file:
        try:
            with open(os.path.join('output', feature_summary_file), 'r', encoding='utf-8') as f:
                feature_summary = f.read()
            analysis_data['feature_discussion_summary'] = feature_summary
        except Exception as e:
            print(f"Ошибка при чтении резюме дискуссии о функциях: {str(e)}")
    try:
        analyzer = Recommendations()
        result_file = analyzer.analyze_from_classified_data(analysis_data)
        if result_file:
            print(f"Рекомендации сохранены в файл: {result_file}")
        else:
            print("Не удалось сгенерировать рекомендации")
        return result_file
    except Exception as e:
        print(f"Ошибка при генерации рекомендаций: {str(e)}")
        return None

def check_similar_bug_in_tracker(bug_text):
    """Заглушка для проверки наличия похожего бага в баг-трекере (Jira, GitHub и т.д.)"""
    print(f"Проверка бага в баг-трекере: {bug_text[:60]}...")
    return "Похожий баг не найден"

def generate_bug_report_via_openai(bug_text, bug_index=None, timestamp=None):
    """Генерирует баг-репорт по шаблону через OpenAI API"""
    import openai
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""Разложи следующий баг по структуре баг-репорта:

1. Заголовок
2. Описание
3. Шаги для воспроизведения
4. Ожидаемый результат
5. Фактический результат
6. Окружение
7. Вложения
8. Дополнительно

Текст бага:
{bug_text}
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — опытный тестировщик ПО. Всегда отвечай строго по структуре баг-репорта."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800,
        )
        report = response.choices[0].message.content.strip()
    except Exception as e:
        report = f"Ошибка при генерации баг-репорта: {str(e)}\n\nТекст бага:\n{bug_text}"
    # Сохраняем баг-репорт в файл
    if not timestamp:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    idx = bug_index if bug_index is not None else 'X'
    filename = f"bugreport_{idx}_{timestamp}.md"
    with open(os.path.join('output', filename), 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Баг-репорт сохранён в файл: {filename}")
    return filename

def find_duplicate_improvements(improvements):
    """Анализирует предложения по улучшениям и находит дубликаты/похожие идеи через OpenAI
    
    Args:
        improvements: Список предложений по улучшениям
        
    Returns:
        list: Список уникальных предложений по улучшениям с объединенным описанием
    """
    import openai
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Формируем список улучшений для анализа
    improvements_text = ""
    for i, imp in enumerate(improvements, 1):
        imp_title = imp.get('title', 'Без названия')
        imp_desc = imp.get('description', 'Без описания')
        imp_category = imp.get('category', 'unknown')
        improvements_text += f"Улучшение {i} ({imp_category}): {imp_title}\n{imp_desc}\n\n"
    
    prompt = f"""Проанализируй следующие предложения по улучшению приложения и найди дубликаты или похожие идеи.
    Объедини похожие предложения, уточни формулировки и верни список уникальных идей.

    Для каждой идеи укажи:
    1. Категорию (feature_improvements, ux_improvements, stability_improvements и т.д.)
    2. Заголовок (краткое описание улучшения)
    3. Описание (подробное объяснение)
    4. Приоритет (high, medium, low)

    Вот список предложений:
    {improvements_text}

    Верни результат в формате JSON:
    [
      {{
        "category": "feature_improvements",
        "title": "Пример заголовка",
        "description": "Пример описания",
        "priority": "high"
      }},
      ...
    ]
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — аналитик по продуктовому менеджменту. Твоя задача — анализировать и объединять похожие предложения по улучшению продукта."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        
        result = response.choices[0].message.content.strip()
        
        # Извлекаем JSON из ответа
        import re
        import json
        
        json_pattern = r'\[.*\]'
        json_match = re.search(json_pattern, result, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            unique_improvements = json.loads(json_str)
        else:
            try:
                unique_improvements = json.loads(result)
            except:
                print("Не удалось извлечь JSON из ответа. Возвращаем исходный список улучшений.")
                unique_improvements = improvements
                
        return unique_improvements
        
    except Exception as e:
        print(f"Ошибка при анализе улучшений: {str(e)}")
        return improvements

def generate_improvement_proposal(improvement):
    """Генерирует детальное предложение по улучшению по заданному шаблону
    
    Args:
        improvement: Словарь с информацией об улучшении
        
    Returns:
        str: Заполненная форма предложения по улучшению
    """
    import openai
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Извлекаем информацию об улучшении
    imp_title = improvement.get('title', 'Без названия')
    imp_desc = improvement.get('description', 'Без описания')
    imp_category = improvement.get('category', 'unknown')
    imp_priority = improvement.get('priority', 'medium')
    
    # Формируем промпт для OpenAI
    template = """Шаблон для предложений по улучшению (Product Improvement Proposal)
1. Название предложения
Краткое, ёмкое название улучшения/фичи.

2. Категория
(Выбери одну или несколько: Feature, UX Improvement, Stability, Performance, Bug Fix)

3. Описание проблемы
В чём суть проблемы/неудобства для пользователя?

4. Предлагаемое решение
Что именно предлагается изменить/добавить?

5. Пользовательский эффект (User Impact)
Как это повлияет на пользователей?

6. Ожидаемый результат
Какой положительный эффект ожидается после внедрения?

7. Приоритет
(High/Medium/Low) - исходя из количества затронутых пользователей, важности для бизнеса.

8. Оценка сложности внедрения
(Оценка: Low/Medium/High, если есть понимание или предварительная экспертиза)

9. Примеры пользовательских отзывов (по желанию)
Цитаты или выдержки из реальных отзывов, подтверждающие проблему.

10. Дополнительные материалы
Скриншоты, ссылки, аналитика, если есть."""
    
    prompt = f"""Заполни шаблон предложения по улучшению на основе следующей информации:

Название: {imp_title}
Категория: {imp_category}
Описание: {imp_desc}
Приоритет: {imp_priority}

Вот шаблон, который нужно заполнить:

{template}

Дай развернутый, аргументированный ответ на основе предоставленной информации. Добавь логичные предположения, где информации недостаточно."""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — опытный продакт-менеджер. Твоя задача — создавать детальные предложения по улучшению продукта."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1200,
        )
        
        proposal = response.choices[0].message.content.strip()
        return proposal
        
    except Exception as e:
        print(f"Ошибка при генерации предложения по улучшению: {str(e)}")
        return f"Ошибка при генерации предложения: {str(e)}\n\nИсходные данные:\n{imp_title}\n{imp_desc}"

if __name__ == "__main__":
    # Проверяем наличие API ключа
    if not os.getenv("OPENAI_API_KEY"):
        print("Ошибка: OPENAI_API_KEY не найден в переменных окружения")
    else:
        asyncio.run(run_sober_analysis()) 