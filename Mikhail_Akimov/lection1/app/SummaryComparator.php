<?php

namespace TextSummarizer;

use OpenAI\Client as OpenAIClient;
use OpenAI\Transporters\HttpTransporter;
use GuzzleHttp\Client as GuzzleClient;
use OpenAI\ValueObjects\ApiKey;
use OpenAI\ValueObjects\Transporter\BaseUri;
use OpenAI\ValueObjects\Transporter\Headers;
use OpenAI\ValueObjects\Transporter\QueryParams;
use OpenAI\ValueObjects\Transporter\Payload;
use OpenAI\Enums\Transporter\Method;


class SummaryComparator {
    private $openai;
    private $apiKey;

    public function __construct($apiKey) {
        $this->apiKey = $apiKey;
        $httpClient = new GuzzleClient();
        $baseUri = BaseUri::from('https://api.openai.com/v1');
        $headers = Headers::withAuthorization(ApiKey::from($apiKey));
        $queryParams = QueryParams::create();
        
        $transporter = new HttpTransporter(
            $httpClient,
            $baseUri,
            $headers,
            $queryParams,
            function ($request) {
                return $request;
            }
        );
        
        $this->openai = new OpenAIClient($transporter);
    }

    public function compareSummaries($originalText, $summary1, $summary2) {
        $prompt = "Проанализируйте два варианта краткого содержания текста и определите, какой из них лучше и почему.\n\n";
        $prompt .= "Исходный текст:\n{$originalText}\n\n";
        $prompt .= "Вариант 1:\n{$summary1}\n\n";
        $prompt .= "Вариант 2:\n{$summary2}\n\n";
        $prompt .= "Пожалуйста, предоставьте подробный анализ, включая:\n";
        $prompt .= "1. Какой вариант лучше и почему\n";
        $prompt .= "2. Какие ключевые моменты были сохранены/упущены в каждом варианте\n";
        $prompt .= "3. Насколько точно передается смысл исходного текста\n";
        $prompt .= "4. Какие особенности каждого подхода к суммаризации\n";

        $response = $this->openai->chat()->create([
            'model' => 'gpt-4',
            'messages' => [
                ['role' => 'system', 'content' => 'Вы - эксперт по анализу текстовых суммаризаций.'],
                ['role' => 'user', 'content' => $prompt]
            ],
            'temperature' => 0.7,
            'max_tokens' => 1000
        ]);

        return $response->choices[0]->message->content;
    }
}