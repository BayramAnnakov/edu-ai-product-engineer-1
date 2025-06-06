Отлично! Вот подробный чеклист в формате todo.md, основанный на 15 шагах, которые мы разработали.

# TODO - Автоматизированный Анализ Отзывов и Симуляция Фокус-группы

Этот файл отслеживает прогресс разработки проекта согласно плану.

## Фаза 1: Фундамент Проекта и Загрузка Данных

### Шаг 1: Настройка Структуры Проекта и Зависимостей
- [x] Создать папку `src/`
- [x] Создать папку `data/`
- [x] Добавить `.gitkeep` в `data/`
- [x] Создать папку `output/`
- [x] Добавить `.gitkeep` в `output/`
- [x] Создать папку `tests/`
- [x] Добавить `.gitkeep` в `tests/`
- [x] Создать файл `requirements.txt`
- [x] Добавить `python-dotenv`, `pandas`, `openai` в `requirements.txt`
- [x] Создать файл `.gitignore`
- [x] Добавить стандартные исключения Python (.pyc, __pycache__, venv/, .env) в `.gitignore`
- [x] Создать файл `.env`
- [x] Добавить `OPENAI_API_KEY=ВАШ_КЛЮЧ_СЮДА` в `.env`
- [x] Создать пустой файл `README.md`
- [x] *Действие пользователя:* Создать виртуальное окружение (`venv`)
- [x] *Действие пользователя:* Установить зависимости (`pip install -r requirements.txt`)
- [x] *Действие пользователя:* Создать файл `.env` из `.env.example` и добавить реальный API ключ

### Шаг 2: Базовый Скрипт, CLI и Загрузка .env
- [x] Создать файл `src/main.py`
- [x] Импортировать `argparse`, `os`, `load_dotenv` в `src/main.py`
- [x] Определить функцию `main()` в `src/main.py`
- [x] Вызвать `load_dotenv()` в начале `main()`
- [x] Реализовать парсинг аргументов с помощью `argparse`
- [x] Добавить обязательный аргумент `--csv-path` (или `-c`)
- [x] Получить значение `csv_path` из аргументов
- [x] Получить значение `OPENAI_API_KEY` из `os.getenv()`
- [x] Добавить проверку наличия `OPENAI_API_KEY`, вывести ошибку и выйти (`exit(1)`) если отсутствует
- [x] Добавить (временную) проверку существования файла `csv_path` (`os.path.exists`), вывести ошибку и выйти (`exit(1)`) если отсутствует
- [x] Добавить placeholder `print` для `csv_path` и статуса API ключа
- [x] Добавить блок `if __name__ == "__main__":` для вызова `main()`
- [x] Добавить docstring для функции `main()`

### Шаг 3: Модуль Загрузки и Валидации CSV
- [x] Создать файл `src/data_loader.py`
- [x] Импортировать `pandas as pd` в `src/data_loader.py`
- [x] Определить константу `REQUIRED_COLUMNS` со списком колонок
- [x] Определить функцию `load_reviews(csv_path: str) -> pd.DataFrame:`
- [x] Добавить docstring для `load_reviews` (параметры, возврат, исключения)
- [x] Использовать `try-except` для `pd.read_csv(csv_path)`
- [x] Обработать `FileNotFoundError` (перевыбросить или обернуть)
- [x] Обработать ошибки парсинга (`pd.errors.ParserError`, `Exception`), поднять `ValueError`
- [x] Реализовать проверку наличия всех колонок из `REQUIRED_COLUMNS`
- [x] Поднять `ValueError` с сообщением об отсутствующих колонках, если проверка не пройдена
- [x] Вернуть DataFrame в случае успеха
- [x] **Модификация `src/main.py`:**
    - [x] Импортировать `load_reviews` из `src.data_loader`
    - [x] Удалить проверку `os.path.exists(csv_path)`
    - [x] Обернуть вызов `load_reviews(csv_path)` в `try-except`
    - [x] Обработать `FileNotFoundError` и `ValueError` от `load_reviews`, вывести ошибку и выйти (`exit(1)`)
    - [x] Вывести сообщение об успешной загрузке и количестве строк (`len(df)`)
    - [x] Сохранить результат в переменную `reviews_df`

