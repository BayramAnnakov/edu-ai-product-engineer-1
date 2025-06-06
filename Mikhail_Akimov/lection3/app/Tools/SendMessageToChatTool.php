<?php
namespace App\Tools;

use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use NeuronAI\Providers\OpenAI\OpenAI as NeuronOpenAI;


use App\Logger;
/**
 * Вебхук регистрируем вот здесь: https://developers.google.com/chat/how-tos/webhooks#step_1_register_the_incoming_webhook
 * Копируем webhook URL с chat.google.com
 */
class SendMessageToChatTool extends Tool
{

    public function __construct()
    {
        parent::__construct(
            'send_message_to_chat',
            'Отправка сообщения в чат'
        );

        $this->addProperty(new ToolProperty(
            name: 'message',
            type: 'string',
            description: 'сообщение, которое нужно доставить в чат',
            required: true
        ));

        $this->setCallable(function (string $message) {
            Logger::I()->log($message, 'SendMessageToChatTool');
            $result = $this->sendMessage($message);
            return json_encode($result);
        });
    }

    public function sendMessage($message)
    {
        $url = $_ENV['CHAT_WEBHOOK_URL'];

        $ch = curl_init();

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-type: application/json; charset=UTF-8'
        ]);

        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['text' => $message]));
        curl_setopt($ch, CURLOPT_URL, $url);

        $result = curl_exec($ch);

        curl_close($ch);

        return json_decode($result, true);
    }
}
