<?php
namespace App;

use App\ConsoleOutput;

class Logger
{
    public static $instance = null;
    public $logFile = 'log.txt';

    public function __construct($params = [])
    {
        if (! empty($params['logFile'])) {
            $this->logFile = $params['logFile'];
        }
    }

    public static function I($params = [])
    {
        if (self::$instance === null) {
            self::$instance = new self($params);
        }
        return self::$instance;
    }


    public function log($message, $speaker = 'system')
    {
        //echo  str_pad($speaker .  ': ', 20, ' ', STR_PAD_RIGHT) . $message . "\n";
        ConsoleOutput::printTwoColumn($speaker, $message);

        file_put_contents($this->logFile, '[' . date('Y-m-d H:i:s') . '] ' . str_pad($speaker .  ': ', 20, ' ', STR_PAD_RIGHT) . $message . "\n", FILE_APPEND);
    }
}