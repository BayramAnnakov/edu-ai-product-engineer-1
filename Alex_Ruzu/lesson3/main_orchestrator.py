import sys
import os
import csv
import asyncio
from agents import Agent, Runner
from dotenv import load_dotenv
from agents import function_tool
from mcp_servers.bug_handler_agent import create_github_issue
from mcp_servers.feature_research_agent import send_feature_research_to_slack

sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_servers'))

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"
RECOMMENDED_PROMPT_PREFIX = (
    "# System context\n"
    "You are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. "
    "Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. "
    "Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.\n"
)

input_path = os.path.join(os.path.dirname(__file__), "data", "viber.csv")

async def main():
    bug_agent = Agent(
        name="bug_handler",
        instructions="For bug reports, check for duplicates and create a new GitHub issue if needed.",
        tools=[create_github_issue]
    )
    feature_agent = Agent(
        name="feature_research",
        instructions="For feature requests, generate a PRD and send it to Slack.",
        tools=[send_feature_research_to_slack]
    )
    # --- Triage/Routing Pattern ---
    # The triage_agent classifies input and routes to the appropriate specialized agent (bug handler or feature research).
    triage_agent = Agent(
        name="triage",
        instructions=(
            f"{RECOMMENDED_PROMPT_PREFIX}"
            "Classify the input as one of: 'bug report', 'feature request', 'positive feedback', or 'irrelevant'. "
            "If it's a bug report, hand off to the bug handler agent. "
            "If it's a feature request, hand off to the feature research agent. "
            "If it's positive feedback or irrelevant, reply ONLY with the classification label."
        ),
        handoffs=[bug_agent, feature_agent]
    )

    with open(input_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        reviews = [row for _, row in zip(range(3), reader)]  # Only process first 3 rows
        print(f"Processing {len(reviews)} reviews...")
        
        for row in reviews:
            review = row.get("content") or row.get("review") or next(iter(row.values()))
            print(f"\nReview: {review}")
            
            result = await Runner.run(triage_agent, review)
            print(f"Agent Output: {result.final_output}\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main()) 