# bug_report_flow.py
# This file implements the bug report flow, including all agents and logic for bug report classification, deduplication.

from agents import Agent, Runner, function_tool
import asyncio

from mcp_servers.mcp_github import create_github_issue, get_existing_issues


BUG_POLICY = """
Bug Report Policy:
- Summary: Use the first sentence of the review, or a concise paraphrase of the main problem, as the summary. The summary should be clear, specific, and under 100 characters if possible.
- The bug report description must always include the following labeled sections, even if you must infer or state 'Not specified':
    Description: [full review text or summary of the problem]
    Expected behavior: [what should have happened]
    Actual behavior: [what did happen]    
    Steps to reproduce: [steps, or 'Not specified']
    Original review: [verbatim review text from CSV]

- Do not invent or add information not present in the review, except for reasonable inferences about expected/actual behavior.
- Do not skip any review classified as a bug report.
- Do not duplicate bug reports for the same review.
- Do not include personal information from the reviewer.

- Example:
    **Description:** The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable.\n
    **Expected behavior:** The pump should function reliably and the o-ring should stay in place.
    **Actual behavior:** The o-ring slides out of place, jamming the pump.\n
    **Steps to reproduce:** Use the pump as directed for several weeks.\n
    **Original review:** The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable. The first one lasted about 9 months but the second lasted less than a month. Until they fix this issue, the product is hit or miss.

If the review does not specify these, infer them or state 'Not specified.'
For each bug report, call the available tool with:
- The summary (first sentence or paraphrase)
- The description (full review text, formatted as specified)
- The original review text from the CSV (verbatim, unmodified, for duplicate detection).
"""

# Add the duplicate checking agent and function
bug_duplicate_agent = Agent(
    name="Bug Duplicate Checker Agent",
    instructions="Given two bug descriptions, answer only 'yes' if they describe the same issue, otherwise 'no'.",
    model="gpt-4o-mini"
)

# First, wrap the check_duplicate function as a function_tool
async def check_duplicate(new_original_review: str) -> bool:
    """Check if the new bug's original review is a duplicate of any existing issue.
    Args:
        new_original_review: The original review text from the new bug report
    Returns:
        bool: True if original review is a duplicate, False otherwise
    """
   
    # Get all existing issues
    existing_issues = await get_existing_issues()
    print(f"[DEBUG] Found {len(existing_issues)} existing issues")
    
    if not existing_issues:
        return False
    
    # Check against each existing issue's review
    for i, existing_issue in enumerate(existing_issues, 1):
        print(f"\n[DEBUG] Checking issue {i} of {len(existing_issues)}:")
        
        # Extract the existing issue description
        existing_issue_desc = existing_issue['body']
        if existing_issue_desc:
            prompt = f"Review 1:\n{new_original_review}\n\nreview 2:\n{existing_issue_desc}\n\nAre these two reviews describing the same issue? Answer only 'yes' or 'no'."

            # Run the duplicate check agent
            result = await Runner.run(bug_duplicate_agent, prompt)
            answer = result.final_output.strip().lower()
            print(f"[DEBUG] Agent response: {answer}")            
            if answer.startswith("yes"):
                return True
    
    print("[DEBUG] No duplicates found - returning False")
    return False


@function_tool
async def create_issue(summary: str, description: str, original_review: str) -> str:
    """Create a GitHub issue if the review is not a duplicate.
    Args:
        summary: The issue summary/title
        description: The full issue description
        original_review: The original review text for duplicate checking
    Returns:
        str: The result of the operation
    """

    # First check for duplicates
    is_duplicate = await check_duplicate(original_review)
    
    if is_duplicate:
        return "Duplicate issue detected - no new issue created"
    
    # If not a duplicate, create the issue
    await create_github_issue(summary, description)

    return "Issue created successfully"

# Then use the wrapped function in the bug_report_agent
bug_report_agent = Agent(
    name="Bug Report Agent",
    instructions=("""
        You must always follow the Bug Report Policy below when generating bug reports.
        Bug Report Policy:\n{BUG_POLICY}\n
        For each bug report, call create_issue with:
        - The summary (first sentence or paraphrase).
        - The description (full review text, formatted as specified).
        - The original review text from the CSV (verbatim, unmodified).
        You must return ONLY the JSON: {{"classification":"bug"}}.
        """
    ),
    tools=[create_issue],   # create GitHub issue
    model="gpt-4o-mini"
)


if __name__ == "__main__":
    import asyncio
    async def main():
        load_dotenv()

        sample_bug_report = """I've been using viber since 2010 and there are still major bugs that haven't been fixed. 
        Sometimes when I write a sentence it would send but keep the last word of it and send it right after my message. 
        Another thing is my aliases. I would go and put a 30 or more character alias and it would say 
        alias error even tho the limit of characters is 50."""
        
        # Normalize the review text
        sample_bug_report = sample_bug_report.strip()
        print(f"Testing bug_report_agent with input: {sample_bug_report}")

        result = await Runner.run(
            bug_report_agent,
            f"""Generate a GitHub issue for the following review. Follow the Bug Report Policy below:
{BUG_POLICY}

Review:
{sample_bug_report}
"""
        )
        print("Agent final output:", result.final_output)
        
    asyncio.run(main())