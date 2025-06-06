<?php

namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use App\YoutrackApi;
use App\Logger;

class AddCommentToYoutrackIssueTool extends Tool
{
    public function __construct()
    {
        parent::__construct(
            'add_comment_to_youtrack_issue',
            'Добавить комментарий к багу в YouTrack.'
        );

        $this->addProperty(new ToolProperty(
            name: 'issueId',
            type: 'string',
            description: 'ID бага',
            required: true
        ));
        $this->addProperty(new ToolProperty(
            name: 'comment',
            type: 'string',
            description: 'Текст комментария',
            required: true
        ));

        $this->setCallable(function (string $summary, string $description) {
            Logger::I()->log($issueId.' - '.$comment, 'AddCommentToYoutrackIssueTool');

            $result = YoutrackApi::I()->addComment($issueId, $comment);
            return $result;
    
        });
    }

}