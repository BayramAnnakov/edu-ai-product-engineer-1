<?php

namespace App\Traits;

use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;

trait ProviderTrait
{

    public function provider(): \NeuronAI\Providers\AIProviderInterface
    {
        return new NeuronOpenAI(
            key: $_ENV['OPENAI_API_KEY'],
            model: 'gpt-4.1-mini'
        );
    }
}
