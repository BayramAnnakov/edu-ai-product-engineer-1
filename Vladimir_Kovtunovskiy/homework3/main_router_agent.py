import asyncio
import os
from pydantic import BaseModel
from dotenv import load_dotenv 
from agents.mcp import MCPServer, MCPServerStdio
from agents import Agent, ModelSettings, function_tool, handoff, Runner, HandoffInputData, trace
from openai.types.responses import ResponseTextDeltaEvent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from feature_handler_agent import feature_handler_manager_agent
from bug_handler_agent import bug_handler_agent

load_dotenv()

class RouterOutput(BaseModel):
    reason: str
    """Your reasoning for why this task is important"""

    task_description: str
    """Detailed description of the task"""

    task_classification: str
    """Bug or feature request task"""

@function_tool
def read_report() -> str:
    report_path = "Vladimir_Kovtunovskiy/homework3/board_session_report.md"

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
            return report_content
    
    except FileNotFoundError:
        error_msg = f"Error: Report file not found at {report_path}"
        return error_msg
    except Exception as e:
        error_msg = f"An error occurred during reading the report: {str(e)}"
        return error_msg

async def run(mcp_server1: MCPServer, mcp_server2: MCPServer, directory_path: str):
    bug_handler_agent.mcp_servers = [mcp_server1]
    feature_handler_manager_agent.mcp_servers = [mcp_server2]

    router_agent = Agent(
        name="Router Agent",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
                    You are the router agent. Your goal is to read a report about product research 
                    and decide which task is the most important to do next. This task should be 
                    classified either as a bug or as a feature request.
                    After classification handoff corresponding feature to a specialized agent
                    for handling bugs or feature requests.
                    For Feature request - ask Agent to do a research on how to implement the feature into the product.
                    For Bugs - ask Agent to create an issue on GitHub.""",
        model="gpt-4.1",
        tools=[read_report, bug_handler_agent.as_tool(tool_name="handle_bugs", 
                                                  tool_description="Creates an issue on GitHub"), 
           feature_handler_manager_agent.as_tool(tool_name="handle_feature_request", 
           tool_description="Creates a research plan and executes it")])

    message = "Analyze the latest report. Either handle a bug or feature request. When everything is finished say good bye to the user."
    print("\n" + "-" * 40)
    print(f"Running: {message}")
    result = Runner.run_streamed(router_agent, input=message)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

async def main():
    github_command = "npx -y @modelcontextprotocol/server-github"
    slack_command = "npx -y @modelcontextprotocol/server-slack"

    # Initialize two MCP servers
    async with MCPServerStdio(
        cache_tools_list=True,
        params={"command": "npx", 
                "args": github_command.split(" ")[1:], 
                "env": {
                    "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]
                }
                },
    ) as server1, MCPServerStdio(
        name="Slack MCP Server",
        params={
            "command": "npx",
            "args": slack_command.split(" ")[1:],
            "env": {
                "SLACK_BOT_TOKEN":  os.environ["SLACK_BOT_TOKEN"],
                "SLACK_TEAM_ID": os.environ["SLACK_TEAM_ID"]
            },
        },
    ) as server2:
        with trace(workflow_name="MCP GitHub Example"):
            await run(server1, server2, "${GITHUB_REPO}")

if __name__ == "__main__":
    asyncio.run(main())
