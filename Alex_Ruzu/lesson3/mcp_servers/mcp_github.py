import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents import function_tool
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os
import warnings

load_dotenv()
warnings.filterwarnings("ignore", category=ResourceWarning)

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME") 
FULL_REPO = f"{GITHUB_USERNAME}/{REPO_NAME}"

print("DEBUG: GITHUB_TOKEN =", os.getenv("GITHUB_TOKEN"))
print("DEBUG: GITHUB_PERSONAL_ACCESS_TOKEN =", os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"))

@function_tool
async def create_github_issue(title: str, description: str):
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
            print("DEBUG: Creating issue in repo:", FULL_REPO)
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            result = await Runner.run(
                starting_agent=agent,
                input=f"Create a new issue in '{FULL_REPO}' titled '{title}' with description '{description}'."
            )
            return result.final_output

async def main():
    async with MCPServerStdio(
        name="GitHub MCP",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"]
        }
    ) as server:
        print("DEBUG: GITHUB_TOKEN =", os.getenv("GITHUB_TOKEN"))
        print("DEBUG: GITHUB_PERSONAL_ACCESS_TOKEN =", os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"))
        print("FULL_REPO:", FULL_REPO)    
        agent = Agent(
            name="GitHubAgent",
            instructions="You can answer questions and perform actions related to GitHub repositories, issues, and pull requests. Use the available tools to interact with GitHub.",
            mcp_servers=[server]
        )
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP GitHub Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            
            # List repositories
            result = await Runner.run(starting_agent=agent, input=f"List repositories for user '{GITHUB_USERNAME}'.")
            print("List of repositories:")
            print(result.final_output)
            
            print("\nDEBUG: FULL_REPO =", FULL_REPO)
            
            # List open issues
            result = await Runner.run(starting_agent=agent, input=f"Show open issues in the repo '{FULL_REPO}'.")
            print("\nOpen issues in the repo:\n")
            print(result.final_output)

            # Create a new issue
            result = await Runner.run(starting_agent=agent, input=f"Create a new issue in '{FULL_REPO}' titled 'Bug: login fails' with description: 'Cannot log in with correct credentials'.")
            print("\nNew issue created:\n")
            print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
