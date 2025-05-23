#!/usr/bin/env python3
"""
Основной скрипт для работы с Telegram MCP - получение диалогов и сообщений
"""

import argparse
import json
import os
from datetime import datetime
from telegram_mcp_client import TelegramMCPClient, get_telegram_dialogs

def format_dialogs_for_analysis(dialogs):
    """Форматирует диалоги для анализа в основном пайплайне"""
    formatted_data = {
        "timestamp": datetime.now().isoformat(),
        "total_dialogs": len(dialogs),
        "dialogs": [],
        "summary": {
            "private_chats": 0,
            "groups": 0,
            "channels": 0,
            "total_unread": 0,
            "pinned_count": 0,
        }
    }
    
    for dialog in dialogs:
        chat_type = dialog.get('type', 'unknown')
        
        # Обновляем статистику
        if chat_type == 'PRIVATE':
            formatted_data["summary"]["private_chats"] += 1
        elif chat_type == 'GROUP' or chat_type == 'SUPERGROUP':
            formatted_data["summary"]["groups"] += 1
        elif chat_type == 'CHANNEL':
            formatted_data["summary"]["channels"] += 1
        
        formatted_data["summary"]["total_unread"] += dialog.get('unread_count', 0)
        
        if dialog.get('is_pinned'):
            formatted_data["summary"]["pinned_count"] += 1
        
        # Форматируем информацию о диалоге
        formatted_dialog = {
            "id": dialog['id'],
            "title": dialog.get('title', dialog.get('first_name', 'Без названия')),
            "type": chat_type,
            "username": dialog.get('username'),
            "unread_count": dialog.get('unread_count', 0),
            "is_pinned": dialog.get('is_pinned', False),
            "is_verified": dialog.get('is_verified', False),
            "last_message": None
        }
        
        # Добавляем информацию о последнем сообщении
        if dialog.get('top_message'):
            top_msg = dialog['top_message']
            formatted_dialog["last_message"] = {
                "text": top_msg.get('text'),
                "date": top_msg.get('date'),
                "from_user": top_msg.get('from_user', {}).get('first_name') if top_msg.get('from_user') else None
            }
        
        formatted_data["dialogs"].append(formatted_dialog)
    
    return formatted_data

async def get_dialogs_command(args):
    """Команда получения диалогов"""
    print(f"📱 Получение {args.limit} диалогов из Telegram...")
    
    try:
        dialogs = await get_telegram_dialogs(limit=args.limit, save_to_file=False)
        
        if dialogs:
            # Форматируем данные
            formatted_data = format_dialogs_for_analysis(dialogs)
            
            # Определяем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.output:
                filename = args.output
            else:
                filename = f"output/telegram_dialogs_{timestamp}.json"
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Сохраняем
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Диалоги сохранены в: {filename}")
            
            # Выводим статистику
            summary = formatted_data["summary"]
            print(f"\n📊 Статистика:")
            print(f"  Всего диалогов: {formatted_data['total_dialogs']}")
            print(f"  Личные чаты: {summary['private_chats']}")
            print(f"  Группы: {summary['groups']}")
            print(f"  Каналы: {summary['channels']}")
            print(f"  Всего непрочитанных: {summary['total_unread']}")
            print(f"  Закрепленных: {summary['pinned_count']}")
            
            # Показываем топ диалогов
            print(f"\n🔝 Топ-5 диалогов по активности:")
            sorted_dialogs = sorted(formatted_data["dialogs"], 
                                  key=lambda x: x['unread_count'], 
                                  reverse=True)
            
            for i, dialog in enumerate(sorted_dialogs[:5], 1):
                title = dialog['title']
                unread = dialog['unread_count']
                chat_type = dialog['type']
                pinned = "📌" if dialog['is_pinned'] else ""
                
                print(f"  {i}. {pinned} {title} ({chat_type}) - {unread} непрочитанных")
            
            return filename
        else:
            print("❌ Не удалось получить диалоги")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка получения диалогов: {str(e)}")
        return None

async def get_chat_history_command(args):
    """Команда получения истории чата"""
    print(f"💬 Получение истории чата {args.chat_id}...")
    
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            messages = await client.get_chat_history(args.chat_id, limit=args.limit)
            
            if messages:
                # Определяем имя файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.output:
                    filename = args.output
                else:
                    filename = f"output/telegram_chat_{args.chat_id}_{timestamp}.json"
                
                # Создаем директорию если не существует
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                # Форматируем данные
                chat_data = {
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": args.chat_id,
                    "total_messages": len(messages),
                    "messages": messages
                }
                
                # Сохраняем
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 История чата сохранена в: {filename}")
                print(f"📊 Получено {len(messages)} сообщений")
                
                await client.close()
                return filename
            else:
                print("❌ Не удалось получить историю чата")
                await client.close()
                return None
        else:
            print("❌ Не удалось инициализировать клиент")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка получения истории чата: {str(e)}")
        if client.client:
            await client.close()
        return None

