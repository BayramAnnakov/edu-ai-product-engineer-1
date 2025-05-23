import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram через Bot API"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") 
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID не найден в переменных окружения")
    
    def send_message(self, text, parse_mode="Markdown"):
        """Отправляет текстовое сообщение в Telegram
        
        Args:
            text (str): Текст сообщения
            parse_mode (str): Режим парсинга (Markdown или HTML)
            
        Returns:
            dict: Ответ от Telegram API
        """
        url = f"{self.base_url}/sendMessage"
        
        # Ограничиваем длину сообщения (Telegram лимит 4096 символов)
        if len(text) > 4000:
            text = text[:3900] + "\n\n... (сообщение обрезано)"
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
            return None
    
    def send_bug_report(self, bug_report_content, bug_index=None):
        """Отправляет баг-репорт в Telegram с красивым форматированием
        
        Args:
            bug_report_content (str): Содержимое баг-репорта
            bug_index (int): Номер бага
            
        Returns:
            dict: Ответ от Telegram API
        """
        # Форматируем заголовок
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bug_num = f"#{bug_index}" if bug_index else ""
        
        header = f"🐛 *Новый баг-репорт {bug_num}*\n"
        header += f"📅 {timestamp}\n"
        header += "─" * 30 + "\n\n"
        
        # Форматируем содержимое для Markdown
        formatted_content = self._format_bug_report_for_telegram(bug_report_content)
        
        message = header + formatted_content
        
        return self.send_message(message)
    
    def send_file(self, file_path, caption=""):
        """Отправляет файл в Telegram
        
        Args:
            file_path (str): Путь к файлу
            caption (str): Подпись к файлу
            
        Returns:
            dict: Ответ от Telegram API
        """
        url = f"{self.base_url}/sendDocument"
        
        try:
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption
                }
                
                response = requests.post(url, files=files, data=data, timeout=60)
                response.raise_for_status()
                return response.json()
        except (requests.exceptions.RequestException, FileNotFoundError) as e:
            print(f"Ошибка при отправке файла в Telegram: {str(e)}")
            return None
    
    def _format_bug_report_for_telegram(self, content):
        """Форматирует баг-репорт для отображения в Telegram"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue
                
            # Заголовки секций делаем жирными
            if any(keyword in line.lower() for keyword in ['заголовок', 'описание', 'шаги', 'ожидаемый', 'фактический', 'окружение']):
                formatted_lines.append(f"*{line}*")
            # Нумерованные списки
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted_lines.append(f"• {line}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def send_summary_report(self, summary_content, report_type="summary"):
        """Отправляет резюме дискуссии в Telegram
        
        Args:
            summary_content (str): Содержимое резюме
            report_type (str): Тип отчета (summary, bugs, features)
            
        Returns:
            dict: Ответ от Telegram API
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Определяем иконку и заголовок по типу отчета
        icons = {
            "bugs": "🐛",
            "features": "✨", 
            "summary": "📊"
        }
        
        titles = {
            "bugs": "Резюме дискуссии о багах",
            "features": "Резюме дискуссии о функциях",
            "summary": "Резюме анализа"
        }
        
        icon = icons.get(report_type, "📋")
        title = titles.get(report_type, "Отчет")
        
        header = f"{icon} *{title}*\n"
        header += f"📅 {timestamp}\n"
        header += "─" * 30 + "\n\n"
        
        # Ограничиваем длину резюме
        if len(summary_content) > 3000:
            summary_content = summary_content[:2900] + "\n\n... (отчет обрезан)"
        
        message = header + summary_content
        
        return self.send_message(message)

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    try:
        notifier = TelegramNotifier()
        response = notifier.send_message("🧪 Тест подключения к Telegram Bot API")
        if response and response.get('ok'):
            print("✅ Подключение к Telegram успешно!")
            return True
        else:
            print("❌ Ошибка подключения к Telegram")
            return False
    except Exception as e:
        print(f"❌ Ошибка при тестировании Telegram: {str(e)}")
        return False

if __name__ == "__main__":
    test_telegram_connection() 