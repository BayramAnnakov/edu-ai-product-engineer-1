import os
from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self, name: str, role: str, temperature: float = 0.7, handoff_description: Optional[str] = None):
        self.name = name
        self.role = role
        self.temperature = temperature
        self.handoff_description = handoff_description
        self.handoffs = []
        # Используем старую версию OpenAI
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.conversation_history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
        })

    def get_response(self, prompt: str) -> str:
        """Get a response from the agent using OpenAI API."""
        # Если промпт - список сообщений, добавляем их все
        if isinstance(prompt, list):
            for message in prompt:
                self.add_message(message["role"], message["content"])
        else:
            # Иначе добавляем как обычное сообщение
            self.add_message("user", prompt)
        
        # Добавляем информацию о возможных хэндофах
        system_message = {"role": "system", "content": self.role}
        
        # Если у агента есть хэндофы, добавляем инструкции по их использованию
        if self.handoffs:
            handoff_info = "Ты можешь передать обсуждение другому агенту, если считаешь что он лучше ответит. "
            handoff_info += "Доступные агенты:\n"
            
            for agent in self.handoffs:
                handoff_info += f"- {agent.name}: {agent.handoff_description or 'Нет описания'}\n"
            
            handoff_info += "\nЕсли хочешь передать слово, напиши в своем ответе: "
            handoff_info += "[ПЕРЕДАЮ СЛОВО: имя_агента]"
            
            # Добавляем к системной инструкции
            system_message["content"] += "\n\n" + handoff_info
        
        messages = [system_message] + self.conversation_history
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=self.temperature,
        )
        
        response_text = response.choices[0].message.content
        self.add_message("assistant", response_text)
        
        return response_text

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = [] 