async def search_messages_command(args):
    """Команда поиска сообщений"""
    print(f"🔍 Поиск сообщений: '{args.query}'...")
    
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            messages = await client.search_messages(
                query=args.query, 
                chat_id=args.chat_id if hasattr(args, 'chat_id') and args.chat_id else None,
                limit=args.limit
            )
            
            if messages:
                # Определяем имя файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_query = args.query.replace(' ', '_').replace('/', '_')[:20]
                if args.output:
                    filename = args.output
                else:
                    filename = f"output/telegram_search_{safe_query}_{timestamp}.json"
                
                # Создаем директорию если не существует
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                # Форматируем данные
                search_data = {
                    "timestamp": datetime.now().isoformat(),
                    "query": args.query,
                    "chat_id": args.chat_id if hasattr(args, 'chat_id') and args.chat_id else None,
                    "total_found": len(messages),
                    "messages": messages
                }
                
                # Сохраняем
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(search_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Результаты поиска сохранены в: {filename}")
                print(f"📊 Найдено {len(messages)} сообщений")
                
                # Показываем примеры
                print(f"\n🔍 Примеры найденных сообщений:")
                for i, msg in enumerate(messages[:3], 1):
                    text = msg.get('text', '[Без текста]')
                    if len(text) > 80:
                        text = text[:77] + "..."
                    
                    chat_info = msg.get('chat', {})
                    chat_title = chat_info.get('title', 'Неизвестный чат')
                    
                    print(f"  {i}. В чате '{chat_title}': {text}")
                
                await client.close()
                return filename
            else:
                print("❌ Ничего не найдено")
                await client.close()
                return None
        else:
            print("❌ Не удалось инициализировать клиент")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка поиска сообщений: {str(e)}")
        if client.client:
            await client.close()
        return None

async def send_message_command(args):
    """Команда отправки сообщения"""
    print(f"📤 Отправка сообщения в чат {args.chat_id}...")
    
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            result = await client.send_message(args.chat_id, args.text)
            
            if result.get('success'):
                # Определяем имя файла для логирования
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.output:
                    filename = args.output
                else:
                    safe_chat_id = str(args.chat_id).replace('@', '').replace('-', '_')
                    filename = f"output/telegram_sent_message_{safe_chat_id}_{timestamp}.json"
                
                # Создаем директорию если не существует
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                # Форматируем данные для сохранения
                message_data = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "send_message",
                    "target_chat": args.chat_id,
                    "message_text": args.text,
                    "result": result
                }
                
                # Сохраняем
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(message_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Лог отправки сохранен в: {filename}")
                
                # Выводим информацию
                chat_info = result.get('chat_info', {})
                chat_name = chat_info.get('title') or chat_info.get('first_name') or chat_info.get('username', 'Неизвестный чат')
                
                print(f"\n📊 Информация об отправке:")
                print(f"  Чат: {chat_name}")
                print(f"  Тип: {chat_info.get('type', 'Unknown')}")
                print(f"  ID сообщения: {result.get('message_id')}")
                print(f"  Дата отправки: {result.get('date', 'Unknown')}")
                print(f"  Текст: \"{result.get('text', '')}\"")
                
                await client.close()
                return filename
            else:
                print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                await client.close()
                return None
        else:
            print("❌ Не удалось инициализировать клиент")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {str(e)}")
        if client.client:
            await client.close()
        return None

def main():
    """Основная функция с парсингом аргументов"""
    parser = argparse.ArgumentParser(description='Telegram MCP Client - получение диалогов и сообщений')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда получения диалогов
    dialogs_parser = subparsers.add_parser('getDialogs', help='Получить список диалогов')
    dialogs_parser.add_argument('--limit', type=int, default=50, 
                               help='Максимальное количество диалогов (по умолчанию: 50)')
    dialogs_parser.add_argument('--output', type=str, 
                               help='Путь к выходному файлу (по умолчанию: auto)')
    
    # Команда получения истории чата
    history_parser = subparsers.add_parser('getHistory', help='Получить историю чата')
    history_parser.add_argument('chat_id', type=int, help='ID чата')
    history_parser.add_argument('--limit', type=int, default=100,
                               help='Максимальное количество сообщений (по умолчанию: 100)')
    history_parser.add_argument('--output', type=str,
                               help='Путь к выходному файлу (по умолчанию: auto)')
    
    # Команда поиска сообщений
    search_parser = subparsers.add_parser('search', help='Поиск сообщений')
    search_parser.add_argument('query', type=str, help='Поисковый запрос')
    search_parser.add_argument('--chat_id', type=int, 
                              help='ID чата для поиска (если не указан - поиск по всем)')
    search_parser.add_argument('--limit', type=int, default=50,
                              help='Максимальное количество результатов (по умолчанию: 50)')
    search_parser.add_argument('--output', type=str,
                              help='Путь к выходному файлу (по умолчанию: auto)')
    
    # Команда отправки сообщения
    send_message_parser = subparsers.add_parser('sendMessage', help='Отправить сообщение в чат')
    send_message_parser.add_argument('chat_id', type=str, help='ID чата или username (например: egorpalich или 131669361)')
    send_message_parser.add_argument('text', type=str, help='Текст сообщения')
    send_message_parser.add_argument('--output', type=str,
                               help='Путь к выходному файлу (по умолчанию: auto)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Выполняем команду
    import asyncio
    
    if args.command == 'getDialogs':
        result = asyncio.run(get_dialogs_command(args))
    elif args.command == 'getHistory':
        result = asyncio.run(get_chat_history_command(args))
    elif args.command == 'search':
        result = asyncio.run(search_messages_command(args))
    elif args.command == 'sendMessage':
        result = asyncio.run(send_message_command(args))
    
    if result:
        print(f"\n✅ Операция завершена успешно")
        print(f"📁 Результат сохранен в: {result}")
    else:
        print(f"\n❌ Операция не выполнена")

if __name__ == "__main__":
    main() 