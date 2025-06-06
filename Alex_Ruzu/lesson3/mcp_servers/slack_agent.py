from dotenv import load_dotenv

load_dotenv()

import os
import asyncio

from agents.mcp.server import MCPServerStdio
from agents import Agent, Runner

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")
SLACK_CHANNEL_IDS = os.getenv("SLACK_CHANNEL_IDS")

if not all([SLACK_BOT_TOKEN, SLACK_TEAM_ID, SLACK_CHANNEL_IDS]):
    raise RuntimeError(
        "Please set SLACK_BOT_TOKEN, SLACK_TEAM_ID, SLACK_CHANNEL_IDS before running this script."
    )

DOCKER_IMAGE = "mcp/slack"

async def send_slack_message(text, channel=None):
    """
    Send a message to Slack using the MCP-based Slack agent.
    Returns the result object from the MCP agent.
    """
    if channel is None:
        # Use the first channel from SLACK_CHANNEL_IDS as default
        channel = SLACK_CHANNEL_IDS.split(',')[0].strip()
    
    server = None
    try:
        server = MCPServerStdio(
            params={
                "command": "docker",
                "args": [
                    "run", "-i", "--rm",
                    "-e", "SLACK_BOT_TOKEN",
                    "-e", "SLACK_TEAM_ID",
                    "-e", "SLACK_CHANNEL_IDS",
                    DOCKER_IMAGE,
                ],
                "env": {
                    "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
                    "SLACK_TEAM_ID": SLACK_TEAM_ID,
                    "SLACK_CHANNEL_IDS": SLACK_CHANNEL_IDS,
                },
            },
            name="slack"
        )
        await server.connect()

        agent = Agent(
            name="Slack helper",
            instructions=(
                "You are a Slack assistant. Use the available tools to answer the user's question. "
                "If no tool is relevant, reply normally."
            ),
            mcp_servers=[server]
        )

        question = (f"Send a message to channel {channel} with the text: '{text}'")
        result = await Runner.run(agent, question)
        return result
    finally:
        if server:
            await server.cleanup()


async def demo_agent_with_mcp():
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "SLACK_BOT_TOKEN",
                "-e", "SLACK_TEAM_ID",
                "-e", "SLACK_CHANNEL_IDS",
                DOCKER_IMAGE,
            ],
            "env": {
                "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
                "SLACK_TEAM_ID": SLACK_TEAM_ID,
                "SLACK_CHANNEL_IDS": SLACK_CHANNEL_IDS,
            },
        },
        name="slack"
    )

    await server.connect()

    agent = Agent(
        name="Slack helper",
        instructions=(
            "You are a Slack assistant. Use the available tools to answer the user's question. "
            "If no tool is relevant, reply normally."
        ),
        mcp_servers=[server],
    )

    question = (
        f"Send a message to channel {SLACK_CHANNEL_IDS.split(',')[0].strip()} with the text 'Hello from the Slack MCP agent!'"
    )
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    await server.cleanup()


if __name__ == "__main__":
    asyncio.run(demo_agent_with_mcp()) 