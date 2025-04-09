import pandas as pd
import json
from summarization import extractive_summarize, abstractive_summarize
from analysis import analyze_summarization_methods
from datetime import datetime
import os

def process_reviews():
    """Process reviews from the Reviews.csv file."""
    try:
        # Load the CSV file
        df = pd.read_csv("Reviews.csv")
        
        # Take first 50 reviews
        reviews = df.head(50)
        
        # Process each review
        results = []
        for idx, row in reviews.iterrows():
            review_text = row['Text']
            
            # Generate summaries
            print(f"Processing review {idx + 1}/50...")
            extractive = extractive_summarize(review_text)
            abstractive = abstractive_summarize(review_text)
            
            results.append({
                'review_id': idx,
                'original_text': review_text,
                'extractive_summary': extractive,
                'abstractive_summary': abstractive
            })
        
        # Save results to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"summarized_reviews_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error processing reviews: {str(e)}")
        return None

def analyze_results(results):
    """Analyze the effectiveness of both summarization approaches."""
    analysis = {
        "total_reviews": len(results),
        "average_scores": {
            "extractive": {
                "length_preservation": 0,
                "key_info_retention": 0
            },
            "abstractive": {
                "conciseness": 0,
                "readability": 0
            }
        },
        "comparison": {
            "extractive_advantages": [],
            "abstractive_advantages": [],
            "best_use_cases": {
                "extractive": [],
                "abstractive": []
            }
        },
        "final_recommendation": ""
    }
    
    # Analyze each review's summaries
    for result in results:
        # Compare lengths
        original_length = len(result['original_text'].split())
        extractive_length = len(result['extractive_summary'].split())
        abstractive_length = len(result['abstractive_summary'].split())
        
        # Update metrics
        analysis["average_scores"]["extractive"]["length_preservation"] += extractive_length / original_length
        analysis["average_scores"]["extractive"]["key_info_retention"] += 1 if len(result['extractive_summary']) > 0 else 0
        
        analysis["average_scores"]["abstractive"]["conciseness"] += abstractive_length / original_length
        analysis["average_scores"]["abstractive"]["readability"] += 1 if len(result['abstractive_summary']) > 0 else 0
    
    # Calculate averages
    for method in ["extractive", "abstractive"]:
        for metric in analysis["average_scores"][method]:
            analysis["average_scores"][method][metric] /= len(results)
    
    # Add general observations
    analysis["comparison"]["extractive_advantages"] = [
        "Сохраняет оригинальные формулировки и контекст",
        "Более точное представление фактической информации",
        "Меньше риск искажения смысла"
    ]
    
    analysis["comparison"]["abstractive_advantages"] = [
        "Создает более краткие и читабельные резюме",
        "Лучше обобщает основные идеи",
        "Более естественное звучание текста"
    ]
    
    analysis["comparison"]["best_use_cases"]["extractive"] = [
        "Технические документы и спецификации",
        "Юридические тексты",
        "Научные статьи"
    ]
    
    analysis["comparison"]["best_use_cases"]["abstractive"] = [
        "Обзоры продуктов",
        "Новостные статьи",
        "Художественные тексты"
    ]
    
    # Final recommendation based on analysis
    if analysis["average_scores"]["abstractive"]["conciseness"] < analysis["average_scores"]["extractive"]["length_preservation"]:
        analysis["final_recommendation"] = """
        На основе анализа отзывов, абстрактивный метод показал себя более эффективным для данного типа текстов.
        Он создает более краткие и читабельные резюме, сохраняя при этом основной смысл отзывов.
        Особенно хорошо этот метод работает с отзывами о продуктах, где важно передать общее впечатление.
        """
    else:
        analysis["final_recommendation"] = """
        Анализ показывает, что экстрактивный метод более подходит для данного набора отзывов.
        Он лучше сохраняет важные детали и специфическую информацию о продуктах.
        Этот метод особенно полезен, когда точность и сохранение оригинальных формулировок имеют первостепенное значение.
        """
    
    return analysis

if __name__ == "__main__":
    # Process the reviews
    print("Starting review processing...")
    results = process_reviews()
    
    if results:
        print(f"Processed {len(results)} reviews successfully!")
    else:
        print("Failed to process reviews.") 