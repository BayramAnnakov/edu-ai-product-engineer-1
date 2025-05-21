import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    async with MCPServerStdio(
        name="Time MCP",
        params={
            "command": "docker",
            "args": ["run", "-i", "--rm", "mcp/time", "--local-timezone=Europe/Tallinn"]
        }
    ) as server:
    
        agent = Agent(
            name="TimeAgent",
            instructions="You can answer questions about the current time, time in different timezones, and time conversions. Use the available tools to answer user questions.",
            mcp_servers=[server]
        )

        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Time Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            result = await Runner.run(starting_agent=agent, input="What time is it?")
            print(result.final_output)

            result = await Runner.run(starting_agent=agent, input="What time is it in Tokyo?")
            print(result.final_output)

            result = await Runner.run(starting_agent=agent, input="When it's 4 PM in New York, what time is it in London?")
            print(result.final_output)

            result = await Runner.run(starting_agent=agent, input="Convert 9:30 AM Tokyo time to New York time")
            print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
