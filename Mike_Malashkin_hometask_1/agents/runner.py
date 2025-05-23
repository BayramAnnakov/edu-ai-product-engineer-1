from typing import Dict, Union, List, Any
import re
from .agent import Agent

class Runner:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the runner."""
        self.agents[agent.name] = agent

    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the runner."""
        if agent_name in self.agents:
            del self.agents[agent_name]

    def get_agent(self, agent_name: str) -> Agent:
        """Get an agent by name."""
        return self.agents.get(agent_name)

    def clear_all_histories(self) -> None:
        """Clear conversation histories for all agents."""
        for agent in self.agents.values():
            agent.clear_history()

    def run_conversation(self, agent_name: str, prompt: Union[str, List[Dict[str, Any]]]) -> str:
        """Run a conversation with a specific agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        # Получаем ответ от агента
        response = agent.get_response(prompt)
        
        # Проверяем, есть ли запрос на хэндоф
        handoff_pattern = r"\[ПЕРЕДАЮ СЛОВО: ([^\]]+)\]"
        handoff_match = re.search(handoff_pattern, response)
        
        # Если обнаружен запрос на хэндоф и у агента настроены хэндофы
        if handoff_match and agent.handoffs:
            # Извлекаем имя агента для хэндофа
            target_agent_name = handoff_match.group(1).strip()
            print(f"Обнаружен запрос на хэндоф к агенту: {target_agent_name}")
            
            # Проверяем, существует ли указанный агент в списке хэндофов
            target_agent = None
            for handoff_agent in agent.handoffs:
                if handoff_agent.name == target_agent_name:
                    target_agent = handoff_agent
                    break
            
            # Если агент найден, продолжаем разговор с ним
            if target_agent and target_agent.name in self.agents:
                # Удаляем маркер хэндофа из ответа
                clean_response = re.sub(handoff_pattern, "", response).strip()
                
                # Формируем контекст для передачи целевому агенту
                handoff_context = f"Агент {agent.name} передал тебе слово. Его последнее сообщение: {clean_response}"
                
                print(f"Выполняется хэндоф от {agent.name} к {target_agent.name}")
                
                # Запускаем разговор с целевым агентом
                return self.run_conversation(target_agent.name, handoff_context)
        
        # Если хэндоф не запрошен или не выполнен, возвращаем ответ
        return response 