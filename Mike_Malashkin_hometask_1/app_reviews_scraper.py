import json
import os
import requests
from datetime import datetime, timedelta
from google_play_scraper import Sort, reviews_all, reviews, app
import time

class AppReviewsScraper:
    """Класс для сбора отзывов из Google Play Market"""
    
    def __init__(self):
        """Инициализация скрапера"""
        # Создаем папку output, если она не существует
        os.makedirs('output', exist_ok=True)
    
    def get_google_play_reviews(self, app_id, lang='en', country='us', months=12):
        """Собирает отзывы из Google Play Market
        
        Args:
            app_id: Идентификатор приложения в Google Play (например, 'com.example.app')
            lang: Язык отзывов
            country: Страна
            months: Количество месяцев, за которые нужно собрать отзывы
            
        Returns:
            list: Список отзывов
        """
        print(f"Сбор отзывов из Google Play для {app_id}...")
        
        # Определяем дату, до которой собираем отзывы
        date_cutoff = datetime.now() - timedelta(days=30 * months)
        
        try:
            # Сначала получаем информацию о приложении
            app_info = app(
                app_id,
                lang=lang,
                country=country
            )
            
            print(f"Приложение: {app_info['title']}")
            print(f"Рейтинг: {app_info['score']}")
            
            # Собираем все отзывы
            result, continuation_token = reviews(
                app_id,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=100  # Начнем с небольшого количества отзывов
            )
            
            all_reviews = []
            all_reviews.extend(result)
            
            # Добавляем отзывы порциями, пока не достигнем временной границы или максимального количества
            while continuation_token and len(all_reviews) < 1000 and (not all_reviews or all_reviews[-1]['at'] > date_cutoff):
                print(f"Собрано отзывов: {len(all_reviews)}, продолжаем...")
                result, continuation_token = reviews(
                    app_id,
                    continuation_token=continuation_token,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=100
                )
                
                # Проверяем, что получили новые отзывы
                if not result:
                    break
                    
                all_reviews.extend(result)
                
                # Добавляем паузу, чтобы не перегружать сервер
                time.sleep(1)
            
            # Фильтруем отзывы по дате
            filtered_reviews = [review for review in all_reviews if review['at'] > date_cutoff]
            
            print(f"Собрано отзывов из Google Play: {len(filtered_reviews)}")
            
            # Преобразуем в нужный формат
            formatted_reviews = []
            for review in filtered_reviews:
                formatted_reviews.append({
                    'text': review['content'],
                    'rating': review['score'],
                    'date': review['at'].strftime("%Y-%m-%d"),
                    'source': 'Google Play',
                    'version': review.get('version', ''),
                    'id': review['reviewId']
                })
            
            return formatted_reviews
            
        except Exception as e:
            print(f"Ошибка при сборе отзывов из Google Play: {str(e)}")
            return []
    
    def get_app_reviews(self, app_name, google_play_id, months=12):
        """Собирает отзывы из Google Play
        
        Args:
            app_name: Название приложения
            google_play_id: Идентификатор в Google Play
            months: Количество месяцев, за которые нужно собрать отзывы
            
        Returns:
            dict: Результаты сбора отзывов
        """
        results = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'app_name': app_name,
            'period_months': months,
            'sites': {}
        }
        
        # Собираем отзывы из Google Play
        if google_play_id:
            # Собираем отзывы на английском (основной язык приложения)
            google_play_reviews = self.get_google_play_reviews(
                app_id=google_play_id,
                lang='en',
                country='us',
                months=months
            )
            
            if google_play_reviews:
                results['sites']['google_play'] = {
                    'total_reviews': len(google_play_reviews),
                    'reviews': google_play_reviews
                }
        
        return results
    
    def save_reviews(self, reviews_data):
        """Сохраняет собранные отзывы в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"app_reviews_{timestamp}.json"
        filepath = os.path.join('output', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(reviews_data, f, ensure_ascii=False, indent=2)
        
        print(f"Отзывы сохранены в файл: {filepath}")
        return filename

# Пример использования
if __name__ == "__main__":
    # Инициализируем скрапер
    scraper = AppReviewsScraper()
    
    # Параметры для приложения Sober
    APP_NAME = "Sober"
    GOOGLE_PLAY_ID = "com.osu.cleanandsobertoolboxandroid"  # Корректный ID (подтвержденный из поиска)
    MONTHS = 12  # Собираем отзывы за последние 12 месяцев (1 год)
    
    # Собираем отзывы только из Google Play
    reviews_data = scraper.get_app_reviews(
        app_name=APP_NAME,
        google_play_id=GOOGLE_PLAY_ID,
        months=MONTHS
    )
    
    # Сохраняем отзывы
    scraper.save_reviews(reviews_data) 