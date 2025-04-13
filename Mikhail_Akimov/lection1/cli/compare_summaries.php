<?php

require __DIR__ . '/../vendor/autoload.php';

use TextSummarizer\SummaryComparator;

// Проверяем аргументы командной строки
if ($argc < 2) {
    echo "Использование: php compare_summaries.php <file> [sentences]\n";
    echo "Примечание: Необходимо установить переменную окружения OPENAI_API_KEY\n";
    exit(1);
}

// Получаем API ключ
$apiKey = getenv('OPENAI_API_KEY');
if (!$apiKey) {
    echo "Ошибка: Переменная окружения OPENAI_API_KEY не установлена\n";
    echo "Установите её командой: export OPENAI_API_KEY='ваш-api-ключ'\n";
    exit(1);
}

// Получаем путь к файлу и количество предложений
$file = $argv[1];
$curPath = getcwd();
if (substr($file,0,1) != '/'){
    $file =  $curPath  . '/' . $file;
    $file = realpath($file);
}
echo "Summarize file: " . $file . PHP_EOL;

$sentences = isset($argv[2]) ? (int)$argv[2] : 3;

// Проверяем существование файла
if (!file_exists($file)) {
    echo "Error! '$file' not found\n";
    exit(1);
}

try {
    // Читаем исходный текст
    $originalText = file_get_contents($file);
    if ($originalText === false) {
        throw new Exception("Cannot read file '$file'");
    }

    // Запускаем первый скрипт суммаризации
    $output1 = [];
    $returnVar1 = 0;
    exec("php " . __DIR__ . "/summarize.php $file $sentences", $output1, $returnVar1);
    
    if ($returnVar1 !== 0) {
        throw new Exception("Error: Bad return code from summarize.php");
    }

    // Запускаем второй скрипт суммаризации
    $output2 = [];
    $returnVar2 = 0;
    exec("php " . __DIR__ . "/summarize_gpt.php $file $sentences", $output2, $returnVar2);
    
    if ($returnVar2 !== 0) {
        throw new Exception("Error: Bad return code from summarize_gpt.php");
    }

    // Извлекаем результаты суммаризации из вывода
    $summary1 = implode("\n", array_slice($output1, 4, -1));
    $summary2 = implode("\n", array_slice($output2, 4, -1));

    // Создаем экземпляр компаратора
    $comparator = new SummaryComparator($apiKey);

    // Получаем анализ результатов
    $analysis = $comparator->compareSummaries($originalText, $summary1, $summary2);

    // Выводим результаты
    echo "\nResult of summaries comparison:\n";
    echo "====================================\n";
    echo "Summary 1:\n";
    echo $summary1 . "\n";
    echo "====================================\n";
    echo "Summary 2:\n";
    echo $summary2 . "\n";
    echo "====================================\n";
    echo "Analysis:\n";
    echo $analysis . "\n";
    echo "====================================\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    exit(1);
} 