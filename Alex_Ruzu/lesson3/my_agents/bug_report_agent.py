from agents import Agent, Runner, function_tool
import pandas as pd
import asyncio

from dotenv import load_dotenv
import os


load_dotenv()

JIRA_BUG_POLICY = """
Jira Bug Report Policy:
- Summary: Use the first sentence of the review, or a concise paraphrase of the main problem, as the summary. The summary should be clear, specific, and under 100 characters if possible.
- The bug report description must always include the following labeled sections, even if you must infer or state 'Not specified':
    Description: [full review text or summary of the problem]
    Expected behavior: [what should have happened]
    Actual behavior: [what did happen]    
    Steps to reproduce: [steps, or 'Not specified']
    Original review: [verbatim review text from CSV]
- Formatting:
    - Start the description with a short context sentence if the review is unclear.
    - If the review mentions error messages, include them in a separate section.
    - If the review mentions environment details (e.g., product version, device), include them at the end.
- Do not invent or add information not present in the review, except for reasonable inferences about expected/actual behavior.
- Do not skip any review classified as a bug report.
- Do not duplicate bug reports for the same review.
- Do not include personal information from the reviewer.
- Example:
    *Description:* The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable.
    *Expected behavior:* The pump should function reliably and the o-ring should stay in place.
    *Actual behavior:* The o-ring slides out of place, jamming the pump.    
    *Steps to reproduce:* Use the pump as directed for several weeks.
    *Original review:* The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable. The first one lasted about 9 months but the second lasted less than a month. Until they fix this issue, the product is hit or miss.

If the review does not specify these, infer them or state 'Not specified.'
For each bug report, call the create_jira_bug tool with:
- The summary (first sentence or paraphrase)
- The description (full review text, formatted as specified)
- The original review text from the CSV (verbatim, unmodified, for duplicate detection)
"""

@function_tool
def print_hello_bug_report():
    print("Creating Jira Bug Report...")
    return '{"classification": "bug"}'


bug_report_agent = Agent (
    name = "Bug Report Agent",
    #instructions = "You are a bug report agent. You are responsible for reporting the bug to the development team.",
    instructions = (
        "You are a bug report agent. "
        "You are responsible for calling the print_hello_bug_report tool when handling a bug report. "
        "You must always call the print_hello_bug_report tool when handling a bug report, "
        "and you must return ONLY the tool's result as your final output. "
        "Do not add any extra text."
    ),
    tools=[print_hello_bug_report],
)

if __name__ == "__main__":
    import asyncio
    async def main():
        sample_bug_report = "The app crashes when I try to send a message."
        print(f"Testing bug_report_agent with input: {sample_bug_report}")
        result = await Runner.run(bug_report_agent, sample_bug_report)
        print("Agent final output:", result.final_output)
    asyncio.run(main())

