import json
import os
import openai
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

class Recommendations:
    def __init__(self):
        """Инициализация клиента OpenAI"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        # Старая версия OpenAI имеет другую инициализацию
        openai.api_key = api_key
    
    def get_latest_discussion_file(self):
        """Находит самый свежий файл с результатами дискуссии"""
        files = [f for f in os.listdir('output') if f.startswith("discussion_")]
        if not files:
            raise FileNotFoundError("Файл с результатами дискуссии не найден")
        return max(files, key=lambda x: os.path.getctime(os.path.join('output', x)))
    
    def load_discussion_data(self, file_path=None):
        """Загружает данные дискуссии из файла"""
        if not file_path:
            file_path = self.get_latest_discussion_file()
        
        print(f"Загрузка данных дискуссии из файла: {file_path}")
        try:
            with open(os.path.join('output', file_path), "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Ошибка при загрузке файла: {str(e)}")
            return None
    
    def generate_improvements(self, discussion_data):
        """Генерирует рекомендации по улучшению на основе дискуссии"""
        if not discussion_data:
            print("Нет данных для анализа")
            return None
            
        # Собираем все высказывания из групповой дискуссии
        all_messages = []
        for message in discussion_data.get("group_discussion", []):
            # Добавляем имя агента к сообщению для лучшего понимания контекста
            agent_name = message.get("agent", "Unknown")
            content = message.get("content", "")
            all_messages.append(f"[{agent_name}]: {content}")
        
        if not all_messages:
            print("В дискуссии нет сообщений для анализа")
            return None
        
        # Объединяем все сообщения в одну строку для анализа
        full_discussion = "\n\n".join(all_messages)
        
        # Определяем тип объекта и его название
        item_type = discussion_data.get("item_type", "unknown")
        topic = discussion_data.get("topic", "Критерии выбора")
        item_name = discussion_data.get("item_name", None)
        
        # Используем имя объекта или его тип, если имя не задано
        object_name = item_name if item_name and item_name.lower() != "none" else item_type
        
        # Формируем универсальный промпт
        system_prompt = "Ты - эксперт по анализу групповых дискуссий и выделению ключевых инсайтов для улучшения"
        prompt = f"""Проанализируй следующую групповую дискуссию на тему "{topic}" и 
        выдели 2-3 ключевых предложения по улучшению {object_name}.
        
        Особое внимание удели конкретным требованиям и аспектам, упомянутым в дискуссии.
        Выдели только самые значимые и повторяющиеся мнения участников дискуссии.
        
        Твой ответ должен быть в формате:
        
        КЛЮЧЕВЫЕ ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:
        1. [Первое предложение]
        2. [Второе предложение]
        3. [Третье предложение, если есть]
        
        Дискуссия:
        {full_discussion}
        """
        
        # Отправляем запрос к OpenAI
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при генерации рекомендаций: {str(e)}")
            return None
    
    def analyze_discussion(self, file_path=None):
        """Основной метод для анализа дискуссии и генерации рекомендаций"""
        try:
            # Загрузка данных
            data = self.load_discussion_data(file_path)
            if not data:
                return None
            
            # Получаем тип объекта
            item_type = data.get("item_type", "unknown")
            item_name = data.get("item_name", "объекта")
            
            # Определяем название объекта для вывода
            display_name = item_name if item_name and item_name.lower() != "none" else item_type
            
            # Генерация рекомендаций
            print(f"Генерация рекомендаций по улучшению: {display_name}")
            improvements = self.generate_improvements(data)
            
            if improvements:
                # Сохранение результатов
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"improvements_{timestamp}.txt"
                
                with open(os.path.join('output', output_file), "w", encoding="utf-8") as f:
                    f.write(improvements)
                
                print(f"Рекомендации сохранены в файл: {output_file}")
                
                # Также выводим результат в консоль
                print("\nРЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
                print(improvements)
                
                return output_file
            
            return None
            
        except Exception as e:
            print(f"Ошибка при анализе дискуссии: {str(e)}")
            return None

if __name__ == "__main__":
    # Пример использования
    analyzer = Recommendations()
    analyzer.analyze_discussion() 