from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import re
import os

class ReviewScraper:
    def __init__(self):
        self.driver = None
        # Типичные классы и ID для блоков отзывов
        self.review_patterns = {
            'classes': [
                # Базовые классы для отзывов
                'review', 'reviews', 'comment', 'comments', 'feedback',
                'отзыв', 'отзывы', 'комментарий', 'комментарии', 'оценка',
                'product-reviews', 'customer-reviews', 'user-reviews',
                'review-item', 'review-content', 'review-text',
                'feedback-item', 'feedback-content',
                
                # Дополнительные селекторы для отзывов
                'product-review-item',
                'customer-feedback',
                'user-comment',
                'review-section__item',
                'review-block',
                'review-card',
                'testimonial',
                'testimonial-item',
                'feedback-block',
                'comment-block',
                'review-container',
                'review-wrapper',
                'review-box',
                'review-entry',
                'product-comment',
                'customer-review-item',
                'review-list-item',
                'feedback-list-item',
                'comment-list-item',
                'review-body',
                'review-content-wrapper',
                'review-text-content',
                'comment-text-content',
                'feedback-text-content',
                'review-message',
                'comment-message',
                'feedback-message',
                'review-description',
                'comment-description',
                'feedback-description',
                
                # Селекторы для рейтингов и оценок
                'rating-container',
                'star-rating',
                'rating-wrapper',
                'rating-box',
                'rating-stars',
                'rating-value',
                'review-rating',
                'product-rating',
                'user-rating',
                
                # Селекторы для метаданных отзыва
                'review-meta',
                'review-author',
                'review-date',
                'review-info',
                'review-details',
                'review-header',
                'review-footer',
                'author-info',
                'review-metadata',
                'review-timestamp',
                
                # Селекторы для специфических частей отзыва
                'review-pros',
                'review-cons',
                'review-advantages',
                'review-disadvantages',
                'review-pluses',
                'review-minuses',
                'review-positive',
                'review-negative',
                'review-summary',
                'review-verdict'
            ],
            'ids': [
                # Базовые ID
                'reviews', 'comments', 'feedback',
                'product-reviews', 'customer-reviews',
                'review-section', 'reviews-section',
                'отзывы', 'комментарии',
                
                # Дополнительные ID
                'reviewsContainer',
                'reviewsList',
                'reviewsBlock',
                'customerReviews',
                'productReviews',
                'userReviews',
                'reviewsTab',
                'commentsTab',
                'feedbackTab',
                'reviewsContent',
                'reviewsWrapper',
                'reviewsPanel',
                'reviewsArea',
                'reviewsRegion',
                'reviewsZone',
                'reviewsFeed',
                'reviewsStream',
                'reviewsCollection',
                'reviewsGroup',
                'reviewsSet'
            ],
            'angular_selectors': [
                # Angular компоненты
                'review-item',
                'review-list',
                'review-card',
                'review-container',
                'review-block',
                'rating-stars',
                'rating-bar',
                'review-text',
                'review-header',
                'review-footer',
                
                # Angular атрибуты
                '[_nghost-ng-c2238975015]',
                '[_ngcontent-ng-c2238975015]',
                '[ng-repeat="review in reviews"]',
                '[ng-repeat="comment in comments"]',
                '[ng-repeat="feedback in feedbacks"]',
                '[ng-if="review"]',
                '[ng-if="hasReviews"]',
                '[ng-show="showReviews"]',
                '[ng-class="reviewClass"]',
                '[data-review]'
            ],
            'data_attributes': [
                # Data атрибуты
                '[data-review]',
                '[data-review-id]',
                '[data-review-type]',
                '[data-review-author]',
                '[data-review-date]',
                '[data-review-rating]',
                '[data-review-text]',
                '[data-review-title]',
                '[data-comment]',
                '[data-feedback]',
                '[data-testimonial]',
                '[data-rating]',
                '[data-stars]',
                '[data-score]',
                '[data-review-section]',
                '[data-review-block]',
                '[data-review-container]',
                '[data-review-wrapper]',
                '[data-review-content]',
                '[data-review-body]'
            ]
        }
    
    def setup_driver(self):
        """Setup Chrome driver with necessary options"""
        if self.driver is not None:
            return
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            # Пытаемся установить ChromeDriver через ChromeDriverManager
            chrome_driver_path = ChromeDriverManager().install()
            print(f"ChromeDriver path: {chrome_driver_path}")
            
            # Устанавливаем права на исполнение
            if os.path.exists(chrome_driver_path):
                os.chmod(chrome_driver_path, 0o755)
                print(f"Установлены права на исполнение для ChromeDriver")
            
            service = Service(chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"Ошибка при установке ChromeDriver: {str(e)}")
            # Пробуем использовать встроенный драйвер
            try:
                print("Пробуем использовать альтернативный метод...")
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"Не удалось инициализировать ChromeDriver: {str(e2)}")
                raise
    
    def cleanup(self):
        """Cleanup browser resources"""
        if self.driver:
            try:
                self.driver.quit()
            finally:
                self.driver = None
    
    def scroll_page(self):
        """Scroll page to bottom with 500px steps"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Прокручиваем на 500 пикселей вниз
            self.driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(1)  # Ждем загрузку контента
            
            # Получаем новую высоту страницы
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Если высота не изменилась, значит достигли конца страницы
            if new_height == last_height:
                break
                
            last_height = new_height

    def extract_reviews_from_schema(self, soup):
        """Extract reviews from schema.org markup"""
        reviews = []
        
        # Поиск по разметке schema.org
        schema_scripts = soup.find_all('script', type='application/ld+json')
        for script in schema_scripts:
            try:
                data = json.loads(script.string)
                # Ищем отзывы в различных форматах schema.org
                if isinstance(data, dict):
                    reviews.extend(self._extract_reviews_from_dict(data))
            except:
                continue
                
        return reviews
    
    def _extract_reviews_from_dict(self, data):
        """Recursively extract reviews from dictionary"""
        reviews = []
        
        if isinstance(data, dict):
            # Проверяем наличие отзывов в текущем объекте
            if data.get('@type') in ['Review', 'UserReview', 'ProductReview']:
                review = {
                    'text': data.get('reviewBody', data.get('description', '')),
                    'rating': data.get('reviewRating', {}).get('ratingValue', None),
                    'author': data.get('author', {}).get('name', None),
                    'date': data.get('datePublished', None)
                }
                if review['text']:
                    reviews.append(review)
            
            # Рекурсивно ищем в значениях
            for value in data.values():
                if isinstance(value, (dict, list)):
                    reviews.extend(self._extract_reviews_from_dict(value))
        elif isinstance(data, list):
            # Рекурсивно ищем в списках
            for item in data:
                if isinstance(item, (dict, list)):
                    reviews.extend(self._extract_reviews_from_dict(item))
                    
        return reviews

    def extract_angular_reviews(self, soup):
        """Extract reviews from Angular-specific markup"""
        reviews = []
        
        # Поиск review-item элементов
        review_items = soup.find_all(['review-item', 'div'], class_='ng-star-inserted')
        
        for item in review_items:
            review_data = {}
            
            # Извлекаем имя автора и дату
            head = item.find('div', class_='head')
            if head:
                author_div = head.find('div')
                if author_div:
                    author_text = author_div.get_text(strip=True).split('\n')[0]
                    review_data['author'] = author_text
                    
                    date_span = author_div.find('span')
                    if date_span:
                        review_data['date'] = date_span.get_text(strip=True)
            
            # Извлекаем рейтинг
            rating_bar = item.find('rating-bar')
            if rating_bar:
                actual_div = rating_bar.find('div', class_='actual')
                if actual_div:
                    # Получаем ширину в процентах и конвертируем в оценку
                    width_style = actual_div.get('style', '')
                    width_match = re.search(r'width:\s*(\d+)%', width_style)
                    if width_match:
                        width_percent = int(width_match.group(1))
                        review_data['rating'] = round(width_percent / 20)  # 100% = 5 звезд
            
            # Извлекаем текст отзыва
            text_content = []
            
            # Ищем блоки с текстом
            text_blocks = item.find_all('div', class_='text-content')
            for block in text_blocks:
                sections = block.find_all('div', class_='ng-star-inserted')
                for section in sections:
                    # Находим заголовок секции (Достоинства/Недостатки/Комментарий)
                    title = section.find('p')
                    content = section.get_text(strip=True)
                    if title:
                        title_text = title.get_text(strip=True)
                        content = content.replace(title_text, '').strip()
                        text_content.append(f"{title_text}: {content}")
                    else:
                        text_content.append(content)
            
            if text_content:
                review_data['text'] = ' | '.join(text_content)
                reviews.append(review_data)
        
        return reviews

    def extract_reviews_by_patterns(self, soup):
        """Extract reviews using common patterns"""
        reviews = []
        
        # Поиск по классам
        for class_name in self.review_patterns['classes']:
            elements = soup.find_all(class_=re.compile(class_name, re.I))
            for element in elements:
                review_text = self._extract_review_text(element)
                if review_text:
                    reviews.append({'text': review_text})
        
        # Поиск по ID
        for id_name in self.review_patterns['ids']:
            elements = soup.find_all(id=re.compile(id_name, re.I))
            for element in elements:
                review_text = self._extract_review_text(element)
                if review_text:
                    reviews.append({'text': review_text})
        
        return reviews
    
    def _extract_review_text(self, element):
        """Extract clean review text from element"""
        # Удаляем скрипты и стили
        for script in element.find_all(['script', 'style']):
            script.decompose()
        
        # Получаем текст
        text = element.get_text(strip=True)
        
        # Очищаем текст
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Проверяем минимальную длину и наличие осмысленного текста
        if len(text) > 10 and any(char.isalpha() for char in text):
            return text
        return None

    def get_reviews(self, url=None):
        """Get reviews from specified URL or return None if URL is not provided"""
        if not url:
            return None
            
        try:
            # Инициализируем драйвер при первом использовании
            self.setup_driver()
            
            # Открываем страницу
            self.driver.get(url)
            
            # Ждем 3 секунды для загрузки начального контента
            time.sleep(3)
            
            # Прокручиваем страницу до конца
            self.scroll_page()
            
            # Получаем содержимое body
            body_content = self.driver.find_element(By.TAG_NAME, "body").get_attribute('innerHTML')
            
            # Создаем объект BeautifulSoup для парсинга
            soup = BeautifulSoup(body_content, 'html.parser')
            
            # Извлекаем отзывы разными методами
            schema_reviews = self.extract_reviews_from_schema(soup)
            pattern_reviews = self.extract_reviews_by_patterns(soup)
            angular_reviews = self.extract_angular_reviews(soup)
            
            # Объединяем результаты
            all_reviews = schema_reviews + pattern_reviews + angular_reviews
            
            # Удаляем дубликаты
            unique_reviews = []
            seen_texts = set()
            for review in all_reviews:
                text = review.get('text', '')
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    unique_reviews.append(review)
            
            # Формируем структуру данных для сохранения
            result = {
                "url": url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reviews_count": len(unique_reviews),
                "reviews": unique_reviews
            }
            
            return result
            
        except Exception as e:
            print(f"Error while scraping reviews: {str(e)}")
            # При ошибке закрываем драйвер для переинициализации при следующей попытке
            self.cleanup()
            return None
            
    def __del__(self):
        """Destructor to ensure browser cleanup"""
        self.cleanup() 