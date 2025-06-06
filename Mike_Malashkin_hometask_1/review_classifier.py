import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class ReviewClassifier:
    """Класс для классификации отзывов на категории: баги, запросы функций и благодарности"""
    
    def __init__(self):
        """Инициализация классификатора"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Инициализируем клиент OpenAI с базовыми параметрами
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url="https://api.openai.com/v1"
        )
    
    def classify_reviews(self, reviews):
        """Классифицирует отзывы на три категории
        
        Args:
            reviews: Список отзывов для классификации
            
        Returns:
            dict: Словарь с классифицированными отзывами
        """
        print("Классифицируем отзывы на категории...")
        
        # Инициализируем результат
        result = {
            'bug_reports': [],
            'feature_requests': [],
            'appreciation': []
        }
        
        # Обрабатываем каждый отзыв
        for idx, review in enumerate(reviews):
            if idx % 20 == 0:
                print(f"Обработано {idx}/{len(reviews)} отзывов...")
            
            # Извлекаем текст отзыва
            if isinstance(review, dict) and 'text' in review:
                review_text = review['text']
            elif isinstance(review, str):
                review_text = review
            else:
                print(f"Пропускаем отзыв {idx}: неизвестный формат")
                continue
            
            # Пропускаем слишком короткие отзывы
            if len(review_text.strip()) < 5:
                continue
            
            # Классифицируем отзыв
            category = self._classify_single_review(review_text)
            
            # Добавляем отзыв в соответствующую категорию
            if category == 'bug_report':
                result['bug_reports'].append(review)
            elif category == 'feature_request':
                result['feature_requests'].append(review)
            elif category == 'appreciation':
                result['appreciation'].append(review)
        
        print(f"Классификация завершена. Баги: {len(result['bug_reports'])}, "
              f"Запросы функций: {len(result['feature_requests'])}, "
              f"Благодарности: {len(result['appreciation'])}")
        
        return result
    
    def _classify_single_review(self, review_text):
        """Классифицирует один отзыв с помощью OpenAI API
        
        Args:
            review_text: Текст отзыва
            
        Returns:
            str: Категория отзыва (bug_report, feature_request, appreciation)
        """
        # Ограничиваем длину текста
        if len(review_text) > 500:
            review_text = review_text[:500] + "..."
        
        # Запрос к модели
        prompt = f"""Определи тип отзыва пользователя о приложении, выбрав одну из трех категорий:
1. bug_report - отчет о баге или проблеме в приложении
2. feature_request - запрос новой функции или улучшения
3. appreciation - благодарность, положительный отзыв без конкретных предложений

Отзыв: "{review_text}"

Ответь только одним словом: bug_report, feature_request или appreciation.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - система классификации отзывов о приложении."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            # Получаем ответ и очищаем от лишних символов
            result = response.choices[0].message.content.strip().lower()
            
            # Проверяем, что ответ соответствует одной из категорий
            if 'bug' in result or 'report' in result:
                return 'bug_report'
            elif 'feature' in result or 'request' in result:
                return 'feature_request'
            elif 'appreciation' in result or 'thanks' in result or 'positive' in result:
                return 'appreciation'
            else:
                # По умолчанию относим к благодарностям, если не удалось классифицировать
                return 'appreciation'
            
        except Exception as e:
            print(f"Ошибка при классификации отзыва: {str(e)}")
            # В случае ошибки относим к благодарностям (наименее критичная категория)
            return 'appreciation'
    
    def summarize_similar_reviews(self, reviews, category_name):
        """Суммаризирует похожие отзывы в рамках одной категории
        
        Args:
            reviews: Список отзывов для суммаризации
            category_name: Название категории (для контекста)
            
        Returns:
            list: Список суммаризированных групп отзывов
        """
        if not reviews:
            return []
        
        print(f"Суммаризируем похожие отзывы в категории '{category_name}'...")
        
        # Если отзывов мало, не выполняем суммаризацию
        if len(reviews) < 3:
            return reviews
        
        # Для больших списков разбиваем на подгруппы по 50 отзывов
        groups = []
        for i in range(0, len(reviews), 50):
            batch = reviews[i:i+50]
            
            # Собираем тексты отзывов
            review_texts = []
            for review in batch:
                if isinstance(review, dict) and 'text' in review:
                    review_texts.append(review['text'])
                elif isinstance(review, str):
                    review_texts.append(review)
            
            # Ограничиваем общую длину текста
            combined_text = "\n\n".join(review_texts)
            if len(combined_text) > 3000:
                combined_text = combined_text[:3000] + "..."
            
            # Запрос к модели для группировки похожих отзывов
            prompt = f"""Ниже приведен список отзывов о приложении из категории '{category_name}'. 
Сгруппируй похожие отзывы и создай краткое резюме для каждой группы.

Отзывы:
{combined_text}

Формат ответа: список групп отзывов в формате JSON:
[
  {{
    "group_name": "Название группы",
    "count": количество_отзывов_в_группе,
    "summary": "Краткое описание проблемы/запроса/благодарности"
  }},
  ...
]
"""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Ты - эксперт по анализу отзывов. Твоя задача - найти закономерности и сгруппировать похожие отзывы."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=1000
                )
                
                # Извлекаем JSON из ответа
                import re
                json_pattern = r'\[.*\]'
                json_match = re.search(json_pattern, response.choices[0].message.content, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        grouped_reviews = json.loads(json_str)
                        groups.extend(grouped_reviews)
                    except json.JSONDecodeError:
                        print(f"Ошибка при парсинге JSON для подгруппы {i//50 + 1}")
                        continue
                else:
                    print(f"Не удалось извлечь JSON для подгруппы {i//50 + 1}")
            
            except Exception as e:
                print(f"Ошибка при суммаризации отзывов: {str(e)}")
        
        print(f"Суммаризация завершена. Получено {len(groups)} групп похожих отзывов.")
        return groups
    
    def process_reviews(self, reviews):
        """Полная обработка отзывов: классификация и суммаризация
        
        Args:
            reviews: Список отзывов для обработки
            
        Returns:
            dict: Результаты обработки
        """
        # Классифицируем отзывы
        classified = self.classify_reviews(reviews)
        
        # Суммаризируем похожие отзывы в каждой категории
        result = {
            'bug_reports': {
                'raw': classified['bug_reports'],
                'summarized': self.summarize_similar_reviews(classified['bug_reports'], 'bug_reports')
            },
            'feature_requests': {
                'raw': classified['feature_requests'],
                'summarized': self.summarize_similar_reviews(classified['feature_requests'], 'feature_requests')
            },
            'appreciation': {
                'raw': classified['appreciation'],
                'summarized': [] # Для благодарностей не делаем суммаризацию
            }
        }
        
        return result 