<?php

namespace App\Agents;

use NeuronAI\Agent;
use NeuronAI\SystemPrompt;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;
use App\Logger;

// use App\Services\OpenAIService;

class FeedbackToFeatureAgent extends Agent
{
    use \App\Traits\ProviderTrait;

    public function instructions(): string
    {
        return new SystemPrompt(
            background: [
                "Ты исследователь, продукт-менеджер, исследуешь фичи в интернете, делаешь анализ и выводы."
            ],
            steps: [
                "Из отзыва пользователя выдели часть, которая описывает фичу сформулируй ее развернуто"
            ],
            output: [
                "Ответ в plain_text"
            ]
        );
    }

    public function makeSense($feedback)
    {
        $response = $this->chat(new UserMessage($feedback));
        $feature = $response->getContent();

        if (is_string($feature) && substr($feature, 0, 1) == '{') {
            $feature = json_decode($feature, true);
            $feature = implode('; ', $feature);
        }
        Logger::I()->log("User: " . $feedback . "\n ---> \nFeature: " . $feature, 'Feedback2Feature');

        return $feature;
    }
}
