import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Импортируем функциональность из других модулей
from app_reviews_scraper import AppReviewsScraper
from analyze_sober_reviews import run_sober_analysis

# Загружаем переменные окружения
load_dotenv()

# Проверяем наличие API ключа OpenAI
if not os.getenv("OPENAI_API_KEY"):
    print("Ошибка: OPENAI_API_KEY не найден в переменных окружения")
    print("Пожалуйста, создайте файл .env и добавьте в него строку OPENAI_API_KEY=ваш_ключ")
    sys.exit(1)

async def main():
    """Основная функция запуска пайплайна анализа отзывов"""
    print("=" * 70)
    print(f"Запуск пайплайна анализа отзывов {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Запускаем анализ отзывов приложения Sober
        await run_sober_analysis()
        
        print("\nВесь пайплайн выполнен успешно!")
        
    except Exception as e:
        print(f"\nОшибка при выполнении пайплайна: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        # Создаем директорию для выходных файлов, если она не существует
        os.makedirs('output', exist_ok=True)
        
        # Запускаем асинхронную функцию main()
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nПроцесс прерван пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {str(e)}")
        sys.exit(1) 