### Шаг 4: Базовая Настройка Логирования
- [x] Создать файл `src/logger_config.py`
- [x] Импортировать `logging` в `src/logger_config.py`
- [x] Определить функцию `setup_logger()`
- [x] Настроить `logging.basicConfig` в `setup_logger` (уровень INFO, формат, StreamHandler)
- [x] Добавить docstring для `setup_logger`
- [x] **Модификация `src/main.py`:**
    - [x] Импортировать `logging` и `setup_logger`
    - [x] Вызвать `setup_logger()` в начале `main()`
    - [x] Заменить все `print` на `logging.info` или `logging.error`
    - [x] Добавить лог `logging.info("Запуск пайплайна...")` в начале
    - [x] Добавить лог `logging.info("Пайплайн успешно завершил загрузку данных.")` (или аналогичный) в конце (пока что после загрузки данных)
- [x] **Модификация `src/data_loader.py`:**
    - [x] Импортировать `logging`
    - [x] Добавить `logging.info` перед чтением CSV
    - [x] Добавить `logging.error` при `FileNotFoundError`
    - [x] Добавить `logging.error` при `ValueError` (ошибка парсинга/колонок)
    - [x] Добавить `logging.info` после успешной загрузки и валидации

## Фаза 2: Агент 1 - Аналитик и Генератор Фич

### Шаг 5: Структура Агента 1 и Подготовка Данных
- [x] Создать файл `src/agent_feature_generator.py`
- [x] Импортировать `pandas`, `logging`
- [x] Определить класс `FeatureGeneratorAgent`
- [x] Реализовать `__init__(self, api_key)` (сохранить `api_key`)
- [x] Инициализировать `self.logger = logging.getLogger(__name__)` в `__init__`
- [x] Определить приватный метод `_prepare_llm_input(self, reviews_df, max_reviews=100)`
- [x] Добавить docstring для `_prepare_llm_input`
- [x] Выбрать колонки 'Summary', 'Text' в `_prepare_llm_input`
- [x] Реализовать логику ограничения количества отзывов (`max_reviews`)
- [x] Добавить логгирование, если отзывы были ограничены
- [x] Сформатировать отзывы в единую строку
- [x] Обработать случай пустого DataFrame в `_prepare_llm_input`
- [x] Вернуть отформатированную строку
- [x] Определить метод `generate_features(self, reviews_df)`
- [x] Добавить docstring для `generate_features`
- [x] Добавить лог `self.logger.info("Агент 1: Начало генерации функций...")`
- [x] Вызвать `_prepare_llm_input`
- [x] Залогировать информацию о подготовленных данных (длина строки)
- [x] Обработать случай пустого входного DataFrame `reviews_df`
- [x] Вернуть пустой список `[]` (placeholder)
- [x] Добавить лог `self.logger.info("Агент 1: Завершил подготовку данных...")`
- [x] **Модификация `src/main.py`:**
    - [x] Импортировать `FeatureGeneratorAgent`
    - [x] Создать экземпляр `feature_agent = FeatureGeneratorAgent(api_key=...)`
    - [x] Вызвать `features = feature_agent.generate_features(reviews_df)`
    - [x] Залогировать результат `features` (пока будет `[]`)

### Шаг 6: Клиент для OpenAI API с Retry
- [x] Создать файл `src/llm_client.py`
- [x] Импортировать `openai`, `os`, `time`, `logging`, `openai` errors
- [x] Определить функцию `call_openai_api(...)` с параметрами (prompt, system_message, model, max_retries, initial_delay)
- [x] Добавить docstring для `call_openai_api`
- [x] Инициализировать логгер
- [x] Получить API ключ из env, проверить, инициализировать `openai.OpenAI` клиент
- [x] Реализовать цикл `for attempt in range(max_retries)`
- [x] Использовать `try-except` внутри цикла
- [x] Вызвать `client.chat.completions.create` в `try`
- [x] Извлечь `response.choices[0].message.content` при успехе
- [x] Залогировать успех и вернуть результат
- [x] Обработать retryable ошибки (`RateLimitError`, `APIError` 5xx) в `except`
- [x] Залогировать предупреждение и номер попытки
- [x] Проверить `attempt == max_retries - 1`, залогировать ошибку, вернуть `None`
- [x] Вычислить и применить экспоненциальную задержку (`time.sleep`)
- [x] Обработать non-retryable ошибки (`AuthenticationError`, `BadRequestError`)
- [x] Залогировать критическую ошибку и вернуть `None`
- [x] Обработать общие `Exception`
- [x] Добавить финальный `return None` после цикла (на всякий случай)
- [x] *Действие пользователя:* Убедиться, что `openai` установлен (`pip install openai`)
- [x] Обновить `requirements.txt` (если `openai` не был добавлен в шаге 1)

