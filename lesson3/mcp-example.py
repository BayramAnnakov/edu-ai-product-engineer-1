from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServer, MCPServerStdio


async def run(server: MCPServer):

    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and answer questions based on those files.",
        mcp_servers=[server],
    )
    message = "Read the files and list them."
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask about books
    message = "What is my #1 favorite book?"
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask a question that reads then reasons.
    message = "Look at my favorite songs. Suggest one new song that I might like."
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

async def main():

    current_dir = os.path.dirname(os.path.abspath(__file__))

    async with MCPServerStdio(
        name = "Filesystem Server, via npx",
        params = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", current_dir],
        },
    ) as server:
        await run(server)

if __name__ == "__main__":
    asyncio.run(main())