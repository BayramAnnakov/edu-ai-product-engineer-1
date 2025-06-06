# Telegram MCP Integration - Настройка и использование

## Описание

Telegram MCP интеграция позволяет получать данные из Telegram через Client API для анализа переписок, диалогов и сообщений. Использует библиотеку pyrogram для взаимодействия с Telegram API.

## Возможности

- **getDialogs** - получение списка всех диалогов (чаты, группы, каналы)
- **getHistory** - получение истории сообщений из конкретного чата
- **search** - поиск сообщений по тексту во всех чатах или в конкретном чате
- Автоматическое сохранение данных в JSON формате
- Статистика и анализ полученных данных
- Асинхронная обработка для высокой производительности

## Предварительные требования

### 1. Получение API credentials

1. Перейдите на https://my.telegram.org/apps
2. Войдите под своим номером телефона
3. Создайте новое приложение:
   - App title: "AI Analysis Tool" (или любое другое название)
   - Short name: "ai_analysis" (или любое другое)
   - Platform: Desktop
4. Скопируйте `api_id` и `api_hash`

### 2. Настройка переменных окружения

Добавьте в файл `.env`:

```env
# Telegram MCP Configuration
TELEGRAM_API_ID=27734869
TELEGRAM_API_HASH=a6868f9bf0a8767f63cac86d954e95b7
```

> **Примечание**: Указанные значения уже настроены в MCP конфигурации, но можно использовать свои.

### 3. Установка зависимостей

```bash
pip install pyrogram==2.0.106
```

Или если используете requirements.txt:

```bash
pip install -r requirements.txt
```

## Первый запуск

При первом запуске потребуется аутентификация:

```bash
python telegram_mcp_client.py
```

Telegram запросит:
1. Номер телефона
2. Код подтверждения из SMS/Telegram
3. Пароль двухфакторной аутентификации (если настроен)

После успешной аутентификации создается файл сессии `telegram_mcp_session.session`, который используется для последующих подключений.

## Использование

### Быстрый тест

```bash
# Простой тест получения диалогов
python test_telegram_mcp.py --simple

# Полный набор тестов
python test_telegram_mcp.py
```

### Основные команды

#### 1. Получение диалогов

```bash
# Получить 50 диалогов (по умолчанию)
python run_telegram_mcp.py getDialogs

# Получить 100 диалогов
python run_telegram_mcp.py getDialogs --limit 100

# Сохранить в конкретный файл
python run_telegram_mcp.py getDialogs --output my_dialogs.json
```

#### 2. Получение истории чата

```bash
# Получить 100 сообщений из чата (замените CHAT_ID на реальный ID)
python run_telegram_mcp.py getHistory CHAT_ID

# Получить 500 сообщений
python run_telegram_mcp.py getHistory CHAT_ID --limit 500
```

#### 3. Поиск сообщений

```bash
# Поиск по всем чатам
python run_telegram_mcp.py search "важная информация"

# Поиск в конкретном чате
python run_telegram_mcp.py search "проект" --chat_id CHAT_ID

# Ограничить количество результатов
python run_telegram_mcp.py search "встреча" --limit 20
```

### Программное использование

```python
from telegram_mcp_client import TelegramMCPClient, get_telegram_dialogs

# Простое получение диалогов
dialogs = run_get_dialogs(limit=30)

# Продвинутое использование
import asyncio

async def my_analysis():
    client = TelegramMCPClient()
    
    try:
        await client.initialize()
        
        # Получаем диалоги
        dialogs = await client.get_dialogs(limit=50)
        
        # Анализируем каждый диалог
        for dialog in dialogs:
            if dialog['unread_count'] > 0:
                print(f"Непрочитанных в {dialog['title']}: {dialog['unread_count']}")
                
                # Получаем историю активного чата
                messages = await client.get_chat_history(dialog['id'], limit=10)
                print(f"Последние сообщения: {len(messages)}")
        
    finally:
        await client.close()

# Запуск
asyncio.run(my_analysis())
```

## Структура выходных данных

### Диалоги (getDialogs)

```json
{
  "timestamp": "2025-01-19T14:30:00.123456",
  "total_dialogs": 25,
  "summary": {
    "private_chats": 15,
    "groups": 8,
    "channels": 2,
    "total_unread": 47,
    "pinned_count": 3
  },
  "dialogs": [
    {
      "id": -1001234567890,
      "title": "Рабочая группа",
      "type": "SUPERGROUP",
      "username": "work_group",
      "unread_count": 5,
      "is_pinned": true,
      "is_verified": false,
      "last_message": {
        "text": "Встреча в 15:00",
        "date": "2025-01-19T13:45:00+00:00",
        "from_user": "Иван"
      }
    }
  ]
}
```