### Шаг 7: Генерация Функций (Агент 1 - Вызов LLM)
- [x] **Модификация `src/agent_feature_generator.py`:**
    - [x] Импортировать `call_openai_api` из `src.llm_client`
    - [x] Определить константу `FEATURE_GENERATION_PROMPT` (из Приложения A)
    - [x] Определить приватный метод `_parse_features(self, llm_response)`
    - [x] Добавить docstring для `_parse_features`
    - [x] Реализовать парсинг ответа LLM (regex/split) для извлечения 'name', 'problem', 'solution'
    - [x] Вернуть список словарей `[{'name': ..., 'problem': ..., 'solution': ...}, ...]`
    - [x] Обработать ошибки парсинга, залогировать, вернуть пустой/частичный список
    - [x] **Модификация `generate_features`:**
        - [x] Проверить, что `reviews_text` не пустой
        - [x] Сформировать `full_prompt` из `FEATURE_GENERATION_PROMPT` и `reviews_text`
        - [x] Вызвать `call_openai_api(prompt=full_prompt, system_message=...)`
        - [x] Проверить, что ответ `llm_response` не `None`. Если `None`, залогировать и вернуть `[]`
        - [x] Залогировать полученный `llm_response` (или его часть)
        - [x] Вызвать `generated_features = self._parse_features(llm_response)`
        - [x] Залогировать количество `len(generated_features)`
        - [x] Вернуть `generated_features`
        - [x] Обновить финальный лог метода
- [x] **Модификация `src/main.py`:**
    - [x] Обновить логгирование результата `features`, чтобы показать реальные данные

## Фаза 3: Агент 2 - Создатель Персон

### Шаг 8: Структура Агента 2 и Подготовка Данных
- [x] Создать файл `src/agent_persona_creator.py`
- [x] Импортировать `pandas`, `logging`, `call_openai_api`
- [x] Определить класс `PersonaCreatorAgent`
- [x] Реализовать `__init__(self, api_key)`
- [x] Инициализировать логгер в `__init__`
- [x] Определить метод `create_personas(self, reviews_df, num_personas=4)`
- [x] Добавить docstring для `create_personas`
- [x] Добавить лог начала работы агента
- [x] Обработать случай пустого `reviews_df`
- [x] Реализовать подготовку данных (выбрать колонки, агрегировать/семплировать отзывы)
- [x] Создать строку `reviews_summary_text`
- [x] Залогировать информацию о подготовленных данных
- [x] Вернуть пустой список `[]` (placeholder)
- [x] Добавить лог завершения подготовки данных
- [x] **Модификация `src/main.py`:**
    - [x] Импортировать `PersonaCreatorAgent`
    - [x] Создать экземпляр `persona_agent = PersonaCreatorAgent(api_key=...)`
    - [x] Вызвать `personas = persona_agent.create_personas(reviews_df)`
    - [x] Залогировать результат `personas` (пока будет `[]`)

### Шаг 9: Генерация Описаний Персон (Агент 2 - Шаг 1 LLM)
- [x] **Модификация `src/agent_persona_creator.py`:**
    - [x] Определить `PERSONA_DESCRIPTION_PROMPT_TEMPLATE` (инструкция + примеры из Приложения B)
    - [x] Определить приватный метод `_parse_persona_descriptions(self, llm_response, num_personas)`
    - [x] Добавить docstring для `_parse_persona_descriptions`
    - [x] Реализовать парсинг нумерованного списка из ответа LLM
    - [x] Обработать ошибки парсинга
    - [x] Вернуть список строк `[description1, description2, ...]`
    - [x] **Модификация `create_personas`:**
        - [x] Сформировать промпт для LLM, используя `PERSONA_DESCRIPTION_PROMPT_TEMPLATE`
        - [x] Вызвать `call_openai_api` для генерации описаний
        - [x] Проверить ответ, залогировать ошибку, вернуть `[]` если `None`
        - [x] Вызвать `persona_descriptions = self._parse_persona_descriptions(...)`
        - [x] Залогировать количество `len(persona_descriptions)`
        - [x] Вернуть `persona_descriptions` (placeholder)
---
*Чеклист завершен. Пройдитесь по пунктам для отслеживания прогресса.*