# bug_report_flow.py
# This file implements the bug report flow, including all agents and logic for bug report classification, deduplication, and Jira integration.

import sys
import os
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool
import pandas as pd
import asyncio
from jira import JIRA
import hashlib
import openai
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#from mcp_servers.mcp_github import create_github_issue
#from mcp_servers.mcp_jira import create_jira_bug


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
    *Description:* The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable.\n
    *Expected behavior:* The pump should function reliably and the o-ring should stay in place.
    *Actual behavior:* The o-ring slides out of place, jamming the pump.    
    *Steps to reproduce:* Use the pump as directed for several weeks.
    *Original review:* The rubber o-ring inside the pump slides out of place, jamming the pump and rendering it unusable. The first one lasted about 9 months but the second lasted less than a month. Until they fix this issue, the product is hit or miss.

If the review does not specify these, infer them or state 'Not specified.'
For each bug report, call the create_jira_bug tool with:
- The summary (first sentence or paraphrase)
- The description (full review text, formatted as specified)
- The original review text from the CSV (verbatim, unmodified, for duplicate detection).
"""

def get_all_jira_bugs(jira_client, jira_project_key):
    start_at = 0
    max_results = 50
    all_issues = []
    while True:
        issues = jira_client.search_issues(
            f'project = {jira_project_key} AND issuetype = Bug',
            startAt=start_at,
            maxResults=max_results
        )
        if not issues:
            break
        all_issues.extend(issues)
        if len(issues) < max_results:
            break
        start_at += max_results
    return all_issues


def is_duplicate_jira_bug_hash(jira_client, jira_project_key, review_hash):
    """
    Check for existing Jira issues with the same review hash in the description.
    Returns the first duplicate issue if found, else None.
    """
    jql = f'project = {jira_project_key} AND issuetype = Bug AND description ~ "{review_hash}"'
    issues = jira_client.search_issues(jql)
    if issues:
        return issues[0]
    return 


async def is_duplicate_jira_bug(jira_client, jira_project_key, new_description):
    """
    Check all bugs in the project for semantic duplicates using bug_duplicate_agent.
    Returns the key of a duplicate issue if found, else None.
    """
    all_issues = get_all_jira_bugs(jira_client, jira_project_key)
    for issue in all_issues:
        existing_desc = getattr(issue.fields, 'description', None)
        if existing_desc:
            is_dup = await check_duplicate(new_description, existing_desc)
            if is_dup:
                return issue.key
    return None


@function_tool
async def create_jira_bug(summary: str, description: str, original_review_text: str) -> str:
    """
    Create a bug issue in Jira, avoiding duplicates by using bug_duplicate_agent for semantic duplicate detection.
    Args:
        summary: The title/summary of the bug.
        description: The detailed description of the bug.
        original_review_text: The original review text from the CSV.
    Returns:
        The key of the created Jira issue or a message if duplicate found.
    """
    print("Summary:", summary)
    print("Description:", description)
    try:
        jira_server = os.getenv('JIRA_SERVER')
        jira_email = os.getenv('JIRA_EMAIL')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        jira_project_key = os.getenv('JIRA_PROJECT_KEY')

        jira = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))

        # Generate a hash of the original review text for traceability
        review_hash = hashlib.sha256(original_review_text.encode('utf-8')).hexdigest()
        hash_line = f"*Review-Hash:* {review_hash}"
        description_with_hash = f"{description}\n\n{hash_line}"

        # Use the duplicate check function based on the review hash
        duplicate_issue = is_duplicate_jira_bug_hash(jira, jira_project_key, review_hash)
        if duplicate_issue:
            msg = f"Duplicate not created: A bug with the same review hash already exists (e.g., {duplicate_issue.key})."
            print("Duplicate Jira issue key:", duplicate_issue.key)
            return json.dumps({"classification": "bug", "result": msg, "duplicate": True, "key": duplicate_issue.key})

        # Use the bug_duplicate_agent-based duplicate check (LLM-as-a-judge pattern)
        duplicate_key = await is_duplicate_jira_bug(jira, jira_project_key, description)
        if duplicate_key:
            msg = f"Duplicate not created: A bug with a similar description already exists (e.g., {duplicate_key})."
            print("Duplicate Jira issue key:", duplicate_key)
            return json.dumps({"classification": "bug", "result": msg, "duplicate": True, "key": duplicate_key})
        
        issue_dict = {
            'project': {'key': jira_project_key},
            'summary': summary,
            'description': description_with_hash,
            'issuetype': {'name': 'Bug'},
        }
        new_issue = jira.create_issue(fields=issue_dict)
        print("Created Jira issue key:", new_issue.key)
        result_string = f"Created Jira issue: {new_issue.key}"
        return json.dumps({"classification": "bug", "result": result_string, "key": new_issue.key})
    except Exception as e:
        return json.dumps({"classification": "bug", "result": f"Error creating Jira issue: {str(e)}", "error": True})




@function_tool
def print_hello_bug_report():
    print("Creating Jira Bug Report...")
    return '{"classification": "bug"}'


bug_report_agent = Agent(
    name="Bug Report Agent",
    instructions = (
        "You are a bug report agent. "
        "You must always follow the Jira Bug Report Policy below when generating bug reports. "
        f"Jira Bug Report Policy:\n{JIRA_BUG_POLICY}\n"
        "You are responsible for calling the create_jira_bug tool when handling a bug report. "
        "You must return ONLY the tool's result as your final output. Do not add any extra text."
    ),
    #tools=[print_hello_bug_report], # For testing
    #tools=[create_github_issue],    # GitHub MCP    
    tools=[create_jira_bug],         # Jira API
    #tools=[create_jira_bug...],        # Jira MCP    
    model="gpt-4o-mini"
)


# --- Deduplication logic (LLM-as-a-judge) ---
from agents import Agent, Runner

bug_duplicate_agent = Agent(
    name="Bug Duplicate Checker Agent",
    instructions="Given two bug descriptions, answer only 'yes' if they describe the same issue, otherwise 'no'.",
    model="gpt-4o-mini"
)

async def check_duplicate(desc1, desc2):
    prompt = f"Bug report 1:\n{desc1}\n\nBug report 2:\n{desc2}\n\nAre these two bug reports describing the same issue? Answer only 'yes' or 'no'."
    result = await Runner.run(bug_duplicate_agent, prompt)
    answer = result.final_output.strip().lower()
    return answer.startswith("yes")


if __name__ == "__main__":
    import asyncio
    async def main():
        load_dotenv()

        sample_bug_report = """I've been using viber since 2010 and there are still major bugs that haven't been fixed. 
        Sometimes when I write a sentence it would send but keep the last word of it and send it right after my message. 
        Another thing is my aliases. I would go and put a 30 or more character alias and it would say 
        alias error even tho the limit of characters is 50. """
        print(f"Testing bug_report_agent with input: {sample_bug_report}")

        result = await Runner.run(
            bug_report_agent,
            f"""Generate a Jira bug report for the following review. 
Follow the Jira Bug Report Policy below:

{JIRA_BUG_POLICY}

Review:
{sample_bug_report}
"""
        )
        print("Agent final output:", result.final_output)
        
    asyncio.run(main())
