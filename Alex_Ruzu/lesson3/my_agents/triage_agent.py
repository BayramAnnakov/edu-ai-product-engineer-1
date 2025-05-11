from agents import Agent, Runner, handoff
import pandas as pd
import asyncio

from my_agents.bug_report_agent import bug_report_agent
from my_agents.feature_request_agent import feature_request_agent
from dotenv import load_dotenv
import os


load_dotenv()

RECOMMENDED_PROMPT_PREFIX = """# System context\nYou are part of a multi-agent system called the Agents SDK, 
    designed to make agent coordination and execution easy. Agents uses two primary abstraction: 
    **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off 
    a conversation to another agent when appropriate. Handoffs are achieved by calling 
    a handoff function, generally named `transfer_to_<agent_name>`. 
    Transfers between agents are handled seamlessly in the background; do not mention 
    or draw attention to these transfers in your conversation with the user.\n"""

triage_agent = Agent(
    name="Triage Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a triage agent. Your job is to read the user feedback and decide if it describes a bug, a feature request, or something else.
    - If the feedback describes a problem, error, or malfunction, you must ALWAYS hand off to the bug_report_agent.
    - If the feedback describes a request for new functionality or an improvement, you must ALWAYS hand off to the feature_request_agent.
    - Otherwise, return ONLY the JSON: {{"classification": "other"}}.
    Never return the classification directly for bug or feature requests; always perform the handoff.
    """,
    handoffs=[bug_report_agent, feature_request_agent]
)
