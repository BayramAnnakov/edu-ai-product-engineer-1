import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")  # Set your GitHub username in .env or replace here
REPO_NAME = "edu-ai-product-engineer-1"  # Replace with your actual repo name
FULL_REPO = f"{GITHUB_USERNAME}/{REPO_NAME}"

async def main():
    async with MCPServerStdio(
        name="GitHub MCP",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"]
        }
    ) as server:
    
        agent = Agent(
            name="GitHubAgent",
            instructions="You can answer questions and perform actions related to GitHub repositories, issues, and pull requests. Use the available tools to interact with GitHub.",
            mcp_servers=[server]
        )

        trace_id = gen_trace_id()
        with trace(workflow_name="MCP GitHub Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            result = await Runner.run(starting_agent=agent, input=f"List repositories for user '{GITHUB_USERNAME}'.")
            print(result.final_output)

            result = await Runner.run(starting_agent=agent, input=f"Show open issues in the repo '{FULL_REPO}'.")
            print(result.final_output)

            result = await Runner.run(starting_agent=agent, input=f"Create a new issue in '{FULL_REPO}' titled 'Bug: login fails' with description 'Cannot log in with correct credentials'.")
            print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
