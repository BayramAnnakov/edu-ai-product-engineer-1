<?php
namespace App;


class FirecrawlApi
{
    public static $instance = null;

    public $ch = null;
    public $baseUrl; // https://api.firecrawl.dev/v1/
    public $token;

    public function __construct($params = [])
    {
        if (! empty($params['baseUrl'])) {
            $this->baseUrl = $params['baseUrl'];
        } elseif (! empty($_ENV['FIRECRAWL_URL'])) {
            $this->baseUrl = $_ENV['FIRECRAWL_URL'];
        }

        if (! empty($params['token'])) {
            $this->token = $params['token'];
        } elseif (! empty($_ENV['FIRECRAWL_API_KEY'])) {
            $this->token = $_ENV['FIRECRAWL_API_KEY'];
        }
    }

    public static function I($params = [])
    {
        if (self::$instance === null) {
            self::$instance = new self($params);
        }
        return self::$instance;
    }

    public function search($query)
    {
        $data = [
            'query' => $query,
            'limit' => 5,
            // "scrapeOptions" => [
            //     "formats" => ["markdown", "links"]
            // ]
        ];
        $results = $this->call('search', $data);
        if (isset($results['data'])) {
            return $results['data'];
        }
        return '';
    }

    public function call($action, $data = [])
    {
        $url = $this->baseUrl . $action;

        $ch = curl_init();

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer ' . $this->token,
            'Content-type: application/json'
        ]);

        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_URL, $url);

        if (false) {
            echo "\n\nURL: $url\n\n";

            ob_start();
            $curl_output = fopen('php://output', 'w');

            curl_setopt($ch, CURLOPT_VERBOSE, true);
            curl_setopt($ch, CURLOPT_STDERR, $curl_output);

            $result = curl_exec($ch); #Инициируем запрос к API и сохраняем ответ в переменную

            fclose($curl_output);
            $dump = ob_get_clean();

            $dump .= PHP_EOL . '[[POST DATA]] ' . json_encode($data) . PHP_EOL;
            $dump .= PHP_EOL . '[[RESPONSE]] ' . $result . PHP_EOL;
            echo $dump;
        } else {
            $result = curl_exec($ch);
        }
        curl_close($ch);

        return json_decode($result, true);
    }
}
