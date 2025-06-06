import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from pyrogram import Client
from pyrogram.types import Dialog, Chat, Message
from dotenv import load_dotenv

load_dotenv()

class TelegramMCPClient:
    """Класс для работы с Telegram Client API через MCP"""
    
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID", "27734869")
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "a6868f9bf0a8767f63cac86d954e95b7")
        self.session_name = "telegram_mcp_session"
        self.client = None
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены в переменных окружения")
    
    async def initialize(self):
        """Инициализация Telegram клиента"""
        try:
            self.client = Client(
                name=self.session_name,
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                workdir="."
            )
            await self.client.start()
            print("✅ Telegram MCP Client успешно инициализирован")
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации Telegram MCP Client: {str(e)}")
            return False
    
    async def get_dialogs(self, limit: int = 50) -> List[Dict]:
        """Получает список диалогов
        
        Args:
            limit (int): Максимальное количество диалогов для получения
            
        Returns:
            List[Dict]: Список диалогов с информацией
        """
        if not self.client:
            raise ValueError("Client не инициализирован. Вызовите initialize() сначала")
        
        try:
            dialogs_data = []
            
            async for dialog in self.client.get_dialogs(limit=limit):
                chat_info = await self._extract_chat_info(dialog)
                dialogs_data.append(chat_info)
            
            return dialogs_data
            
        except Exception as e:
            print(f"❌ Ошибка получения диалогов: {str(e)}")
            return []
    
    async def _extract_chat_info(self, dialog: Dialog) -> Dict:
        """Извлекает информацию о чате из диалога"""
        chat = dialog.chat
        
        chat_info = {
            "id": chat.id,
            "type": chat.type.name,
            "title": getattr(chat, 'title', None),
            "username": getattr(chat, 'username', None),
            "first_name": getattr(chat, 'first_name', None),
            "last_name": getattr(chat, 'last_name', None),
            "is_verified": getattr(chat, 'is_verified', False),
            "is_restricted": getattr(chat, 'is_restricted', False),
            "is_scam": getattr(chat, 'is_scam', False),
            "unread_count": getattr(dialog, 'unread_count', 0),
            "is_pinned": getattr(dialog, 'is_pinned', False),
            "top_message": None
        }
        
        # Получаем информацию о последнем сообщении
        if dialog.top_message:
            try:
                top_msg = dialog.top_message
                chat_info["top_message"] = {
                    "id": top_msg.id,
                    "date": top_msg.date.isoformat() if top_msg.date else None,
                    "text": getattr(top_msg, 'text', None),
                    "from_user": None
                }
                
                if top_msg.from_user:
                    chat_info["top_message"]["from_user"] = {
                        "id": top_msg.from_user.id,
                        "first_name": getattr(top_msg.from_user, 'first_name', None),
                        "username": getattr(top_msg.from_user, 'username', None)
                    }
            except Exception as e:
                print(f"⚠️ Ошибка получения последнего сообщения для чата {chat.id}: {str(e)}")
        
        return chat_info
    
    async def get_chat_history(self, chat_id: int, limit: int = 100) -> List[Dict]:
        """Получает историю сообщений из конкретного чата
        
        Args:
            chat_id (int): ID чата
            limit (int): Максимальное количество сообщений
            
        Returns:
            List[Dict]: Список сообщений
        """
        if not self.client:
            raise ValueError("Client не инициализирован. Вызовите initialize() сначала")
        
        try:
            messages_data = []
            
            async for message in self.client.get_chat_history(chat_id, limit=limit):
                msg_info = await self._extract_message_info(message)
                messages_data.append(msg_info)
            
            return messages_data
            
        except Exception as e:
            print(f"❌ Ошибка получения истории чата {chat_id}: {str(e)}")
            return []
    
    async def _extract_message_info(self, message: Message) -> Dict:
        """Извлекает информацию из сообщения"""
        msg_info = {
            "id": message.id,
            "date": message.date.isoformat() if message.date else None,
            "text": getattr(message, 'text', None),
            "media_type": None,
            "from_user": None,
            "reply_to_message_id": getattr(message, 'reply_to_message_id', None),
            "forward_from": None
        }
        
        # Информация об отправителе
        if message.from_user:
            msg_info["from_user"] = {
                "id": message.from_user.id,
                "first_name": getattr(message.from_user, 'first_name', None),
                "username": getattr(message.from_user, 'username', None),
                "is_bot": getattr(message.from_user, 'is_bot', False)
            }
        
        # Тип медиа
        if message.media:
            msg_info["media_type"] = message.media.name
        
        return msg_info
    
    async def search_messages(self, query: str, chat_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Поиск сообщений по тексту
        
        Args:
            query (str): Поисковый запрос
            chat_id (int, optional): ID чата для поиска (если None - поиск по всем чатам)
            limit (int): Максимальное количество результатов
            
        Returns:
            List[Dict]: Список найденных сообщений
        """
        if not self.client:
            raise ValueError("Client не инициализирован. Вызовите initialize() сначала")
        
        try:
            messages_data = []
            
            async for message in self.client.search_messages(chat_id=chat_id, query=query, limit=limit):
                msg_info = await self._extract_message_info(message)
                # Добавляем информацию о чате
                if message.chat:
                    msg_info["chat"] = {
                        "id": message.chat.id,
                        "title": getattr(message.chat, 'title', None),
                        "username": getattr(message.chat, 'username', None)
                    }
                messages_data.append(msg_info)
            
            return messages_data
            
        except Exception as e:
            print(f"❌ Ошибка поиска сообщений: {str(e)}")
            return []
    
    async def send_message(self, chat_id: str, text: str) -> Dict:
        """Отправляет сообщение в чат
        
        Args:
            chat_id (str): ID чата или username (например, 'egorpalich' или '131669361')
            text (str): Текст сообщения
            
        Returns:
            Dict: Информация об отправленном сообщении
        """
        if not self.client:
            raise ValueError("Client не инициализирован. Вызовите initialize() сначала")
        
        try:
            # Отправляем сообщение
            message = await self.client.send_message(chat_id, text)
            
            # Формируем ответ
            result = {
                "success": True,
                "message_id": message.id,
                "chat_id": message.chat.id,
                "date": message.date.isoformat() if message.date else None,
                "text": message.text,
                "chat_info": {
                    "id": message.chat.id,
                    "type": message.chat.type.name,
                    "title": getattr(message.chat, 'title', None),
                    "username": getattr(message.chat, 'username', None),
                    "first_name": getattr(message.chat, 'first_name', None)
                }
            }
            
            print(f"✅ Сообщение отправлено в чат {chat_id}")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения в чат {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "chat_id": chat_id
            }
    
    async def close(self):
        """Закрывает соединение с Telegram"""
        if self.client:
            await self.client.stop()
            print("📱 Telegram MCP Client отключен")
    
    def save_dialogs_to_file(self, dialogs: List[Dict], filename: Optional[str] = None) -> str:
        """Сохраняет диалоги в JSON файл
        
        Args:
            dialogs (List[Dict]): Список диалогов
            filename (str, optional): Имя файла (если None - генерируется автоматически)
            
        Returns:
            str: Путь к сохраненному файлу
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/telegram_dialogs_{timestamp}.json"
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dialogs, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Диалоги сохранены в файл: {filename}")
        return filename

# Функции для удобного использования
async def get_telegram_dialogs(limit: int = 50, save_to_file: bool = True) -> List[Dict]:
    """Основная функция для получения диалогов Telegram
    
    Args:
        limit (int): Максимальное количество диалогов
        save_to_file (bool): Сохранять ли результат в файл
        
    Returns:
        List[Dict]: Список диалогов
    """
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            dialogs = await client.get_dialogs(limit=limit)
            
            if save_to_file and dialogs:
                client.save_dialogs_to_file(dialogs)
            
            print(f"📱 Получено {len(dialogs)} диалогов")
            return dialogs
        else:
            print("❌ Не удалось инициализировать Telegram клиент")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка в get_telegram_dialogs: {str(e)}")
        return []
    finally:
        await client.close()

def run_get_dialogs(limit: int = 50):
    """Запускает получение диалогов в синхронном режиме"""
    return asyncio.run(get_telegram_dialogs(limit=limit))

if __name__ == "__main__":
    # Пример использования
    print("🔧 Тестирование Telegram MCP Client")
    print("=" * 50)
    
    dialogs = run_get_dialogs(limit=20)
    
    if dialogs:
        print(f"\n📊 Сводка по {len(dialogs)} диалогам:")
        for i, dialog in enumerate(dialogs[:5], 1):
            print(f"{i}. {dialog.get('title', dialog.get('first_name', 'Без названия'))} "
                  f"(ID: {dialog['id']}, непрочитанных: {dialog['unread_count']})")
        
        if len(dialogs) > 5:
            print(f"... и еще {len(dialogs) - 5} диалогов")
    else:
        print("❌ Диалоги не получены") 