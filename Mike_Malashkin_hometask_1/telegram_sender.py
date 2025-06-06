import os
import json
import asyncio
import subprocess
from datetime import datetime
from telegram_mcp_client import TelegramMCPClient

class TelegramReportSender:
    """Класс для отправки баг-репортов и улучшений в Telegram"""
    
    def __init__(self, recipient_username: str = "@mmalashkin"):
        self.recipient = recipient_username
        self.client = None
        
    async def send_bug_reports(self, bugreports_timestamp: str):
        """Отправляет все баг-репорты за указанную дату
        
        Args:
            bugreports_timestamp (str): Временная метка в формате YYYYMMDD_HHMMSS
        """
        print(f"🐛 Отправка баг-репортов в Telegram пользователю {self.recipient}...")
        
        # Ищем все файлы баг-репортов
        import glob
        pattern = f"output/bugreport_*_{bugreports_timestamp}.md"
        bug_files = glob.glob(pattern)
        
        if not bug_files:
            print(f"❌ Не найдены файлы баг-репортов по маске: {pattern}")
            return False
        
        print(f"📄 Найдено {len(bug_files)} баг-репортов для отправки")
        
        # Инициализируем клиент
        client = TelegramMCPClient()
        try:
            if not await client.initialize():
                print("❌ Не удалось инициализировать Telegram клиент")
                return False
            
            sent_count = 0
            for i, bug_file in enumerate(bug_files, 1):
                try:
                    # Читаем содержимое файла
                    with open(bug_file, 'r', encoding='utf-8') as f:
                        bug_content = f.read()
                    
                    # Обрезаем если слишком длинное (лимит Telegram 4096 символов)
                    if len(bug_content) > 4000:
                        bug_content = bug_content[:3900] + "\\n\\n[...содержимое обрезано...]"
                    
                    # Отправляем сообщение
                    message_text = f"🐛 **БАГ-РЕПОРТ #{i}**\\n\\n{bug_content}"
                    result = await client.send_message(self.recipient, message_text)
                    
                    if result.get('success'):
                        print(f"✅ Баг-репорт #{i} отправлен (ID: {result.get('message_id')})")
                        sent_count += 1
                        
                        # Пауза между сообщениями
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Ошибка отправки баг-репорта #{i}: {result.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Ошибка обработки файла {bug_file}: {str(e)}")
            
            print(f"📊 Отправлено {sent_count} из {len(bug_files)} баг-репортов")
            return sent_count > 0
            
        finally:
            await client.close()
    
    async def send_improvements(self, improvements_timestamp: str):
        """Отправляет все предложения по улучшениям за указанную дату
        
        Args:
            improvements_timestamp (str): Временная метка в формате YYYYMMDD_HHMMSS
        """
        print(f"💡 Отправка предложений по улучшениям в Telegram пользователю {self.recipient}...")
        
        # Ищем файлы с улучшениями
        import glob
        pattern = f"output/improvement_proposal_*_{improvements_timestamp}.md"
        improvement_files = glob.glob(pattern)
        
        if not improvement_files:
            print(f"❌ Не найдены файлы улучшений по маске: {pattern}")
            return False
        
        print(f"📄 Найдено {len(improvement_files)} предложений для отправки")
        
        # Инициализируем клиент
        client = TelegramMCPClient()
        try:
            if not await client.initialize():
                print("❌ Не удалось инициализировать Telegram клиент")
                return False
            
            sent_count = 0
            for i, improvement_file in enumerate(improvement_files, 1):
                try:
                    # Читаем содержимое файла
                    with open(improvement_file, 'r', encoding='utf-8') as f:
                        improvement_content = f.read()
                    
                    # Обрезаем если слишком длинное
                    if len(improvement_content) > 4000:
                        improvement_content = improvement_content[:3900] + "\\n\\n[...содержимое обрезано...]"
                    
                    # Отправляем сообщение
                    message_text = f"💡 **ПРЕДЛОЖЕНИЕ ПО УЛУЧШЕНИЮ #{i}**\\n\\n{improvement_content}"
                    result = await client.send_message(self.recipient, message_text)
                    
                    if result.get('success'):
                        print(f"✅ Улучшение #{i} отправлено (ID: {result.get('message_id')})")
                        sent_count += 1
                        
                        # Пауза между сообщениями
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ Ошибка отправки улучшения #{i}: {result.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Ошибка обработки файла {improvement_file}: {str(e)}")
            
            print(f"📊 Отправлено {sent_count} из {len(improvement_files)} предложений")
            return sent_count > 0
            
        finally:
            await client.close()
    
    def send_bug_reports_sync(self, bugreports_timestamp: str):
        """Синхронная версия отправки баг-репортов"""
        return asyncio.run(self.send_bug_reports(bugreports_timestamp))
    
    def send_improvements_sync(self, improvements_timestamp: str):
        """Синхронная версия отправки улучшений"""
        return asyncio.run(self.send_improvements(improvements_timestamp))

# Функции для прямого использования
def send_bug_reports_to_telegram(timestamp: str, recipient: str = "@mmalashkin"):
    """Отправляет баг-репорты в Telegram
    
    Args:
        timestamp (str): Временная метка генерации баг-репортов
        recipient (str): Получатель в Telegram
    """
    sender = TelegramReportSender(recipient)
    return sender.send_bug_reports_sync(timestamp)

def send_improvements_to_telegram(timestamp: str, recipient: str = "@mmalashkin"):
    """Отправляет предложения по улучшениям в Telegram
    
    Args:
        timestamp (str): Временная метка генерации улучшений
        recipient (str): Получатель в Telegram
    """
    sender = TelegramReportSender(recipient)
    return sender.send_improvements_sync(timestamp)

if __name__ == "__main__":
    # Пример использования
    import sys
    
    if len(sys.argv) < 3:
        print("Использование:")
        print("python telegram_sender.py bugs TIMESTAMP [@recipient]")
        print("python telegram_sender.py improvements TIMESTAMP [@recipient]")
        sys.exit(1)
    
    action = sys.argv[1]
    timestamp = sys.argv[2]
    recipient = sys.argv[3] if len(sys.argv) > 3 else "@mmalashkin"
    
    if action == "bugs":
        success = send_bug_reports_to_telegram(timestamp, recipient)
        print("✅ Баг-репорты отправлены!" if success else "❌ Ошибка отправки баг-репортов")
    elif action == "improvements":
        success = send_improvements_to_telegram(timestamp, recipient)
        print("✅ Улучшения отправлены!" if success else "❌ Ошибка отправки улучшений")
    else:
        print("❌ Неизвестное действие. Используйте 'bugs' или 'improvements'") 