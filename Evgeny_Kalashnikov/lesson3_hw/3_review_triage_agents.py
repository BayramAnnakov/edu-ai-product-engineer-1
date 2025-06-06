import os
import asyncio
from typing import List, Optional, Literal

from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, trace, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp.server import MCPServerStdio

load_dotenv()

# ───────────────────────────────────────── Constants ──────────────────────────────────────────
REVIEW_FILE = "2_netflix.md"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")  # Fallback to generic format if not set
DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"
BUG_REPORT_GUIDELINES = """When creating bug reports, follow these guidelines:
- Description: Always include the following labeled sections:
  - Description: Full review text or summary of the problem
  - Expected behavior: What should have happened
  - Actual behavior: What did happen
  - Steps to reproduce: Steps, or 'Not specified' 
- If the review is unclear, start with a short context sentence
- Do not invent or add information not present in the review
- Do not include personal information from the reviewer
- For sections without explicit information, infer from context or state 'Not specified'

Include original complete review text without modifications at the end of the description
"""

# ───────────────────────────────────────── Data contracts ──────────────────────────────────────
class Review(BaseModel):
    review_text: str

class ReviewsArray(BaseModel):
    reviews: List[Review]

class ClassificationOut(BaseModel):
    review_text: str
    classification: Literal["bug report", "feature request", "other"]

class DupCheckOut(ClassificationOut):
    is_duplicate: bool
    original_issue_id: Optional[int] = None

class BugPostResult(DupCheckOut):
    status: str  # "commented" | "created" | "error"
    url: Optional[str] = None

# ───────────────────────────────────────── Function tools ──────────────────────────────────────
@function_tool
def read_file_content(filename: str) -> str:
    """Read the content of a file and return it as a string."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"File read: {filename}")
        return content
    except Exception as e:
        error_msg = f"Error reading file '{filename}': {str(e)}"
        print(error_msg)
        return error_msg

# ───────────────────────────────────────── Agent factory --------------------------------------

def build_review_processor(mcp_github: MCPServerStdio):
    """Build a fully agentic review processing system with a single entry point."""

    # --- Bug poster specialized agent -------------------------------------------------------------
    bug_poster = Agent(
        name="bug‑poster",
        model="o4-mini",
        mcp_servers=[mcp_github],
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an expert at posting bug reports to GitHub following specific guidelines.
    
    When you receive a request to post a bug report:
    1. Format and post the bug according to these guidelines:
    {BUG_REPORT_GUIDELINES}

    2. Work only with this repository {GITHUB_REPO}
    
    3. Based on your analysis:
       - If the report is a duplicate, add it as a comment to the existing issue. Include original complete review text without modifications to the comment.
       - If it's a new bug, create a fresh issue with proper formatting
       
    4. Provide a summary of what you did and the result
    
    Use your judgment to determine the best way to format the report based on 
    the available information.
    """
    )
    
    # --- Duplicate checker specialized agent ----------------------------------------------------
    duplicate_checker = Agent(
        name="duplicate‑checker",
        model="o4-mini",
        mcp_servers=[mcp_github],
        tools=[
            bug_poster.as_tool(
                tool_name="transfer_to_bug_poster",
                tool_description="Post a bug report to GitHub, either creating a new issue or commenting on an existing one if it's a duplicate"
            )
        ],  # Has access to the bug poster as a tool
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an expert at identifying duplicate issues by checking GitHub.
    
    When reviewing a bug report:
    1. Analyze the core issue described in the report
    2. Search for similar existing issues on GitHub using the search_issues tool
       - Use ONLY 'is:issue state:open repo:{GITHUB_REPO}' as your search query to get all open issues
       - Do not add any additional search terms
    3. Use your judgment to determine if this is a duplicate issue
    
    If you determine this is a duplicate issue:
    - You MAY use the post_bug tool to add the report as a comment to the existing issue
    
    If you determine this is a new issue:
    - You MAY use the post_bug tool to create a new GitHub issue with the report
    
    You have flexibility to determine whether this should be posted to GitHub based on
    the quality and clarity of the bug report.
    
    Handle errors gracefully - if a GitHub operation fails, report the error clearly
    and continue with your analysis.
    """
    )
    
    # --- Main review processor agent -----------------------------------------------------
    review_processor = Agent(
        name="review‑processor",
        model="o4-mini",
        tools=[
            read_file_content,
            duplicate_checker.as_tool(
                tool_name="transfer_to_duplicate_checker",
                tool_description="Check if a bug report is a duplicate of an existing GitHub issue and optionally post it"
            )   
        ],
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an expert at processing customer feedback and bug reports.
    
    You have the following capabilities:
    1. You can read files using the read_file_content tool
    2. You can check for duplicate bugs and post issues using the check_duplicate tool
    
    When processing a task:
    - If asked to process a file of reviews, read the file first
    - Identify any reviews that appear to be bug reports
    - Use your judgment to decide if a review qualifies as a bug report
    - For bug reports, you MAY use the check_duplicate tool to verify if it's a duplicate
      and potentially post to GitHub
    
    You are given autonomy to decide:
    - Which reviews are worth processing as bug reports
    - Whether to check if a bug is a duplicate
    - How to summarize the results of your analysis
    
    Focus on identifying and properly handling technical issues mentioned in reviews.
    """
    )

    return review_processor

# ───────────────────────────────────────── Main workflow ──────────────────────────────────────
async def main():
    # Initialize GitHub MCP server
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN must be set in .env file")
    
    print(f"Using GitHub repository: {GITHUB_REPO}")
    
    server = MCPServerStdio(
        params={
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                DOCKER_IMAGE,
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
        },
        name="github",
        cache_tools_list=True,
    )
    
    async with server as mcp_github:
        # 1. Build the single entry-point agent once MCP is live
        review_processor = build_review_processor(mcp_github)

        # 2. Run the whole pipeline under a *single* trace with full agentic control
        with trace("review_processing_pipeline"):
            # Single entry point with open-ended task description
            result = await Runner.run(
                review_processor, 
                f"""Process customer reviews from the file {REVIEW_FILE}.
                
                Your task:
                1. Read the reviews from the file
                2. Identify which ones are bug reports
                3. For each bug report, check if it's a duplicate of an existing issue
                4. Post non-duplicate bugs as new issues, or add duplicate bugs as comments
                
                You have full autonomy to decide how to process these reviews based on 
                their content and your analysis.
                """
            )

        # 3. Print the final summary from the agent
        print("\nReview Processing Summary:")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
