import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents import function_tool
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os
import sys
import subprocess

load_dotenv()

SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

@function_tool
async def send_slack_message(message: str):
    channel = os.getenv("SLACK_CHANNEL", "#general")
    async with MCPServerStdio(
        name="Slack MCP",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"]
        }
    ) as server:
        agent = Agent(
            name="SlackAgent",
            instructions="You can send messages to Slack channels using the available tools.",
            mcp_servers=[server]
        )
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Slack Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            result = await Runner.run(
                starting_agent=agent,
                input=f"Send the following message to the Slack channel '{channel}': {message}"
            )
            return result.final_output

async def main():
    async with MCPServerStdio(
        name="Slack MCP",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"]
        }
    ) as server:
        agent = Agent(
            name="SlackAgent",
            instructions="You can send messages to Slack channels using the available tools.",
            mcp_servers=[server]
        )
        print("DEBUG: SLACK_BOT_TOKEN =", os.getenv("SLACK_BOT_TOKEN"))
        print("SLACK_CHANNEL:", SLACK_CHANNEL)

        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Slack Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            # Example: Send a message to the Slack channel
            result = await Runner.run(
                starting_agent=agent,
                input=f"Send the following message to the Slack channel '{SLACK_CHANNEL}': Hello from MCP Slack integration!"
            )
            print("Message sent result:")
            print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
