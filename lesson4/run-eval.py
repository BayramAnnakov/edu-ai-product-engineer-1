import openai, json, os
from schemas import ReviewRow
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
EVAL_ID = "eval_6820b68a05288190a585ee032ec43ce0"

# ---- 5-a  ·  Load or build your dataset -----------------------------------
rows: list[ReviewRow] = [
    ReviewRow(
        review="App crashes on login screen.",
        label="bug",
        known_issues=["Crash on login when password is empty"],
        is_duplicate=True,
    ),
    ReviewRow(
        review="Please add an undo option for deletions!",
        label="feature",
        known_issues=[],
        is_duplicate=False,
    ),
    # …more rows…
]

# ---- 5-b  ·  Collect agent outputs ----------------------------------------
def call_agent(row: ReviewRow) -> str:
    """
    Simulates agent responses to test different graders.
    Returns different responses based on the input row to test various cases.
    """
    # Test bug vs feature grader
    if row.label == "bug":
        if row.is_duplicate:
            return "duplicate bug: This is a known issue that occurs when the password field is empty. We're working on a fix."
        else:
            return "bug: The app crashes on the login screen. This needs immediate attention."
    elif row.label == "feature":
        if "undo" in row.review.lower():
            # Good feature proposal that should pass the feature quality grader
            return """Feature Proposal: Undo Deletion Functionality

User Request: Add an undo option for deletions

Competitive Analysis:
- Google Drive offers a 30-day undo history
- Dropbox provides an undo feature in their web interface
- Notion has a comprehensive undo system with keyboard shortcuts

Implementation Plan:
1. Add an undo stack to track recent deletions
2. Implement a keyboard shortcut (Cmd/Ctrl + Z) for undo
3. Add an undo button in the UI toolbar
4. Store deletion metadata for 30 days

Benefits:
- Reduces user anxiety about accidental deletions
- Improves user experience by providing a safety net
- Aligns with industry standard practices
- Minimal performance impact as we'll only store recent deletions"""
        else:
            # Poor feature proposal that should fail the feature quality grader
            return "We should add this feature. It would be nice to have."
    
    return "I'm not sure how to categorize this request."

# Create JSONL file with the evaluation data
jsonl_data = []
for row in rows:
    assistant_response = call_agent(row)
    jsonl_data.append({
        "item": row.model_dump(exclude_none=True),
        "sample": {
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": assistant_response,
                    },
                }
            ],
        },
    })

# Write to JSONL file
jsonl_file = "eval_data.jsonl"
with open(jsonl_file, "w") as f:
    for item in jsonl_data:
        f.write(json.dumps(item) + "\n")

# # Upload the file
file = client.files.create(
    file=open(jsonl_file, "rb"),
    purpose="evals"
)
print("File uploaded:", file.id)

# Read file content as string (newline-separated JSONL) for API
with open(jsonl_file, "r") as f:
    jsonl_content = f.read()

# Create the run
run_result = client.evals.runs.create(
    eval_id=EVAL_ID,
    name="first-full-run",
    data_source={
        "type": "jsonl",
        "source": {
            "type": "file_id",
            "id": file.id
        }
    }
)

print("Run submitted:", run_result.id)
print("View interactive report:", run_result.report_url)
