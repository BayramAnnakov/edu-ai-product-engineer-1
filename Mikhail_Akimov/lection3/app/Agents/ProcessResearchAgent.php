<?php
namespace App\Agents;

use NeuronAI\Agent;
use NeuronAI\Tools\Tool;
use NeuronAI\SystemPrompt;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;

use App\Tools\SearchContentInInternetTool;
use App\Tools\SendMessageToChatTool;
use App\Tools\MakeSenseOutOfTheFeatureDescriptionTool;
use App\Logger;

class ProcessResearchAgent extends Agent
{
    use \App\Traits\ProviderTrait;

    public function instructions(): string
    {
        return new SystemPrompt(
            background: [
                "Ты исследователь, продукт-менеджер, исследуешь фичи в интернете, делаешь анализ и выводы.",
            ],
            steps: [
                "Из отзыва пользователя выдели часть, которая описывает фичу сформулируй ее развернуто.",
                "Составь исследовательский план конкурентного анализа этой фичи или похожей в интернете. Выведи план в виде списка.",
                "Начни выполнять этот план и сообщай результат каждого этапа плана",
                "Сделай вывод по результату исследования и отправь его сообщением в Гугл-чат с просьбой к продакт-менеджеру проверить и утвердить"
            ]
        );
    }

    public function tools(): array
    {
        return [
            MakeSenseOutOfTheFeatureDescriptionTool::make(),
            SearchContentInInternetTool::make(),
            SendMessageToChatTool::make()
        ];
    }
}
