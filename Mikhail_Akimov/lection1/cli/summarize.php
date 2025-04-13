<?php

require __DIR__ . '/../vendor/autoload.php';

use TextSummarizer\TextSummarizer;

// Проверяем, передан ли аргумент с путем к файлу
if ($argc < 2) {
    echo "Usage: php summarize.php <file> [sentences]\n";
    exit(1);
}

// Получаем путь к файлу из аргументов
$file = $argv[1];
$curPath = getcwd();
if (substr($file,0,1) != '/'){
    $file =  $curPath  . '/' . $file;
    $file = realpath($file);
}
echo "Summarize file: $file" . PHP_EOL;


// Получаем количество предложений (по умолчанию 3)
$sentences = isset($argv[2]) ? (int)$argv[2] : 3;

// Проверяем существование файла
if (!file_exists($file)) {
    echo "Error: File '$file' not found\n";
    exit(1);
}

try {

    // Читаем содержимое файла
    $text = file_get_contents($file);

    if ($text === false) {
        throw new Exception("Could not read file '$file'");
    }
    
    // Создаем экземпляр суммаризатора
    $summarizer = new TextSummarizer();
    
    // Получаем краткое содержание
    $summary = $summarizer->summarize($text, $sentences);
    
    // Выводим результат
    echo "\nShort summary ({$sentences} sentences):\n";
    echo "----------------------------------------\n";
    echo $summary . "\n";
    echo "----------------------------------------\n";
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    exit(1);
} 