from agents import Agent, Runner, function_tool
from pydantic import BaseModel
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer, MCPServerStdio
import asyncio
import shutil
import os
from dotenv import load_dotenv 

load_dotenv()

class BugHandlerOutput(BaseModel):
    bug_id: str
    """Bug id in the ticket system"""

    bug_description: str
    """Detailed description of the bug"""

@function_tool
def create_bug_ticket(bug_description: str) -> BugHandlerOutput:
    """Creates a bug ticket and returns BugHandler Output Object with bug bug_id and bug_description

    Args:
        bug_description: The detailed description of the bug
    """
    print(f"[Bug Handler Tool] Creating bug ticket for: {bug_description}")
    # In a real scenario, this would interact with a ticketing system or GitHub Issues via MCP
    return BugHandlerOutput(bug_id="id_1_simulated", bug_description=bug_description)

async def setup_mcp_server(repo_path: str): # Added repo_path argument
    """Setup and return the MCP server for GitHub integration"""
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise ValueError(f"The provided path '{repo_path}' is not a valid git repository.")
        
    print(f"[Bug Handler] Setting up MCP Server with repo_path: {repo_path}")
    return MCPServerStdio(
        cache_tools_list=True, # If True, tools are fetched once. If False, on every agent run that needs them.
        params={
            "command": "uvx",
            "args": ["mcp-server-git"],
            "github_token": "${GITHUB_TOKEN}",
            "repo": "${GITHUB_REPO}",  # Format: "owner/repository_name"
            "cwd": repo_path  # Crucial for mcp-server-git to know the local repo context
        }
    )

# Create the agent instance that can be imported by other modules
bug_handler_agent = Agent(
    name="Bug Handler Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a specialized agent for handling bug reports.
    Your primary task is to create a github issue using the available tools or mcp.
    The user will provide a description of the bug. First search if github has simillar issue, if not create a new issue as a critical bug.
    Only work with this git repository VVK93/edu-ai-product-engineer-1
    """,
    model="gpt-4.1",
    handoff_description="An agent that specializes in creating and managing bug reports."
    )