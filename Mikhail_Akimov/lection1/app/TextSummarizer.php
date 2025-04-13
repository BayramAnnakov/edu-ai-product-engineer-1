<?php

namespace TextSummarizer;

class TextSummarizer
{
    /**
     * Создает краткое содержание текста
     * @param string $text Исходный текст
     * @param int $sentences Количество предложений в кратком содержании
     * @return string Краткое содержание
     */
    public function summarize(string $text, int $sentences = 3): string
    {
        // Разбиваем текст на предложения
        $sentencesArray = $this->splitIntoSentences($text);
        
        if (count($sentencesArray) <= $sentences) {
            return $text;
        }
        
        // Получаем частотное распределение слов
        $wordFrequencies = $this->calculateWordFrequencies($text);
        
        // Рассчитываем оценку важности для каждого предложения
        $scores = $this->calculateSentenceScores($sentencesArray, $wordFrequencies);
        
        // Сортируем предложения по важности
        arsort($scores);
        
        // Выбираем топ-N предложений
        $selectedSentences = array_slice(array_keys($scores), 0, $sentences);
        
        // Сортируем выбранные предложения по их исходному порядку
        sort($selectedSentences);
        
        // Собираем итоговый текст
        $summary = [];
        foreach ($selectedSentences as $index) {
            $summary[] = $sentencesArray[$index];
        }
        
        return implode(' ', $summary);
    }
    
    /**
     * Разбивает текст на предложения
     */
    private function splitIntoSentences(string $text): array
    {
        // Заменяем переносы строк на пробелы
        $text = preg_replace('/\s+/', ' ', $text);
        
        // Разбиваем на предложения (учитываем . ! ? и сохраняем аббревиатуры)
        $sentences = preg_split('/(?<=[.!?])\s+(?=[A-ZА-Я])/', $text, -1, PREG_SPLIT_NO_EMPTY);
        
        return array_map('trim', $sentences);
    }
    
    /**
     * Рассчитывает частоту слов в тексте
     */
    private function calculateWordFrequencies(string $text): array
    {
        // Приводим к нижнему регистру
        $text = mb_strtolower($text);
        
        // Удаляем пунктуацию
        $text = preg_replace('/[^\p{L}\s]/u', '', $text);
        
        // Разбиваем на слова
        $words = preg_split('/\s+/', $text, -1, PREG_SPLIT_NO_EMPTY);
        
        // Считаем частоту слов
        $frequencies = array_count_values($words);
        
        // Сортируем по убыванию частоты
        arsort($frequencies);
        
        return $frequencies;
    }
    
    /**
     * Рассчитывает оценку важности для каждого предложения
     */
    private function calculateSentenceScores(array $sentences, array $wordFrequencies): array
    {
        $scores = [];
        $totalSentences = count($sentences);
        
        foreach ($sentences as $index => $sentence) {
            // Приводим предложение к нижнему регистру
            $sentence = mb_strtolower($sentence);
            
            // Удаляем пунктуацию
            $sentence = preg_replace('/[^\p{L}\s]/u', '', $sentence);
            
            // Разбиваем на слова
            $words = preg_split('/\s+/', $sentence, -1, PREG_SPLIT_NO_EMPTY);
            
            // Считаем общий вес слов в предложении
            $score = 0;
            foreach ($words as $word) {
                $score += $wordFrequencies[$word] ?? 0;
            }
            
            // Нормализуем оценку по длине предложения
            if (count($words) > 0) {
                $score = $score / count($words);
            }
            
            // Учитываем позицию предложения (первые и последние предложения важнее)
            $positionScore = 1;
            if ($index < $totalSentences * 0.2) { // Первые 20% предложений
                $positionScore = 1.5;
            } elseif ($index > $totalSentences * 0.8) { // Последние 20% предложений
                $positionScore = 1.2;
            }
            
            $scores[$index] = $score * $positionScore;
        }
        
        return $scores;
    }
} 