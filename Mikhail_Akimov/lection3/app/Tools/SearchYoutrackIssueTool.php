<?php
namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;

use App\YoutrackApi;
use App\Logger;

class SearchYoutrackIssueTool extends Tool
{

    public function __construct()
    {
        parent::__construct(
            'search_youtrack_issue',
            'Поиск похожих багов в YouTrack по названию или описанию или ключевым словам.'
        );

        $this->addProperty(new ToolProperty(
            name: 'query',
            type: 'string',
            description: 'слова или фразы для поиска бага в Youtrack',
            required: true
        ));

        $this->setCallable(function (string $query) {
            Logger::I()->log($query, 'SearchYoutrackIssueTool');
            $issues = YoutrackApi::I()->searchIssues($query);
            $results = '';
            if (is_array($issues)) {
                $results = [];
                foreach ($issues as $issue) {
                    if (
                        isset($issue['$type'])
                        && $issue['$type'] == 'Issue'
                        && isset($issue['summary'])
                        && isset($issue['description'])
                        && isset($issue['created'])
                        && isset($issue['id'])
                    ) {
                        $results[] = [
                            'issueid' => $issue['id'],
                            'summary' => $issue['summary'],
                            'description' => $issue['description'],
                            'created' => date('Y-m-d H:i:s', $issue['created'])
                        ];
                    }
                }
                if (sizeof($results) > 0) {
                    $results = json_encode($results);
                } else {
                    $results = '';
                }
            }
            return $results;
        });
    }
}