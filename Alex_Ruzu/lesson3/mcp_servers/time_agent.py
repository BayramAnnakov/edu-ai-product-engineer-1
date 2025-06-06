"""
time_mcp_demo.py
Minimal example of using the Time MCP Server from Python with the
OpenAI Agents SDK.

What it shows
-------------
1. Spin up the Time MCP Server as a subprocess (STDIO transport)
2. Call a tool to get the current time
3. (Bonus) Wrap the server into an Agent so the LLM can call the same tools
"""

from dotenv import load_dotenv
import os

load_dotenv()

import asyncio
from agents.mcp.server import MCPServerStdio
from agents import Agent, Runner

DOCKER_IMAGE = "mcp/time"

DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Europe/Helsinki")  # Default is Helsinki

async def get_current_time():
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                DOCKER_IMAGE,
                f"--local-timezone={DEFAULT_TIMEZONE}",
            ],
        },
        name="time",
        cache_tools_list=True,
    )
    await server.connect()

    agent = Agent(
        name="Time helper",
        instructions=(
            "You are a time assistant. Use the available tools to answer the user's question. "
            "If no tool is relevant, reply normally."
        ),
        mcp_servers=[server],
    )

    question = "What is the current time?"
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    await server.cleanup()
    return result

async def demo_agent_with_mcp():
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                DOCKER_IMAGE,
                f"--local-timezone={DEFAULT_TIMEZONE}",
            ],
        },
        name="time",
        cache_tools_list=True,
    )

    await server.connect()

    agent = Agent(
        name="Time helper",
        instructions=(
            "You are a time assistant. Use the available tools to answer the user's question. "
            "If no tool is relevant, reply normally."
        ),
        mcp_servers=[server],
    )

    question = "What is the current time?"
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    question = "What is the current time in New York?"
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    question = "If it is 3pm in New York, what time is it in London?"
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    await server.cleanup()

if __name__ == "__main__":
    asyncio.run(demo_agent_with_mcp()) 