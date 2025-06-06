import os
import asyncio
import csv
from dotenv import load_dotenv
from openai import OpenAI
from .github_agent import get_issues, create_issue
from agents import function_tool

load_dotenv()

LLM_MODEL = "gpt-4o-mini"
client = OpenAI()

input_path = os.path.join(os.path.dirname(__file__), "..", "data", "viber_classified.csv")

BUG_REPORT_POLICY = (
    "When generating bug reports, follow these guidelines:\n"
    "- Description: Always include the following labeled sections (infer or state 'Not specified' if missing):\n"
    "  - Description: Full review text or summary of the problem.\n"
    "  - Expected behavior: What should have happened.\n"
    "  - Actual behavior: What did happen.\n"
    "  - Steps to reproduce: Steps, or 'Not specified'.\n"
    "  - Original review: Verbatim review text from CSV.\n"
    "- If the review is unclear, start the description with a short context sentence.\n"
    "- Do not invent or add information not present in the review, except for reasonable inferences about expected/actual behavior.\n"
    "- Do not skip any review classified as a bug report.\n"
    "- Do not duplicate bug reports for the same review.\n"
    "- Do not include personal information from the reviewer.\n"
    "If the review does not specify these, infer them or state 'Not specified.'\n"
)

def format_bug_report(title, review):
    prompt = (
        f"Format this bug report according to the policy:\n"
        f"Review: {review}\n\n"
        f"Bug Report Policy:\n{BUG_REPORT_POLICY}"
    )
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0
    )
    return response.choices[0].message.content.strip()


def is_duplicate_llm(new_desc, existing_desc):
    prompt = (
        "You are a strict QA expert. Compare the following two bug report descriptions. "
        "If they describe the same underlying issue, reply ONLY with the word 'duplicate'. "
        "If not, reply ONLY with the word 'unique'.\n"
        f"New Report Description: {new_desc}\n"
        f"Existing Issue Description: {existing_desc}\n"
        "Judgment:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0
    )
    llm_output = response.choices[0].message.content.strip().lower()
    return llm_output.startswith('duplicate')


async def _create_github_issue_impl(title: str, body: str) -> str:
    async def _run():
        formatted_body = format_bug_report(title, body)
        issues = await get_issues()
        for issue in issues:
            if is_duplicate_llm(formatted_body, issue['body']):
                print("Status: Duplicate issue found")
                return "duplicate"
        new_url = await create_issue(title, formatted_body)
        print(f"Status: New issue created at {new_url}")
        return new_url
    return await _run()


@function_tool
async def create_github_issue(title: str, body: str) -> str:
    return await _create_github_issue_impl(title, body)


def main():
    with open(input_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        bug_reports = [row for _, row in zip(range(3), reader)]
        print(f"Processing {len(bug_reports)} bug reports...")

        # CSV writing is commented out for agentic/in-memory workflow.
        # Uncomment the following lines if you want to save results to a CSV file.
        # fieldnames = reader.fieldnames + ["status"]
        # writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        # writer.writeheader()
        for row in bug_reports:
            if row.get("classification") != "bug report":
                continue
            review = row["content"]
            title = review[:100]

            # Call the main bug report creation logic
            url = _create_github_issue_impl(title, review)
            row["status"] = url

            # Print the result to the terminal
            print(f"Bug report: {title} | Status: {url}")

            # writer.writerow(row)  # Uncomment to write to CSV
    print(f"Bug handling complete.")


if __name__ == "__main__":
    main() 