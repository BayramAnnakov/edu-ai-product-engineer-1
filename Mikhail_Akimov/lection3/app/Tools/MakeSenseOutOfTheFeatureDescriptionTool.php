<?php

namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;


use App\Logger;
use App\Agents\FeedbackToFeatureAgent;

class MakeSenseOutOfTheFeatureDescriptionTool extends Tool
{
    public static $agent = null;

    public function __construct()
    {
        parent::__construct(
            'make_sense_out_of_the_feature_description',
            'Из отзыва пользователя (feedback) выдели часть, которая описывает фичу сформулируй ее развернуто'
        );

        $this->addProperty(new ToolProperty(
            name: 'feedback',
            type: 'string',
            description: 'Обратная связь пользователя из которой нужно выделить описание фичи',
            required: true
        ));

        $this->setCallable(function (string $feedback) {
            if (! static::$agent) {
                static::$agent = new FeedbackToFeatureAgent();
            }
            $result = static::$agent->makeSense($feedback);
            return json_encode($result);
        });
    }
}
