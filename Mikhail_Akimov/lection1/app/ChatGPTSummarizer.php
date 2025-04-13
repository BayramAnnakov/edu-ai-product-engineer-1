<?php

namespace TextSummarizer;

class ChatGPTSummarizer
{
    private string $apiKey;
    private string $apiUrl = 'https://api.openai.com/v1/chat/completions';
    
    public function __construct(string $apiKey)
    {
        $this->apiKey = $apiKey;
    }
    
    /**
     * Создает краткое содержание текста с помощью ChatGPT
     * @param string $text Исходный текст
     * @param int $sentences Желаемое количество предложений
     * @return string Краткое содержание
     */
    public function summarize(string $text, int $sentences = 3): string
    {
        $prompt = sprintf(
            "Пожалуйста, создай краткое содержание следующего текста в %d предложениях. " .
            "Сохрани основные идеи и ключевые моменты. Текст:\n\n%s",
            $sentences,
            $text
        );
        
        try {
            $response = $this->makeRequest([
                'model' => 'gpt-3.5-turbo',
                'messages' => [
                    ['role' => 'system', 'content' => 'Ты - эксперт по созданию кратких содержаний текстов. Твоя задача - создавать четкие и информативные краткие содержания, сохраняя основной смысл и ключевые идеи исходного текста.'],
                    ['role' => 'user', 'content' => $prompt]
                ],
                'temperature' => 0.7,
                'max_tokens' => 500
            ]);
            
            return trim($response['choices'][0]['message']['content']);
            
        } catch (\Exception $e) {
            throw new \RuntimeException(
                "Ошибка при получении ответа от ChatGPT: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Выполняет запрос к API OpenAI
     * @param array $data Данные запроса
     * @return array Ответ от API
     */
    private function makeRequest(array $data): array
    {
        $ch = curl_init($this->apiUrl);
        
        if ($ch === false) {
            throw new \RuntimeException('Cannot initialize cURL');
        }
        
        $headers = [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $this->apiKey
        ];
        
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_SSL_VERIFYPEER => true
        ]);
        
        $response = curl_exec($ch);
        
        if ($response === false) {
            $error = curl_error($ch);
            curl_close($ch);
            throw new \RuntimeException('cURL error: ' . $error);
        }
        
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            throw new \RuntimeException('API returned error code: ' . $httpCode . '('.$response.')');
        }
        
        $result = json_decode($response, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new \RuntimeException('Ошибка при разборе JSON ответа: ' . json_last_error_msg());
        }
        
        return $result;
    }
} 