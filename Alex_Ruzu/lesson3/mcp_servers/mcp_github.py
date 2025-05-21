import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os
import re
import json


load_dotenv()


DOCKER_IMAGE    = "ghcr.io/github/github-mcp-server"
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME       = os.getenv("REPO_NAME") 
FULL_REPO       = f"{GITHUB_USERNAME}/{REPO_NAME}"

REQUIRED = [GITHUB_TOKEN, GITHUB_USERNAME, REPO_NAME]
if not all(REQUIRED):
    raise RuntimeError("Please export GITHUB_TOKEN, GITHUB_USERNAME, REPO_NAME before running this script.")


async def get_existing_issues():
    """Get all existing GitHub issues.
    Returns:
        list: List of issue descriptions
    """

    try:    
        server = MCPServerStdio(
            name="GitHub MCP",        
            params={
                "command": "docker",
                "args": [
                    "run", "-i", "--rm",
                    "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                    DOCKER_IMAGE,
                ],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
            },
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
        
        result = await Runner.run(
            agent,
            input=f"List all open issues in '{FULL_REPO}' repo for user '{GITHUB_USERNAME}'. "
            "Return ONLY a JSON array with fields: number, title, body. Do not include any extra text."
        )
        
        if not result or not result.final_output:
            print("[DEBUG] No result or empty result from Runner.run")
            return []

        # Parse the result into a list of issues
        # The LLM is prompted to return ONLY a JSON array of issues, but in practice,
        # it may sometimes include extra text (such as explanations, markdown, or formatting)
        # before or after the JSON. To robustly handle this, we use a regular expression
        # to extract the first JSON array found in the output, and then parse it.
        #
        # This approach ensures that even if the LLM adds extra text, we can still
        # reliably obtain the structured list of issues for further processing.
        #
        # If no JSON array is found, or if the JSON is invalid, an empty list is returned.
        def extract_json_array(text):
            match = re.search(r'(\[\s*{.*}\s*\])', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise ValueError("No JSON array found in output")

        issues = extract_json_array(result.final_output)        
        return issues
    except Exception as e:
        print(f"Error in get_existing_issues: {str(e)}")
        return []
    finally:
        await server.cleanup()


async def create_github_issue(title: str, description: str):
    server = MCPServerStdio(
        name="GitHub MCP",        
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                DOCKER_IMAGE,
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        },
        cache_tools_list=True,
    )
    await server.connect()

    try:
        agent = Agent(
            name="GitHub helper",
            instructions=(
                "You are a GitHub assistant. Use the available tools to answer the user's question. "
                "If no tool is relevant, reply normally."
            ),
            mcp_servers=[server],
        )

        result = await Runner.run(
            starting_agent=agent,
            input=f"Create a new issue in '{FULL_REPO}' titled '{title}' with description '{description}'."
        )
        return result.final_output
    finally:
        await server.cleanup()


async def main():
    server = MCPServerStdio(
        name="GitHub MCP",        
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                DOCKER_IMAGE,
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        },
        cache_tools_list=True,
    )
    await server.connect()

    try:
        agent = Agent(
            name="GitHub helper",
            instructions=(
                "You are a GitHub assistant. Use the available tools to answer the user's question. "
                "If no tool is relevant, reply normally."
            ),
            mcp_servers=[server],   # ←📦 The magic line; see docs examples :contentReference[oaicite:0]{index=0}
        )
        '''
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP GitHub Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
        '''    
        # List repositories
        result = await Runner.run(starting_agent=agent, input=f"List repositories for user '{GITHUB_USERNAME}'.")
        print("List of repositories:")
        print(result.final_output)
        
        print("\nDEBUG: FULL_REPO =", FULL_REPO)
        
        # List open issues
        result = await Runner.run(starting_agent=agent, input=f"Show open issues in the repo '{FULL_REPO}'.")
        print("\nOpen issues in the repo:\n")
        issues = await get_existing_issues()
        for issue in issues:
            print(issue['number'], issue['title'])
            # You can now easily extract the 'Original review:' from issue['body']

        # Create a new issue
        result = await Runner.run(
            starting_agent=agent, 
            input=(
                f"Create a new issue in '{FULL_REPO}' titled 'Bug: login fails' "
                f"with description: 'Cannot log in with correct credentials'."
            )
        )
        print("\nNew issue created:\n")
        print(result.final_output)

    finally:
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
