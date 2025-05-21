import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import asyncio

# Uncomment ONE of the following imports and function calls to run the desired agent.
# Only one should be uncommented at a time.

# --- AGENT: OpenAI Text ---
# from agents.agent_openai_text import main as openai_text_main
# if __name__ == "__main__":
#     asyncio.run(openai_text_main())

# --- AGENT: OpenAI Review ---
from ai_agents.agent_openai_review import main as openai_review_main
if __name__ == "__main__":
    asyncio.run(openai_review_main())

# --- AGENT: CrewAI Review ---
# from agents.agent_crewai_review import main as crewai_review_main
# if __name__ == "__main__":
#     asyncio.run(crewai_review_main())

# --- AGENT: LangGraph Text ---
# from agents.agent_langgraph_text import main as langgraph_text_main
# if __name__ == "__main__":
#     langgraph_text_main()

# --- AGENT: CrewAI Text ---
# from agents.agent_crewai_text import main as crewai_text_main
# if __name__ == "__main__":
#     asyncio.run(crewai_text_main())
