<?php
namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;

use App\FirecrawlApi;
use App\Logger;

class SearchContentInInternetTool extends Tool
{

    public function __construct()
    {
        parent::__construct(
            'search_content_in_internet',
            'Поиск информации в интернете'
        );

        $this->addProperty(new ToolProperty(
            name: 'query',
            type: 'string',
            description: 'слова или фразы для поиска в интернете',
            required: true
        ));

        $this->setCallable(function (string $query) {
            Logger::I()->log($query, 'SearchContentInInternetTool');
            
            $founds = FirecrawlApi::I()->search($query);
            $results = '';
            if (is_array($founds)) {
                $results = [];
                foreach ($founds as $found) {
                    Logger::I()->log(
                        $found['title'] . "\n" . 
                        $found['url'] . "\n\n" . 
                        $found['description'] . "\n", 
                        'Tools FirecrawlApi'
                    );

                    $results[] = $found;
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