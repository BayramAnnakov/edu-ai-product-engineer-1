from google.adk.agents import Agent

# Import read_csv and generate_plot tools from the new utility module
from .tools.data_tools import read_csv, generate_plot

LIVE_MODEL = "gemini-2.0-flash-live-001"

VOICE_AGENT_PROMPT = """
# Voice Agent
Your role is to assist users with their questions and help them with their problems.

# Task:
Assist users with their questions and help them with their problems. 
Preview the data first and tell me what is inside.
"""

root_agent = Agent(
    name="voice_agent",
    model=LIVE_MODEL,
    description="This is data analysis voice agent.",
    instruction=VOICE_AGENT_PROMPT,
    tools=[read_csv, generate_plot]
)