import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_IDS")

REQUIRED = [SLACK_BOT_TOKEN, SLACK_TEAM_ID, SLACK_CHANNEL]
if not all(REQUIRED):
    raise RuntimeError("Export SLACK_BOT_TOKEN, SLACK_TEAM_ID, SLACK_CHANNEL first.")

DOCKER_IMAGE = "mcp/slack"


async def send_slack_message(message: str):
    """
    Send a message to the Slack channel.
    """

    server = MCPServerStdio(
        name="Slack MCP",        
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "SLACK_BOT_TOKEN",
                "-e", "SLACK_TEAM_ID",
                "-e", "SLACK_CHANNEL_IDS",
                DOCKER_IMAGE,
            ],
            "env": {
                "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
                "SLACK_TEAM_ID": SLACK_TEAM_ID,
                "SLACK_CHANNEL_IDS": SLACK_CHANNEL,
            },
        },
        cache_tools_list=True,
    )       
    await server.connect()

    try:    
        agent = Agent(
            name="SlackAgent",
            instructions=(
                "You are a Slack assistant. Use the available tools to answer the user's question. "
                "If no tool is relevant, reply normally."
            ),
            mcp_servers=[server],
        )

        result = await Runner.run(
            starting_agent=agent,
            input=f"Send the following message to the Slack channel '{SLACK_CHANNEL}': {message}"
        )

        return result.final_output
    except Exception as e:
        return f"Error: {e}"
    finally:
        await server.cleanup()


async def main():
    server = MCPServerStdio(
        name="Slack MCP",        
        params={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "SLACK_BOT_TOKEN",
                "-e", "SLACK_TEAM_ID",
                "-e", "SLACK_CHANNEL_IDS",
                DOCKER_IMAGE,
            ],
            "env": {
                "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
                "SLACK_TEAM_ID": SLACK_TEAM_ID,
                "SLACK_CHANNEL_IDS": SLACK_CHANNEL,
            },
        },
        cache_tools_list=True,
    )       
    await server.connect()

    try:    
        agent = Agent(
            name="SlackAgent",
            instructions=(
                "You are a Slack assistant. Use the available tools to answer the user's question. "
                "If no tool is relevant, reply normally."
            ),
            mcp_servers=[server],
        )
        
        # Example: Send a message to the Slack channel
        result = await Runner.run(
            starting_agent=agent,
            input=f"Send the following message to the Slack channel '{SLACK_CHANNEL}': Hello from MCP Slack integration!"
        )
        print("Message sent to the Slack channel result:")
        print(result.final_output)

        result = await Runner.run(
            starting_agent=agent,
            input=f"Get a list of users in the Slack channel '{SLACK_CHANNEL}'"
        )
        print("List of users in the Slack channel:")
        print(result.final_output)

        await send_slack_message("Hello from MCP Slack integration!!!!")

        return result.final_output
    except Exception as e:
        return f"Error: {e}"
    finally:
        await server.cleanup()  


if __name__ == "__main__":
    asyncio.run(main())
