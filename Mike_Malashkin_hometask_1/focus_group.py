import asyncio
import json
from datetime import datetime
from agents import Agent, Runner
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Создаем агента-фасилитатора
facilitator_agent = Agent(
    name="Facilitator",
    instructions="""You are an experienced focus group facilitator. Your role is to:
    1. Guide the discussion about mascara products and user experience
    2. Ask probing questions about product features and preferences
    3. Ensure all participants share their views
    4. Keep the discussion focused on:
       - Product quality and effectiveness
       - Application experience
       - Price-quality ratio
       - Brand comparison
    Be empathetic and encourage detailed feedback.""",
)

def create_persona_agent(persona_data, site_name):
    """Создает агента на основе данных персоны"""
    return Agent(
        name=f"Persona_{site_name}",
        handoff_description=f"Customer persona from {site_name}",
        instructions=f"""You are a real customer with the following profile:
        {persona_data['persona']}
        
        Share your experience and opinions about mascara products based on your profile.
        Focus on:
        - Your experience with different mascaras
        - What you value most in mascara products
        - Your pain points and concerns
        - Price sensitivity and brand preferences
        
        Always stay in character and respond based on your persona's characteristics.""",
    )

# Создаем агента для финального саммари
summary_agent = Agent(
    name="Research Analyst",
    instructions="""You are a Research Analyst who will create a detailed summary of the focus group discussion.
    Your summary should include:
    1. Key findings about mascara preferences
    2. Common pain points across different customer segments
    3. Product improvement suggestions
    4. Price sensitivity insights
    5. Brand perception
    6. Recommendations for manufacturers""",
)

class FocusGroup:
    def __init__(self):
        self.discussion_log = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.persona_agents = []
        
    async def log_message(self, role, message):
        self.discussion_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "message": message
        })
        
    async def run_discussion(self):
        # Загружаем персоны
        try:
            with open("personas_20250424_211711.json", 'r', encoding='utf-8') as f:
                personas_data = json.load(f)
        except FileNotFoundError:
            print("Error: Personas file not found")
            return
            
        # Создаем агентов из персон
        for persona in personas_data['personas']:
            self.persona_agents.append(create_persona_agent(persona, persona['site']))
            
        # Начало дискуссии
        await self.log_message("Facilitator", "Welcome to our focus group discussion about mascara products. Today we'll be discussing your experiences, preferences, and concerns about different mascara products.")
        
        # Первый раунд: общие впечатления
        result = await Runner.run(facilitator_agent, 
            "Let's start by discussing your overall experience with mascara products. What are the most important features for you when choosing a mascara?")
        await self.log_message("Facilitator", result.final_output)
        
        # Получаем ответы от каждой персоны
        for agent in self.persona_agents:
            result = await Runner.run(agent, "Share your experience and what you value most in mascara products. What makes you choose or avoid certain mascaras?")
            await self.log_message(agent.name, result.final_output)
        
        # Второй раунд: конкретные характеристики
        result = await Runner.run(facilitator_agent, 
            "Let's discuss specific mascara features. What about application experience, lasting power, and removal process?")
        await self.log_message("Facilitator", result.final_output)
        
        for agent in self.persona_agents:
            result = await Runner.run(agent, "Tell us about your experience with mascara application, how long it lasts, and how easy it is to remove.")
            await self.log_message(agent.name, result.final_output)
        
        # Третий раунд: цена и бренды
        result = await Runner.run(facilitator_agent, 
            "Now let's talk about price points and brands. How do you make decisions about which mascara to buy?")
        await self.log_message("Facilitator", result.final_output)
        
        for agent in self.persona_agents:
            result = await Runner.run(agent, "Share your thoughts on mascara prices and brands. What price range do you prefer and why?")
            await self.log_message(agent.name, result.final_output)
        
        # Финальное саммари
        all_discussion = "\n".join([f"{log['role']}: {log['message']}" for log in self.discussion_log])
        summary = await Runner.run(summary_agent, f"Please create a comprehensive summary of this focus group discussion about mascara products:\n\n{all_discussion}")
        await self.log_message("Research Analyst", summary.final_output)
        
        # Сохраняем лог дискуссии
        self.save_discussion()
        
    def save_discussion(self):
        output_file = f"mascara_focus_group_discussion_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Focus Group Discussion - Mascara Products\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("=" * 80 + "\n\n")
            
            for entry in self.discussion_log:
                f.write(f"[{entry['timestamp']}] {entry['role']}:\n")
                f.write(f"{entry['message']}\n\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"\nDiscussion saved to: {output_file}")

async def main():
    focus_group = FocusGroup()
    await focus_group.run_discussion()

if __name__ == "__main__":
    asyncio.run(main()) 