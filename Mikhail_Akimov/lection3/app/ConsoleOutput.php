<?php
namespace App;

class ConsoleOutput
{
    public static function wrapText($text, $maxLength)
    {
        $result = [];
        $currentLine = '';
        $words = preg_split('/([\s,.;:!?]+)/u', $text, -1, PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_EMPTY);
        
        foreach ($words as $word) {
            if (mb_strlen($currentLine . $word) <= $maxLength) {
                $currentLine .= $word;
            } else {
                if (!empty($currentLine)) {
                    $result[] = trim($currentLine);
                }
                $currentLine = $word;
            }
        }
        
        if (!empty($currentLine)) {
            $result[] = trim($currentLine);
        }
        
        return $result;
    }

    public static function printBoxed($text)
    {
        $terminalWidth = self::getTerminalWidth();

        $paragraphs = explode("\n", $text);
        $maxLen = 0;
        foreach ($lines as $line) {
            $len = mb_strlen($line);
            if ($len > $maxLen) $maxLen = $len;
        }

        if($maxLen > $terminalWidth-4) {
            $maxLen = $terminalWidth-4;
        }

        $lines = [];
        foreach ($paragraphs as $paragraph) {
            $wrappedLines = self::wrapText($paragraph, $maxLen);
            $lines = array_merge($lines, $wrappedLines);
        }
        // $maxLen = 0;
        // foreach ($lines as $line) {
        //     $len = mb_strlen($line);
        //     if ($len > $maxLen) {
        //         $maxLen = $len;
        //     }
        // }
        $horizontal = '─';
        $vertical = '│';
        $corner_tl = '┌';
        $corner_tr = '┐';
        $corner_bl = '└';
        $corner_br = '┘';

        echo $corner_tl . str_repeat($horizontal, $maxLen + 2) . $corner_tr . PHP_EOL;
        foreach ($lines as $line) {
            $pad = $maxLen - mb_strlen($line);
            echo $vertical . ' ' . $line . str_repeat(' ', $pad) . ' ' . $vertical . PHP_EOL;
        }
        echo $corner_bl . str_repeat($horizontal, $maxLen + 2) . $corner_br . PHP_EOL;
    }

    public static function printTwoColumn($first, $two)
    {
        $firstLen = mb_strlen($first);
        $terminalWidth = self::getTerminalWidth();
        $maxLen = $terminalWidth - $firstLen - 7;

        // Разбиваем текст на строки с учетом переносов
        $lines = [];
        $paragraphs = explode("\n", $two);
        foreach ($paragraphs as $paragraph) {
            $wrappedLines = self::wrapText($paragraph, $maxLen);
            $lines = array_merge($lines, $wrappedLines);
        }

        $horizontal = '─';
        $vertical = '│';
        $corner_tl = '┌';
        $corner_tr = '┐';
        $corner_bl = '└';
        $corner_br = '┘';
        $cross = '┼';
        $cross_t = '┬';
        $cross_b = '┴';
        $cross_l = '├';
        $cross_r = '┤';
        
        echo $corner_tl . str_repeat($horizontal, $firstLen + 2) . $cross_t . str_repeat($horizontal, $maxLen + 2) . $corner_tr . PHP_EOL;
        echo $vertical . ' ' . $first . ' ' . $vertical . ' ' . $lines[0] . str_repeat(' ', $maxLen - mb_strlen($lines[0])) . ' ' . $vertical . PHP_EOL;
        for ($i = 1; $i < count($lines); $i++) {
            echo $vertical . ' ' . str_repeat(' ', $firstLen) . ' ' . $vertical . ' ' . $lines[$i] . str_repeat(' ', $maxLen - mb_strlen($lines[$i])) . ' ' . $vertical . PHP_EOL;
        }
        echo $corner_bl . str_repeat($horizontal, $firstLen + 2) . $cross_b . str_repeat($horizontal, $maxLen + 2) . $corner_br . PHP_EOL;
    }

    public static function getTerminalWidth()
    {
        if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
            $output = [];
            exec('mode con', $output);
            foreach ($output as $line) {
                if (preg_match('/Columns:\s+(\d+)/', $line, $matches)) {
                    return (int)$matches[1];
                }
            }
        } else {
            $width = exec('tput cols');
            return (int)$width;
        }
        return 80; // значение по умолчанию
    }
}