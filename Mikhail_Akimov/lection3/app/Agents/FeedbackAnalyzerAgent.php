<?php

namespace App\Agents;

use NeuronAI\Agent;
use NeuronAI\SystemPrompt;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;
use App\Logger;

// use App\Services\OpenAIService;

class FeedbackAnalyzerAgent extends Agent
{
    use \App\Traits\ProviderTrait;

    public function instructions(): string
    {
        return new SystemPrompt(
            background: [
                "Ты — ассистент для категоризации пользовательских отзывов. " .
                "bug - это жалоба на то что не работает в сервисе или описание того как не работает. " .
                "feature - это описание того что не хватает в сервисе или сравнение с конкурентом, вот у них есть, а когда у вас будет. " .
                "other - все что не попадает в bug и feature."
            ],
            steps: [
                "Категоризируй пользовательский отзыв на одну из категорий: 'bug', 'feature', 'other'"
            ],
            output: [
                "Ответ в plain_text одним словом: bug, feature или other"
            ]
        );
    }

    public function classifyCategory($feedback)
    {
        Logger::I()->log($feedback, 'user');

        $response = $this->chat(new UserMessage($feedback));
        $category = $response->getContent();

        if (is_string($category) && substr($category, 0, 1) == '{') {
            $category = json_decode($category, true);
            $category = $category['category'];
        }
        Logger::I()->log($category, 'FeedbackAnalyzerAgent');

        return $category;
    }
}
