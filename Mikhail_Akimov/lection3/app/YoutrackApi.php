<?php
namespace App;


class YoutrackApi
{
    public static $instance = null;

    public $ch = null;
    public $baseUrl; // https://youtrack.com/api/
    public $token;

    public function __construct($params = [])
    {
        if (! empty($params['baseUrl'])) {
            $this->baseUrl = $params['baseUrl'];
        } elseif (! empty($_ENV['YOUTRACK_URL'])) {
            $this->baseUrl = $_ENV['YOUTRACK_URL'];
        }

        if (! empty($params['token'])) {
            $this->token = $params['token'];
        } elseif (! empty($_ENV['YOUTRACK_TOKEN'])) {
            $this->token = $_ENV['YOUTRACK_TOKEN'];
        }
    }

    public static function I($params = [])
    {
        if (self::$instance === null) {
            self::$instance = new self($params);
        }
        return self::$instance;
    }

    public function createIssue($projectId, $summary, $description)
    {
        $data = json_encode([
            'project' => ['id' => $projectId],
            'summary' => $summary,
            'description' => $description
        ]);

        return $this->call('issues', $data, 'POST');
    }

    public function searchIssues($query)
    {
        $data =
            'fields=id,summary,description,numberInProject,project,created' .
            '&$top=1' .
            '&query=' . urlencode($query)
        ;

        $results = $this->call('issues', $data, 'GET');

        return $results;
    }

    public function addComment($issueId, $comment)
    {
        $data = json_encode([
            'text' => $comment
        ]);

        return $this->call('issues/' . $issueId . '/comments', $data, 'POST');
    }

    public function call($action, $data = [], $method = 'POST')
    {
        $url = $this->baseUrl . $action;

        $ch = curl_init();

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        if ($method == 'POST') {
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $this->token,
                'Content-type: application/json',
                'Accept: */*'
            ]);

            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        } else {
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $this->token,
                'Accept: */*'
            ]);

            curl_setopt($ch, CURLOPT_POST, false);
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');
            $url .= '?' . $data;
        }
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

            $dump .= PHP_EOL . '[[POST DATA]] ' . $data . PHP_EOL;
            $dump .= PHP_EOL . '[[RESPONSE]] ' . $result . PHP_EOL;
            echo $dump;
        } else {
            $result = curl_exec($ch);
        }
        curl_close($ch);

        return json_decode($result, true);
    }
}
