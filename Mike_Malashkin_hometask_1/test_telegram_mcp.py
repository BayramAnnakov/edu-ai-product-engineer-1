#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Telegram MCP Client
"""

import os
import asyncio
from telegram_mcp_client import TelegramMCPClient, get_telegram_dialogs

async def test_basic_connection():
    """Тестирует базовое подключение к Telegram"""
    print("\n🔗 Тест 1: Базовое подключение...")
    
    client = TelegramMCPClient()
    
    try:
        success = await client.initialize()
        if success:
            print("✅ Подключение успешно")
            await client.close()
            return True
        else:
            print("❌ Ошибка подключения")
            return False
    except Exception as e:
        print(f"❌ Ошибка в тесте подключения: {str(e)}")
        return False

async def test_get_dialogs():
    """Тестирует получение диалогов"""
    print("\n📱 Тест 2: Получение диалогов...")
    
    try:
        dialogs = await get_telegram_dialogs(limit=10, save_to_file=True)
        
        if dialogs:
            print(f"✅ Получено {len(dialogs)} диалогов")
            
            # Показываем информацию о первых 3 диалогах
            for i, dialog in enumerate(dialogs[:3], 1):
                title = dialog.get('title', dialog.get('first_name', 'Без названия'))
                chat_type = dialog.get('type', 'Unknown')
                unread = dialog.get('unread_count', 0)
                
                print(f"  {i}. {title} (тип: {chat_type}, непрочитанных: {unread})")
            
            return True
        else:
            print("❌ Диалоги не получены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте получения диалогов: {str(e)}")
        return False

async def test_get_chat_history():
    """Тестирует получение истории чата"""
    print("\n💬 Тест 3: Получение истории чата...")
    
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            # Получаем диалоги для выбора чата
            dialogs = await client.get_dialogs(limit=5)
            
            if dialogs:
                # Берем первый диалог
                first_dialog = dialogs[0]
                chat_id = first_dialog['id']
                chat_title = first_dialog.get('title', first_dialog.get('first_name', 'Без названия'))
                
                print(f"  Получаем историю для: {chat_title}")
                
                # Получаем историю
                messages = await client.get_chat_history(chat_id, limit=5)
                
                if messages:
                    print(f"✅ Получено {len(messages)} сообщений")
                    
                    # Показываем последние 2 сообщения
                    for i, msg in enumerate(messages[:2], 1):
                        text = msg.get('text', '[Без текста]')
                        date = msg.get('date', 'Неизвестно')
                        from_user = msg.get('from_user', {})
                        sender = from_user.get('first_name', 'Неизвестный отправитель')
                        
                        # Обрезаем длинный текст
                        if len(text) > 50:
                            text = text[:47] + "..."
                        
                        print(f"    {i}. {sender}: {text} ({date[:19] if date != 'Неизвестно' else date})")
                    
                    await client.close()
                    return True
                else:
                    print("❌ История чата не получена")
                    await client.close()
                    return False
            else:
                print("❌ Не удалось получить диалоги для теста")
                await client.close()
                return False
        else:
            print("❌ Не удалось инициализировать клиент")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте истории чата: {str(e)}")
        if client.client:
            await client.close()
        return False

async def test_search_messages():
    """Тестирует поиск сообщений"""
    print("\n🔍 Тест 4: Поиск сообщений...")
    
    client = TelegramMCPClient()
    
    try:
        if await client.initialize():
            # Ищем сообщения с популярными словами
            search_queries = ["привет", "как дела", "спасибо"]
            
            for query in search_queries:
                print(f"  Ищем: '{query}'")
                
                messages = await client.search_messages(query, limit=3)
                
                if messages:
                    print(f"    ✅ Найдено {len(messages)} сообщений")
                    break
                else:
                    print(f"    ❌ Ничего не найдено")
            
            await client.close()
            return True
            
    except Exception as e:
        print(f"❌ Ошибка в тесте поиска: {str(e)}")
        if client.client:
            await client.close()
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование Telegram MCP Client")
    print("=" * 60)
    
    # Проверяем переменные окружения
    api_id = os.getenv("TELEGRAM_API_ID", "27734869")
    api_hash = os.getenv("TELEGRAM_API_HASH", "a6868f9bf0a8767f63cac86d954e95b7")
    
    print(f"📋 Конфигурация:")
    print(f"  API ID: {api_id}")
    print(f"  API Hash: {api_hash[:10]}...")
    
    # Запуск тестов
    test_results = []
    
    test_results.append(await test_basic_connection())
    
    if test_results[-1]:  # Если базовое подключение работает
        test_results.append(await test_get_dialogs())
        test_results.append(await test_get_chat_history())
        test_results.append(await test_search_messages())
    else:
        print("\n⚠️ Пропускаем остальные тесты из-за ошибки подключения")
    
    # Результаты
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    
    test_names = [
        "Базовое подключение",
        "Получение диалогов", 
        "История чата",
        "Поиск сообщений"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
        print(f"  {i+1}. {name}: {status}")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n🎯 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены!")
    elif passed > 0:
        print("⚠️ Частичная работоспособность")
    else:
        print("❌ Система не работает")

def run_simple_dialog_test():
    """Простой синхронный тест получения диалогов"""
    print("🚀 Быстрый тест получения диалогов Telegram...")
    
    try:
        from telegram_mcp_client import run_get_dialogs
        dialogs = run_get_dialogs(limit=15)
        
        if dialogs:
            print(f"\n✅ Успешно получено {len(dialogs)} диалогов")
            print("\n🔝 Топ-5 диалогов:")
            
            for i, dialog in enumerate(dialogs[:5], 1):
                title = dialog.get('title', dialog.get('first_name', 'Без названия'))
                chat_type = dialog.get('type', 'Unknown')
                unread = dialog.get('unread_count', 0)
                is_pinned = "📌" if dialog.get('is_pinned') else ""
                
                print(f"  {i}. {is_pinned} {title}")
                print(f"     Тип: {chat_type} | Непрочитанных: {unread}")
                
                # Показываем последнее сообщение если есть
                if dialog.get('top_message') and dialog['top_message'].get('text'):
                    last_text = dialog['top_message']['text']
                    if len(last_text) > 60:
                        last_text = last_text[:57] + "..."
                    print(f"     Последнее: {last_text}")
                print()
                
            return True
        else:
            print("❌ Диалоги не получены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Простой тест
        run_simple_dialog_test()
    else:
        # Полные тесты
        asyncio.run(main()) 