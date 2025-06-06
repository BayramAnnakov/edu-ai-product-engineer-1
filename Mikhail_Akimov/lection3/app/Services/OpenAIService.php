<?php

// namespace App\Services;


// use OpenAI\Client as OpenAIClient;
// use OpenAI\Transporters\HttpTransporter;
// use GuzzleHttp\Client as GuzzleClient;
// use OpenAI\ValueObjects\ApiKey;
// use OpenAI\ValueObjects\Transporter\BaseUri;
// use OpenAI\ValueObjects\Transporter\Headers;
// use OpenAI\ValueObjects\Transporter\QueryParams;
// use OpenAI\ValueObjects\Transporter\Payload;
// use OpenAI\Enums\Transporter\Method;

// class OpenAIService
// {
//     static protected ?OpenAIService $_I = null;

//     public OpenAIClient $client;
//     static public ?string $apiKey = null;

//     public function __construct()
//     {
//         $httpClient = new GuzzleClient();
//         $baseUri = BaseUri::from('https://api.openai.com/v1');
//         $headers = Headers::withAuthorization(ApiKey::from(OpenAIService::$apiKey));
//         $queryParams = QueryParams::create();
        
//         $transporter = new HttpTransporter(
//             $httpClient,
//             $baseUri,
//             $headers,
//             $queryParams,
//             function ($request) {
//                 return $request;
//             }
//         );
        
//         $this->client = new OpenAIClient($transporter);
//     }

//     public static function I()
//     {
//         if (static::$_I === null) {
//             static::$_I = new OpenAIService();
//         }

//         return static::$_I;
//     }
// } 