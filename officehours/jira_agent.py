from dotenv import load_dotenv

load_dotenv()

import os, asyncio
from agents.mcp.server import MCPServerStdio
from agents import Agent, Runner

JIRA_URL      = os.getenv("JIRA_URL")
JIRA_USER     = os.getenv("JIRA_USERNAME")
JIRA_TOKEN= os.getenv("JIRA_API_TOKEN")

REQUIRED = [JIRA_URL, JIRA_USER, JIRA_TOKEN]
if not all(REQUIRED):
    raise RuntimeError("Export JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN first.")

DOCKER_IMAGE = "ghcr.io/sooperset/mcp-atlassian:latest"

async def demo_agent():
    server = MCPServerStdio(
        name="jira",
        cache_tools_list=True,
        params={
            "command": "docker",
            "args": [
                "run","-i","--rm",
                "-e","JIRA_URL","-e","JIRA_USERNAME","-e","JIRA_API_TOKEN",
                DOCKER_IMAGE
            ],
            "env": {
                "JIRA_URL": JIRA_URL,
                "JIRA_USERNAME": JIRA_USER,
                "JIRA_API_TOKEN": JIRA_TOKEN,
            },
        },
    )
    await server.connect()

    agent = Agent(
        name="Jira helper",
        instructions="Use Jira tools to answer.",
        mcp_servers=[server],
    )

    q = ("List the two latest issues in project NQ"
         "and summarise each in one line.")
    result = await Runner.run(agent, q)
    print(result.final_output)

    q = ("Create a new issue in project NQ with the title 'Issue from openai agent SDK' and the body 'This is a new issue created from the openai agent SDK'")
    result = await Runner.run(agent, q)
    print(result.final_output)

    await server.cleanup()

if __name__ == "__main__":
    asyncio.run(demo_agent())  # uncomment to test the LLM-driven version
