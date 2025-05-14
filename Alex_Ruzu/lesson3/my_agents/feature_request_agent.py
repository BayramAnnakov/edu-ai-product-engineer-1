from agents import Agent, Runner, function_tool
import pandas as pd
import asyncio

from dotenv import load_dotenv
import os


load_dotenv()

@function_tool
def print_hello_feature_request():
    print("Creating Jira Feature Request...")
    return '{"classification": "feature"}'


feature_request_agent = Agent(
    name = "Feature Request Agent",
    instructions = (
        "You are a feature request agent. "
        "You are responsible for calling print_hello_feature_request tool when handling a feature request."
        "You must always call the print_hello_feature_request tool when handling a feature request, "
        "and you must return ONLY the tool's result as your final output. "
        "Do not add any extra text."        
    ),
    tools=[print_hello_feature_request],
    model="gpt-4o-mini"
)

if __name__ == "__main__":
    import asyncio
    async def main():
        sample_feature_request = "I would like a new feature that allows me to add a new contact to my address book."
        print(f"Testing feature_request_agent with input: {sample_feature_request}")
        result = await Runner.run(feature_request_agent, sample_feature_request)
        print("Agent final output:", result.final_output)
    asyncio.run(main())
