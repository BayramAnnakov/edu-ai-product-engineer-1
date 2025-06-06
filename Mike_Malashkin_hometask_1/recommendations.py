import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

class Recommendations:
    def __init__(self):
        """Инициализация клиента OpenAI"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Инициализируем клиент OpenAI с базовыми параметрами
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
    
    def get_latest_discussion_file(self):
        """Находит самый свежий файл с результатами дискуссии"""
        files = [f for f in os.listdir('output') if f.startswith("discussion_")]
        if not files:
            raise FileNotFoundError("Файл с результатами дискуссии не найден")
        return max(files, key=lambda x: os.path.getctime(os.path.join('output', x)))
    
    def load_discussion_data(self, file_path=None):
        """Загружает данные дискуссии из файла"""
        if not file_path:
            file_path = self.get_latest_discussion_file()
        
        print(f"Загрузка данных дискуссии из файла: {file_path}")
        try:
            with open(os.path.join('output', file_path), "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Ошибка при загрузке файла: {str(e)}")
            return None
    
    def generate_improvements(self, discussion_data):
        """Генерирует рекомендации по улучшению на основе дискуссии"""
        if not discussion_data:
            print("Нет данных для анализа")
            return None
            
        # Собираем все высказывания из групповой дискуссии
        all_messages = []
        for message in discussion_data.get("group_discussion", []):
            # Добавляем имя агента к сообщению для лучшего понимания контекста
            agent_name = message.get("agent", "Unknown")
            content = message.get("content", "")
            all_messages.append(f"[{agent_name}]: {content}")
        
        if not all_messages:
            print("В дискуссии нет сообщений для анализа")
            return None
        
        # Объединяем все сообщения в одну строку для анализа
        full_discussion = "\n\n".join(all_messages)
        
        # Определяем тип объекта и его название
        item_type = discussion_data.get("item_type", "unknown")
        topic = discussion_data.get("topic", "Критерии выбора")
        item_name = discussion_data.get("item_name", None)
        
        # Используем имя объекта или его тип, если имя не задано
        object_name = item_name if item_name and item_name.lower() != "none" else item_type
        
        # Формируем универсальный промпт
        system_prompt = "Ты - эксперт по анализу групповых дискуссий и выделению ключевых инсайтов для улучшения"
        prompt = f"""Проанализируй следующую групповую дискуссию на тему "{topic}" и 
        выдели 2-3 ключевых предложения по улучшению {object_name}.
        
        Особое внимание удели конкретным требованиям и аспектам, упомянутым в дискуссии.
        Выдели только самые значимые и повторяющиеся мнения участников дискуссии.
        
        Твой ответ должен быть в формате:
        
        КЛЮЧЕВЫЕ ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:
        1. [Первое предложение]
        2. [Второе предложение]
        3. [Третье предложение, если есть]
        
        Дискуссия:
        {full_discussion}
        """
        
        # Отправляем запрос к OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Ошибка при генерации рекомендаций: {str(e)}")
            return None
    
    def analyze_discussion(self, file_path=None):
        """Основной метод для анализа дискуссии и генерации рекомендаций"""
        try:
            # Загрузка данных
            data = self.load_discussion_data(file_path)
            if not data:
                return None
            
            # Получаем тип объекта
            item_type = data.get("item_type", "unknown")
            item_name = data.get("item_name", "объекта")
            
            # Определяем название объекта для вывода
            display_name = item_name if item_name and item_name.lower() != "none" else item_type
            
            # Генерация рекомендаций
            print(f"Генерация рекомендаций по улучшению: {display_name}")
            improvements = self.generate_improvements(data)
            
            if improvements:
                # Сохранение результатов
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"improvements_{timestamp}.txt"
                
                with open(os.path.join('output', output_file), "w", encoding="utf-8") as f:
                    f.write(improvements)
                
                print(f"Рекомендации сохранены в файл: {output_file}")
                
                # Также выводим результат в консоль
                print("\nРЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
                print(improvements)
                
                return output_file
            
            return None
            
        except Exception as e:
            print(f"Ошибка при анализе дискуссии: {str(e)}")
            return None

    def analyze_from_classified_data(self, analysis_data):
        """Анализирует данные классифицированных отзывов и создает рекомендации
        
        Args:
            analysis_data: Данные анализа (суммаризированные отзывы и результаты дискуссий)
            
        Returns:
            str: Имя файла с рекомендациями
        """
        print("Генерация рекомендаций на основе классифицированных отзывов...")
        
        # Создаем структуру для хранения всех аспектов анализа
        all_aspects = {
            "bug_fixes": [],
            "feature_improvements": [],
            "ux_improvements": [],
            "performance_improvements": [],
            "stability_improvements": []
        }
        
        # Обрабатываем отчеты о багах
        if 'bug_reports' in analysis_data and analysis_data['bug_reports']['summarized']:
            for bug_group in analysis_data['bug_reports']['summarized']:
                # Если это не словарь, пропускаем
                if not isinstance(bug_group, dict):
                    continue
                    
                # Извлекаем информацию о группе багов
                group_name = bug_group.get('group_name', 'Неизвестная проблема')
                summary = bug_group.get('summary', 'Нет описания')
                count = bug_group.get('count', 1)
                
                # Добавляем в соответствующий раздел
                all_aspects["bug_fixes"].append({
                    "issue": group_name,
                    "description": summary,
                    "count": count,
                    "priority": "high" if count > 3 else "medium"
                })
        
        # Обрабатываем запросы функций
        if 'feature_requests' in analysis_data and analysis_data['feature_requests']['summarized']:
            for feature_group in analysis_data['feature_requests']['summarized']:
                # Если это не словарь, пропускаем
                if not isinstance(feature_group, dict):
                    continue
                    
                # Извлекаем информацию о группе запросов
                group_name = feature_group.get('group_name', 'Неизвестная функция')
                summary = feature_group.get('summary', 'Нет описания')
                count = feature_group.get('count', 1)
                
                # Добавляем в соответствующий раздел
                all_aspects["feature_improvements"].append({
                    "feature": group_name,
                    "description": summary,
                    "count": count,
                    "priority": "high" if count > 3 else "medium"
                })
        
        # Добавляем данные из дискуссий, если они есть
        if 'bug_discussion_summary' in analysis_data and analysis_data['bug_discussion_summary']:
            # Обрабатываем результаты дискуссии о багах
            self._extract_discussion_insights(
                analysis_data['bug_discussion_summary'],
                all_aspects,
                "stability_improvements"
            )
            
        if 'feature_discussion_summary' in analysis_data and analysis_data['feature_discussion_summary']:
            # Обрабатываем результаты дискуссии о функциях
            self._extract_discussion_insights(
                analysis_data['feature_discussion_summary'],
                all_aspects,
                "ux_improvements"
            )
        
        # Формируем итоговые рекомендации
        recommendations = self._generate_final_recommendations(all_aspects)
        
        # Сохраняем результаты в файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"final_recommendations_{timestamp}.json"
        
        try:
            with open(os.path.join('output', result_file), 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, ensure_ascii=False, indent=2)
            
            print(f"Рекомендации сохранены в файл: {result_file}")
            return result_file
            
        except Exception as e:
            print(f"Ошибка при сохранении рекомендаций: {str(e)}")
            return None
    
    def _extract_discussion_insights(self, discussion_text, all_aspects, aspect_key):
        """Извлекает инсайты из текста дискуссии
        
        Args:
            discussion_text: Текст дискуссии или резюме
            all_aspects: Словарь со всеми аспектами рекомендаций
            aspect_key: Ключ для добавления инсайтов
        """
        # Проверяем, что текст дискуссии не пустой
        if not discussion_text:
            return
            
        # Разбиваем текст дискуссии на строки
        lines = discussion_text.strip().split('\n')
        
        # Ищем строки с предложениями (обычно они начинаются с цифр)
        suggestions = []
        
        for line in lines:
            # Если строка начинается с цифры или содержит характерные маркеры
            if (line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))):
                suggestions.append(line.strip())
        
        # Добавляем найденные предложения в соответствующий раздел
        for i, suggestion in enumerate(suggestions):
            # Убираем цифры и символы в начале строки
            clean_suggestion = suggestion
            while clean_suggestion and (clean_suggestion[0].isdigit() or clean_suggestion[0] in '.-:) '):
                clean_suggestion = clean_suggestion[1:].strip()
                
            if clean_suggestion:
                all_aspects[aspect_key].append({
                    "improvement": f"Обсуждение {i+1}",
                    "description": clean_suggestion,
                    "source": "discussion",
                    "priority": "medium"
                })
    
    def _generate_final_recommendations(self, all_aspects):
        """Генерирует финальные рекомендации на основе всех аспектов
        
        Args:
            all_aspects: Словарь со всеми аспектами рекомендаций
            
        Returns:
            dict: Структурированные рекомендации
        """
        # Создаем структуру для рекомендаций
        recommendations = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_issues": len(all_aspects["bug_fixes"]),
                "total_feature_requests": len(all_aspects["feature_improvements"]),
                "total_ux_improvements": len(all_aspects["ux_improvements"]),
                "total_performance_improvements": len(all_aspects["performance_improvements"]),
                "total_stability_improvements": len(all_aspects["stability_improvements"])
            },
            "high_priority_recommendations": [],
            "medium_priority_recommendations": [],
            "low_priority_recommendations": []
        }
        
        # Обрабатываем каждый аспект и добавляем рекомендации
        priority_mapping = {
            "bug_fixes": "high",
            "feature_improvements": "medium",
            "ux_improvements": "medium",
            "performance_improvements": "medium",
            "stability_improvements": "high"
        }
        
        for aspect_key, items in all_aspects.items():
            default_priority = priority_mapping.get(aspect_key, "medium")
            
            for item in items:
                priority = item.get("priority", default_priority)
                
                recommendation = {
                    "category": aspect_key,
                    "title": item.get("issue", item.get("feature", item.get("improvement", "Рекомендация"))),
                    "description": item.get("description", "Нет описания"),
                    "user_impact": "high" if priority == "high" else "medium",
                    "implementation_complexity": "medium"  # По умолчанию средняя сложность
                }
                
                # Добавляем рекомендацию в соответствующий раздел по приоритету
                if priority == "high":
                    recommendations["high_priority_recommendations"].append(recommendation)
                elif priority == "medium":
                    recommendations["medium_priority_recommendations"].append(recommendation)
                else:
                    recommendations["low_priority_recommendations"].append(recommendation)
        
        # Сортируем рекомендации по категориям внутри приоритетов
        for priority_list in ["high_priority_recommendations", "medium_priority_recommendations", "low_priority_recommendations"]:
            recommendations[priority_list] = sorted(recommendations[priority_list], key=lambda x: x["category"])
        
        return recommendations

if __name__ == "__main__":
    # Пример использования
    analyzer = Recommendations()
    analyzer.analyze_discussion() 