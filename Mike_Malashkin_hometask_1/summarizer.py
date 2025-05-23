import json
import os
import openai
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

class DiscussionSummarizer:
    def __init__(self):
        """Инициализация клиента OpenAI"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def get_latest_discussion_file(self):
        """Находит самый свежий файл с результатами дискуссии"""
        files = [f for f in os.listdir('output') if f.startswith("discussion_")]
        if not files:
            raise FileNotFoundError("Файл с результатами дискуссии не найден.")
        return max(files, key=lambda x: os.path.getctime(os.path.join('output', x)))
    
    def load_discussion_data(self, file_path=None):
        """Загружает данные дискуссии из файла"""
        if not file_path:
            file_path = self.get_latest_discussion_file()
        
        print(f"Загрузка данных дискуссии из файла: {file_path}")
        with open(os.path.join('output', file_path), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    def generate_abstractive_summary(self, discussion_data):
        """Генерирует абстрактное резюме дискуссии с ключевыми предложениями по улучшению"""
        # Собираем все высказывания из групповой дискуссии
        all_messages = []
        for message in discussion_data.get("group_discussion", []):
            # Добавляем имя агента к сообщению для лучшего понимания контекста
            agent_name = message.get("agent", "Unknown")
            content = message.get("content", "")
            all_messages.append(f"[{agent_name}]: {content}")
        
        # Объединяем все сообщения в одну строку для анализа
        full_discussion = "\n\n".join(all_messages)
        
        # Получаем тему дискуссии и название объекта
        topic = discussion_data.get("topic", "Критерии выбора")
        item_name = discussion_data.get("item_name", None)
        item_type = discussion_data.get("item_type", "объекта")
        
        # Определяем название объекта для промпта
        object_name = item_name if item_name and item_name.lower() != "none" else item_type
        
        # Формируем промпт
        system_prompt = "Ты - эксперт по анализу групповых дискуссий и выделению ключевых инсайтов для улучшения."
        prompt = f"""Проанализируй следующую групповую дискуссию на тему "{topic}" и 
        выдели 2-3 ключевых предложения по улучшению {object_name}.
        
        Особое внимание удели конкретным требованиям и аспектам {object_name}, упомянутым в дискуссии.
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
            print(f"Ошибка при генерации резюме: {str(e)}")
            return None
    
    def summarize_discussion(self, file_path=None, output_file_name=None):
        """Основной метод для резюмирования дискуссии
        output_file_name: если задан, использовать это имя файла для сохранения
        """
        # Загрузка данных
        data = self.load_discussion_data(file_path)
        
        # Генерация резюме
        print("Генерация абстрактного резюме дискуссии")
        summary = self.generate_abstractive_summary(data)
        
        if summary:
            # Сохранение результатов
            if output_file_name:
                output_file = output_file_name
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"discussion_summary_{timestamp}.txt"
            
            with open(os.path.join('output', output_file), "w", encoding="utf-8") as f:
                f.write(summary)
            
            print(f"Резюме сохранено в файл: {output_file}")
            
            # Также выводим результат в консоль
            print("\nРЕЗЮМЕ ДИСКУССИИ:")
            print(summary)
            
            return output_file
        
        return None

if __name__ == "__main__":
    # Пример использования
    summarizer = DiscussionSummarizer()
    summarizer.summarize_discussion() 