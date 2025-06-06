from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import defaultdict
import string
import time

# Загружаем необходимые ресурсы NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Загружаем переменные окружения
load_dotenv()

# Инициализируем клиент OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_assistant():
    """Создает ассистента для анализа отзывов."""
    assistant = client.beta.assistants.create(
        name="Аналитик отзывов",
        instructions="Ты - эксперт по анализу отзывов на товары. Твоя задача - анализировать отзывы, выделять ключевые моменты и предоставлять структурированные выводы.",
        model="gpt-4-turbo-preview",
        tools=[{"type": "code_interpreter"}]
    )
    return assistant

def extractive_summarization(text: str) -> str:
    """Создает экстрактивную суммаризацию отзывов, используя NLTK."""
    # Токенизация предложений
    sentences = sent_tokenize(text)
    
    # Токенизация слов и удаление стоп-слов
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words and word not in string.punctuation]
    
    # Вычисление частоты слов
    word_frequencies = FreqDist(words)
    
    # Нормализация частот
    max_frequency = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_frequency
        
    # Вычисление весов предложений
    sentence_scores = defaultdict(float)
    for i, sentence in enumerate(sentences):
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[i] += word_frequencies[word]
                
    # Выбор топ предложений (примерно 30% от общего количества)
    num_sentences = max(1, int(len(sentences) * 0.3))
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    top_sentences = sorted([i for i, _ in top_sentences])
    
    # Формирование итоговой суммаризации
    summary = [sentences[i] for i in top_sentences]
    
    # Структурирование по категориям
    categories = {
        "Преимущества": [],
        "Недостатки": [],
        "Общие впечатления": []
    }
    
    for sentence in summary:
        if any(word in sentence.lower() for word in ["good", "great", "excellent", "love", "perfect"]):
            categories["Преимущества"].append(sentence)
        elif any(word in sentence.lower() for word in ["bad", "poor", "disappointed", "problem", "issue"]):
            categories["Недостатки"].append(sentence)
        else:
            categories["Общие впечатления"].append(sentence)
    
    # Форматирование результата
    result = "Экстрактивная суммаризация отзывов:\n\n"
    for category, sentences in categories.items():
        if sentences:
            result += f"{category}:\n"
            for sentence in sentences:
                result += f"- {sentence}\n"
            result += "\n"
    
    return result

def analyze_with_assistant(assistant_id: str, text: str) -> str:
    """Анализирует текст с помощью ассистента."""
    # Создаем тред
    thread = client.beta.threads.create()
    
    # Добавляем сообщение в тред
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"""
        Проанализируй следующие отзывы на товар и создай детальный анализ:
        
        {text}
        
        Правила анализа:
        1. Обобщи основные преимущества и недостатки товара
        2. Выдели ключевые темы и тренды в отзывах
        3. Оцени общее впечатление покупателей
        4. Предоставь рекомендации на основе анализа
        5. Используй естественный язык и избегай прямого цитирования
        
        Структура ответа:
        1. Общее впечатление
        2. Основные преимущества
        3. Основные недостатки
        4. Рекомендации
        """
    )
    
    # Запускаем ассистента
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Ждем завершения выполнения
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        time.sleep(1)
    
    # Получаем ответ
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def load_reviews(file_path: str) -> str:
    """Загружает отзывы из CSV файла и объединяет их в один текст."""
    try:
        df = pd.read_csv(file_path)
        if 'Text' not in df.columns:
            raise ValueError("В файле отсутствует колонка 'Text'")
        
        # Объединяем все отзывы в один текст
        all_reviews = "\n\n".join(df['Text'].dropna().astype(str))
        return all_reviews
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return ""

def analyze_reviews(file_path: str) -> dict:
    """Анализирует отзывы, используя оба метода суммаризации."""
    # Загружаем отзывы
    reviews_text = load_reviews(file_path)
    if not reviews_text:
        return {"error": "Не удалось загрузить отзывы из файла"}
    
    # Создаем ассистента
    assistant = create_assistant()
    
    # Выполняем экстрактивную суммаризацию
    extractive_summary = extractive_summarization(reviews_text)
    
    # Выполняем анализ с помощью ассистента
    abstractive_summary = analyze_with_assistant(assistant.id, reviews_text)
    
    # Сравниваем результаты с помощью ассистента
    comparison = analyze_with_assistant(assistant.id, f"""
    Сравни следующие две суммаризации отзывов на товар и предоставь детальный анализ:
    
    Экстрактивная суммаризация (на основе NLTK):
    {extractive_summary}
    
    Абстрактивная суммаризация (на основе GPT-4):
    {abstractive_summary}
    
    Проанализируй:
    1. Насколько полно охвачены все аспекты товара в каждом подходе
    2. Какие преимущества и недостатки у каждого метода
    3. Какой подход лучше подходит для разных целей
    4. Какие рекомендации можно дать на основе анализа
    5. Какой тип суммаризации более полезен для потенциальных покупателей
    """)
    
    return {
        "extractive_summary": extractive_summary,
        "abstractive_summary": abstractive_summary,
        "comparison": comparison
    }

if __name__ == "__main__":
    # Проверяем наличие API ключа
    if not os.getenv("OPENAI_API_KEY"):
        print("Ошибка: Не найден API ключ OpenAI. Пожалуйста, создайте файл .env с переменной OPENAI_API_KEY")
        exit(1)

    # Анализируем отзывы
    results = analyze_reviews("Reviews_product.csv")
    
    # Выводим результаты
    print("\nРезультат экстрактивной суммаризации:")
    print(results["extractive_summary"])
    
    print("\nРезультат абстрактивной суммаризации:")
    print(results["abstractive_summary"])
    
    print("\nСравнительный анализ:")
    print(results["comparison"]) 