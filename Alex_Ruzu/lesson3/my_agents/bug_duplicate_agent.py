from agents import Agent, Runner
import asyncio

from dotenv import load_dotenv
import os

bug_duplicate_agent = Agent(
    name="BugDuplicateChecker",
    instructions="Given two bug descriptions, answer only 'yes' if they describe the same issue, otherwise 'no'.",
    model="gpt-4o-mini"
)

async def check_duplicate(desc1, desc2):
    prompt = f"Bug report 1:\n{desc1}\n\nBug report 2:\n{desc2}\n\nAre these two bug reports describing the same issue? Answer only 'yes' or 'no'."
    result = await Runner.run(bug_duplicate_agent, prompt)
    answer = result.final_output.strip().lower()
    return answer.startswith("yes")

if __name__ == "__main__":
    async def main():
        load_dotenv()

        desc1 = "The app crashes when I try to send a message."
        desc2 = "Whenever I send a message, the app closes unexpectedly."
        is_dup = await check_duplicate(desc1, desc2)
        print(f"Are these duplicates? {'Yes' if is_dup else 'No'}")
    asyncio.run(main()) 