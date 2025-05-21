# triage_agent.py
# This file implements the triage agent for the Agents SDK.
from agents import Agent, handoffs
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ai_agents.bug_report_flow import bug_report_agent
from ai_agents.feature_request_flow import feature_request_agent


# Triage agent (LLM-as-a-judge)
triage_agent = Agent(
    name="Triage Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}\n\n
    You are a triage agent. Your job is to read the user feedback and decide if it describes a bug, a feature request, or something else.
    - If the feedback describes a problem, error, or malfunction, you must ALWAYS hand off to the bug_report_agent.
    - If the feedback describes a request for new functionality or an improvement, you must ALWAYS hand off to the feature_request_agent.
    - Otherwise, return ONLY the JSON: {{"classification":"other"}}.
    - Always perform the handoff for bug or feature requests.
    """,
    handoffs=[bug_report_agent, feature_request_agent]
)
