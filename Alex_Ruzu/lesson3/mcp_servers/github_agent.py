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
from .filtered_mcp_server import FilteredServer
import json

# Agents-SDK ≥ 0.0.21
from agents.mcp.server import MCPServerStdio        # core MCP client
from agents import Agent, Runner                    # only needed for the bonus part

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")            # PAT with repo / read:org scopes
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")      # GitHub username
REPO_NAME = os.getenv("REPO_NAME")                  # GitHub repository name

if not all([GITHUB_TOKEN, GITHUB_USERNAME, REPO_NAME]):
    raise RuntimeError(
        "Please set GITHUB_TOKEN, GITHUB_USERNAME, REPO_NAME before running this script."
    )

GITHUB_REPO =  GITHUB_USERNAME + "/" + REPO_NAME
DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"


async def create_issue(title, body):
    """
    Create a new issue in the repository.
    """
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
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
        mcp_servers=[server],
    )
            
    question = (f"Create a new issue in {GITHUB_REPO} with the title: '{title}' and the body: '{body}'")
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    await server.cleanup()

    return result


async def get_issues():
    """
    Get all open issues in the repository.
    """
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
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
        mcp_servers=[server],
    )

    question = f"List all open issues in {GITHUB_REPO}. Return ONLY a JSON array of objects with 'title' and 'body' fields, no other text."
    result = await Runner.run(agent, question)
    await server.cleanup()

    # Extract JSON from the response
    response_text = result.final_output
    # Find the first '[' and last ']' to extract just the JSON array
    start = response_text.find('[')
    end = response_text.rfind(']') + 1
    if start >= 0 and end > start:
        json_str = response_text[start:end]
        try:
            issues = json.loads(json_str)
            return issues
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {json_str}")
            return []
    return []


async def demo_agent_with_mcp():
    """
    Same server, but let an LLM decide which tool(s) to call.
    Needs OPENAI_API_KEY in env. Omit if you only want raw MCP usage.
    """
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                DOCKER_IMAGE,
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        },
        name="github",
        cache_tools_list=True,
    )

    # Use this MCP server wrapper to filter the tools that are available to the agent
    # server = FilteredServer(
    #     params={
    #         "command": "docker",
    #         "args": [
    #             "run",
    #             "-i",
    #             "--rm",
    #             "-e",
    #             "GITHUB_PERSONAL_ACCESS_TOKEN",
    #             DOCKER_IMAGE,
    #         ],
    #         "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
    #     },
    #     name="github",
    #     cache_tools_list=True,
    #     allowed=["list_issues"]
    # )

    await server.connect()

    agent = Agent(
        name="GitHub helper",
        instructions=(
            "You are a GitHub assistant. Use the available tools to answer the user's question. "
            "If no tool is relevant, reply normally."
        ),
        mcp_servers=[server],   
    )

    question = (
        f"List the three most recently updated open issues in {GITHUB_REPO} "
        "and summarise each in one sentence."
    )
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)

    question = (f"Create a new issue in {GITHUB_REPO} with the title 'Issue from openai agent SDK' and the body 'This is a new issue created from the openai agent SDK'")
    result = await Runner.run(agent, question)
    print("\n🗣  Agent's answer:\n", result.final_output)


    issues = await get_issues()
    print("issues: ", issues)


    await server.cleanup()


if __name__ == "__main__":
    asyncio.run(demo_agent_with_mcp())  # uncomment for the agent version
