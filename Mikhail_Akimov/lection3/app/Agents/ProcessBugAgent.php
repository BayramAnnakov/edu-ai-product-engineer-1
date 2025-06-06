<?php
namespace App\Agents;

use NeuronAI\Agent;
use NeuronAI\Tools\Tool;
use NeuronAI\SystemPrompt;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;

use App\Tools\SearchYoutrackIssueTool;
use App\Tools\AddCommentToYoutrackIssueTool;
use App\Tools\CreateYoutrackIssueTool;
use App\Logger;

class ProcessBugAgent extends Agent
{

    use \App\Traits\ProviderTrait;

    public function instructions(): string
    {
        return new SystemPrompt(
            background: [
                "Ты агент поддержки, который обрабатывает баг-репорты пользователей.",
            ],
            steps: [
                "Из отзыва пользователя выдели часть, которая описывает баг - это описание бага (description) из него нужно сделать выжимку (summary) которое потом будем использовать в тикете в качестве названия",
                "Используй tools для поиска багов в YouTrack.",
                "Если получили список в формате json с такими параметрами [{issueid: id, summary: text, description: text2, created: date}], то сообщим о том что такой баг уже заведен и выведи его номер.",
                "Если баг не найден — создай новый тикет в YouTrack.",
                "Верни пользователю ссылку на тикет и статус обращения."
            ]
        );
    }

    public function tools(): array
    {
        return [
            SearchYoutrackIssueTool::make(),
            AddCommentToYoutrackIssueTool::make(),
            CreateYoutrackIssueTool::make(),
        ];
    }
}