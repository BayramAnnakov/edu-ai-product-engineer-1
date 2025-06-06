<?php
namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use App\YoutrackApi;
use App\Logger;

class CreateYoutrackIssueTool extends Tool
{
    public function __construct()
    {
        parent::__construct(
            'create_youtrack_issue',
            'Создать новый баг в YouTrack.'
        );

        // $this->addProperty(new ToolProperty(
        //     name: 'project_id',
        //     type: 'string',
        //     description: 'ID проекта',
        //     required: true
        // ));
        $this->addProperty(new ToolProperty(
            name: 'summary',
            type: 'string',
            description: 'Краткое описание бага',
            required: true
        ));
        $this->addProperty(new ToolProperty(
            name: 'description',
            type: 'string',
            description: 'Подробное описание бага',
            required: true
        ));

        $this->setCallable(function (string $summary, string $description) {
            $projectId = '0-1';
            Logger::I()->log('Project ' . $projectId . ' - ' . $summary, 'CreateYoutrackIssueTool');
            $result = YoutrackApi::I()->createIssue($projectId, $summary, $description);
            return $result;
        });
    }
}