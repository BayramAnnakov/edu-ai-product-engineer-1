"""
github_mcp_demo.py
Minimal example of using the GitHub MCP Server from Python with the
OpenAI Agents SDK (https://openai.github.io/openai-agents-python/mcp/).

What it shows
-------------
1. Spin up the GitHub MCP Server as a subprocess (STDIO transport)
2. Discover the tools it exposes (MCP list_tools)
3. Call two representative tools directly
4. (Bonus) Wrap the server into an Agent so the LLM can call the same tools
"""

from dotenv import load_dotenv

load_dotenv()

import os
import asyncio

# Agents-SDK ≥ 0.0.21
from agents.mcp.server import MCPServerStdio      # core MCP client
from agents import Agent, Runner                  # only needed for the bonus part

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")          # PAT with repo / read:org scopes

if not GITHUB_TOKEN:
    raise RuntimeError(
        "Please `export GITHUB_TOKEN=...` before running this script."
    )

DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"


async def demo_agent_with_mcp():
    """
    Same server, but let an LLM decide which tool(s) to call.
    Needs OPENAI_API_KEY in env. Omit if you only want raw MCP usage.
    """
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                DOCKER_IMAGE,
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        },
        name="github",
        cache_tools_list=True,
    )

    await server.connect()

    agent = Agent(
        name="GitHub helper",
        instructions=(
            "You are a GitHub assistant. Use the available tools to answer the user's question. "
            "If no tool is relevant, reply normally."
        ),
        mcp_servers=[server],   # ←📦 The magic line; see docs examples :contentReference[oaicite:0]{index=0}
    )

    question = (
        "List the three most recently updated open issues in BayramAnnakov/edu-ai-product-engineer-1 "
        "and summarise each in one sentence."
    )
    result = await Runner.run(agent, question)
    print("\n🗣  Agent’s answer:\n", result.final_output)

    question = ("Create a new issue in BayramAnnakov/edu-ai-product-engineer-1 with the title 'Issue from openai agent SDK' and the body 'This is a new issue created from the openai agent SDK'")
    result = await Runner.run(agent, question)
    print("\n🗣  Agent’s answer:\n", result.final_output)

    await server.cleanup()


if __name__ == "__main__":
    asyncio.run(demo_agent_with_mcp())  # uncomment for the agent version
