<?php

require __DIR__ . '/vendor/autoload.php';

use App\Services\OpenAIService;
use App\Agents\FeedbackAnalyzerAgent;
use App\Agents\ProcessBugAgent;
use App\Agents\ProcessResearchAgent;
use NeuronAI\Chat\Messages\UserMessage;
use App\Logger;

// Загрузка переменных окружения
$dotenv = \Dotenv\Dotenv::createImmutable(__DIR__ . '/', '.env');
$dotenv->safeLoad();
$dotenv->required([
    'OPENAI_API_KEY',
    'YOUTRACK_TOKEN',
    'FIRECRAWL_API_KEY',
    'CHAT_WEBHOOK_URL'
])->notEmpty();

// Проверка наличия API ключа
if (!$_ENV['OPENAI_API_KEY']) {
    die("Ошибка: Не установлен OPENAI_API_KEY в файле .env\n");
}

// Проверка аргументов командной строки
if ($argc < 2) {
    fwrite(STDERR, "Использование: php app.php <путь_к_файлу_отзывов>\n");
    exit(1);
}

$filePath = $argv[1];

if (!file_exists($filePath)) {
    fwrite(STDERR, "Файл не найден: $filePath\n");
    exit(1);
}

$feedbacks = file($filePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

if (!$feedbacks) {
    fwrite(STDERR, "Файл пуст или не удалось прочитать: $filePath\n");
    exit(1);
}

$analyzer = new FeedbackAnalyzerAgent();
$bugAgent = new ProcessBugAgent();
$researchAgent = new ProcessResearchAgent();

// Пока просто выводим отзывы
foreach ($feedbacks as $feedback) {
    $category = $analyzer->classifyCategory($feedback);

    switch ($category) {
        case 'bug':
            $response = $bugAgent->chat(new UserMessage($feedback));
            Logger::I()->log($response->getContent(), 'bug');
            break;

        case 'feature':
            $response = $researchAgent->chat(new UserMessage($feedback));
            Logger::I()->log($response->getContent(), 'feature');
            exit;
            break;

        default:
            Logger::I()->log($feedback, 'other');
            break;
    }

    echo "\n";
} 