### История чата (getHistory)

```json
{
  "timestamp": "2025-01-19T14:30:00.123456",
  "chat_id": -1001234567890,
  "total_messages": 100,
  "messages": [
    {
      "id": 12345,
      "date": "2025-01-19T13:45:00+00:00",
      "text": "Привет! Как дела?",
      "media_type": null,
      "from_user": {
        "id": 123456789,
        "first_name": "Иван",
        "username": "ivan_user",
        "is_bot": false
      },
      "reply_to_message_id": null
    }
  ]
}
```

### Результаты поиска (search)

```json
{
  "timestamp": "2025-01-19T14:30:00.123456",
  "query": "важная информация",
  "chat_id": null,
  "total_found": 15,
  "messages": [
    {
      "id": 54321,
      "date": "2025-01-19T12:00:00+00:00",
      "text": "Это важная информация для проекта",
      "chat": {
        "id": -1001234567890,
        "title": "Рабочая группа",
        "username": "work_group"
      },
      "from_user": {
        "id": 987654321,
        "first_name": "Мария",
        "username": "maria_user",
        "is_bot": false
      }
    }
  ]
}
```

## Интеграция с основным пайплайном

Telegram MCP данные можно использовать как дополнительный источник для анализа:

1. **Анализ клиентских запросов** - поиск сообщений с жалобами или запросами функций
2. **Мониторинг обратной связи** - отслеживание реакций пользователей на продукт
3. **Генерация персон** - использование реальных диалогов для создания более точных персон
4. **Контекстный анализ** - понимание как клиенты обсуждают продукт в неформальной обстановке

Пример интеграции:

```python
# Получаем диалоги из Telegram
dialogs_data = run_get_dialogs(limit=100)

# Ищем упоминания продукта
product_mentions = []
for dialog in dialogs_data:
    if dialog['unread_count'] > 0:
        # Анализируем активные чаты на предмет упоминаний продукта
        messages = get_chat_history(dialog['id'], limit=50)
        # ... анализ сообщений
```

## Безопасность и рекомендации

1. **Защита данных**:
   - Не сохраняйте API credentials в коде
   - Используйте переменные окружения
   - Регулярно обновляйте токены доступа

2. **Производительность**:
   - Используйте лимиты для больших чатов
   - Кэшируйте результаты когда возможно
   - Избегайте слишком частых запросов

3. **Соблюдение правил**:
   - Соблюдайте лимиты Telegram API
   - Получайте согласие при анализе групповых чатов
   - Не нарушайте приватность пользователей

## Устранение проблем

### Ошибка аутентификации
```
❌ Ошибка инициализации Telegram MCP Client: Authentication failed
```
**Решение**: Удалите файл сессии и пройдите аутентификацию заново:
```bash
rm telegram_mcp_session.session
python telegram_mcp_client.py
```

### Ошибка API credentials
```
❌ TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены
```
**Решение**: Проверьте файл `.env` и убедитесь что переменные установлены правильно.

### Ошибка доступа к чату
```
❌ Ошибка получения истории чата: Chat not found
```
**Решение**: Убедитесь что у вас есть доступ к чату и ID указан правильно.

### Медленная работа
**Решение**: 
- Уменьшите лимиты (--limit)
- Используйте поиск по конкретным чатам вместо глобального поиска
- Проверьте стабильность интернет-соединения

## Полезные советы

1. **Получение Chat ID**: Запустите `getDialogs` и найдите нужный чат в результатах
2. **Batch обработка**: Для анализа множества чатов используйте скрипты с циклами
3. **Фильтрация**: Используйте Python для дополнительной фильтрации полученных данных
4. **Мониторинг**: Настройте регулярное выполнение для отслеживания изменений

## Примеры использования

### Анализ активности в группах
```bash
# Получаем диалоги и анализируем групповую активность
python run_telegram_mcp.py getDialogs --limit 50
# Анализируем JSON файл для поиска самых активных групп
```

### Мониторинг упоминаний бренда
```bash
# Ищем упоминания продукта
python run_telegram_mcp.py search "название_продукта" --limit 100
```

### Экспорт данных для анализа
```bash
# Экспортируем историю важного чата
python run_telegram_mcp.py getHistory CHAT_ID --limit 1000 --output important_chat_export.json
``` 