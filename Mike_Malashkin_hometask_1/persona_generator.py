import json
import os
import openai
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class PersonaGenerator:
    def __init__(self):
        """Инициализация клиента OpenAI"""
        # Старая версия OpenAI имеет другую инициализацию
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def generate_persona(self, reviews, category=None):
        """Генерирует персону на основе отзывов
        
        Args:
            reviews: Список отзывов для анализа
            category: Категория объекта отзывов (может быть None, тогда будет определена автоматически)
        """
        # Ограничиваем количество отзывов для избежания превышения лимита токенов
        if len(reviews) > 100:
            print(f"Слишком много отзывов ({len(reviews)}), ограничиваем до 100")
            reviews = reviews[:100]
            
        # Преобразуем словари в строки, если нужно
        review_texts = []
        for review in reviews:
            if isinstance(review, dict) and 'text' in review:
                review_texts.append(f"Отзыв: {review['text']}")
            elif isinstance(review, str):
                review_texts.append(f"Отзыв: {review}")
            
        # Объединяем все отзывы в один текст
        reviews_text = "\n\n".join(review_texts)
        
        # Если текст слишком длинный, обрезаем его
        if len(reviews_text) > 10000:
            print(f"Текст отзывов слишком длинный ({len(reviews_text)} символов), обрезаем до 10000")
            reviews_text = reviews_text[:10000] + "..."
        
        # Автоматически определяем категорию, если не задана
        if category is None:
            # Берем малую выборку отзывов для быстрого анализа
            sample_reviews = reviews[:5]
            sample_text = "\n\n".join(sample_reviews)
            
            # Ограничиваем длину текста
            if len(sample_text) > 1000:
                sample_text = sample_text[:1000] + "..."
            
            # Запрос к API для определения категории
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты - эксперт по анализу отзывов. Определи категорию объекта отзывов."},
                        {"role": "user", "content": f"На основе этих отзывов, определи основную категорию объекта отзывов. Отвечай одним словом.\n\n{sample_text}"}
                    ],
                    temperature=0.3,
                    max_tokens=20,
                )
                category = response.choices[0].message.content.strip().lower()
                print(f"Автоматически определена категория объекта: {category}")
            except Exception as e:
                print(f"Ошибка при автоматическом определении категории объекта: {str(e)}")
                category = "unknown"  # значение по умолчанию
        
        # Формируем универсальный промпт для любого типа объекта отзывов
        prompt = f"""На основе следующих отзывов, создай детальный портрет типичного потребителя/пользователя.
        
        Включи в описание:
        1. Демографические характеристики (возраст, пол, социальный статус, если применимо)
        2. Ключевые потребности и болевые точки
        3. Критерии выбора и оценки
        4. Предпочтения в использовании
        5. Ожидания и требования
        
        Отзывы:
        {reviews_text}
        
        Создай подробное описание персоны, которое отражает общие характеристики и потребности, 
        выявленные из анализа отзывов. Адаптируй описание к типу объекта отзывов."""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты - эксперт по анализу потребительского поведения и созданию портретов целевой аудитории."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Ошибка при генерации персоны: {str(e)}")
            return None

    def generate_reviews_summary(self, reviews):
        """Генерирует краткую сводку отзывов с помощью OpenAI API"""
        # Извлекаем только текст отзывов
        reviews_text = []
        for review in reviews:
            if isinstance(review, dict) and 'text' in review:
                text = review.get('text', '')
                if text and not text.startswith('Комментарий:') and not text.startswith('Отзывы') and not text.startswith('Срок использования:'):
                    reviews_text.append(text)
            elif isinstance(review, str):
                if not review.startswith('Комментарий:') and not review.startswith('Отзывы') and not review.startswith('Срок использования:'):
                    reviews_text.append(review)
        
        # Формируем промпт для OpenAI
        prompt = f"""Проанализируй следующие отзывы и создай краткое саммари, 
        которое описывает основные тенденции в отзывах, включая:
        - Общее впечатление пользователей
        - Основные положительные моменты
        - Основные отрицательные моменты
        - Часто упоминаемые характеристики объекта отзывов

        Отзывы для анализа:
        {' | '.join(reviews_text)}

        Ответ должен быть в виде связного текста на русском языке, без заголовков и списков.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - эксперт по анализу отзывов. Твоя задача - создавать четкие и информативные обзоры на основе отзывов."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Ошибка при генерации сводки: {str(e)}")
            return None

    def process_reviews_batch(self, reviews_file, batch_size=15):
        """Обрабатывает отзывы группами и генерирует персоны"""
        # Загружаем отзывы
        with open(reviews_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        personas = []
        persona_number = 1
        
        # Обрабатываем отзывы по каждому сайту
        for site_name, site_data in data['sites'].items():
            reviews = site_data['reviews']
            
            # Разбиваем отзывы на группы по batch_size
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                
                # Генерируем персону для текущей группы отзывов
                persona = self.generate_persona(batch)
                if persona:
                    personas.append({
                        'persona_number': persona_number,
                        'site': site_name,
                        'reviews_range': f"{i+1}-{min(i+batch_size, len(reviews))}",
                        'persona': persona
                    })
                    persona_number += 1
        
        # Сохраняем результаты
        if personas:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"personas_{timestamp}.json"
            
            result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_personas': len(personas),
                'personas': personas
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            print(f"\nСгенерировано {len(personas)} персон")
            print(f"Результаты сохранены в: {output_file}")
            
        return personas

if __name__ == "__main__":
    # Пример использования
    generator = PersonaGenerator()
    generator.process_reviews_batch("output/reviews_latest.json") 