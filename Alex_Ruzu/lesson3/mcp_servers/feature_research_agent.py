import os
import asyncio
import csv
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from agents import function_tool
from .slack_agent import send_slack_message
from .time_agent import get_current_time

load_dotenv()

LLM_MODEL = "gpt-4o-mini"
client = OpenAI()

input_path = os.path.join(os.path.dirname(__file__), "..", "data", "viber_classified.csv")
output_path = os.path.join(os.path.dirname(__file__), "..", "data", "feature_research.md")

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)


def get_major_competitors(request):
    prompt = (
        "List the major competitors for Viber relevant to the following feature request. "
        "Return a numbered list of company/product names only.\n"
        f"Feature Request: {request}\n\nCompetitors:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def select_top_competitors(competitors, request):
    prompt = (
        "Given the following list of competitors and a feature request, select the 3 most relevant competitors for analysis. "
        "Return only their names as a comma-separated list.\n"
        f"Feature Request: {request}\n"
        f"Competitors: {competitors}\n\nTop 3 Competitors:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0
    )
    return response.choices[0].message.content.strip()

# --- LLM-as-a-Planner Pattern ---
# The LLM generates a step-by-step research plan before executing research and report generation.
def generate_research_plan(request):
    prompt = (
        "You are a product research planner. Given the following feature request, outline a step-by-step research plan to investigate competitor products and user needs.\n"
        f"Feature Request: {request}\n\nResearch Plan:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def generate_feature_research(request, plan, top_competitors):
    prompt = (
        "You are a product research expert. Using the following research plan and focusing on these top competitors, "
        "analyze the feature request and provide a structured research report.\n"
        f"Feature Request: {request}\n"
        f"Research Plan: {plan}\n"
        f"Top Competitors: {top_competitors}\n\n"
        "Include the following sections:\n"
        "1. Market Analysis (with competitor comparison)\n"
        "2. User Impact\n"
        "3. Technical Feasibility\n"
        "4. Implementation Recommendations\n"
        "Be specific and cite competitor features where possible.\n\nResearch Report:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0
    )
    return response.choices[0].message.content.strip()

async def save_research_to_markdown(request, research):
    filepath = output_path
    
    timestamp_result = await get_current_time()
    timestamp = getattr(timestamp_result, "final_output", str(timestamp_result))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Feature Research Report\n\n")
        f.write(f"## Research Timestamp: {timestamp}\n\n")
        f.write(f"## Original Request\n\n{request}\n\n")
        f.write(f"## Research Analysis\n\n{research}\n")
    return filepath

async def _send_slack_message_impl(message: str) -> str:
    try:
        # 1. Generate research plan
        plan = generate_research_plan(message)

        # 2. Get major competitors
        competitors = get_major_competitors(message)

        # 3. Select top 3 competitors
        top_competitors = select_top_competitors(competitors, message)
       
        # 4. Generate research report using plan and competitors
        research = generate_feature_research(message, plan, top_competitors)

        # 5. Save to markdown
        await save_research_to_markdown(message, research)

        # 6. Send to Slack via MCP-based agent
        # --- Human-in-the-loop Pattern ---
        # For feature requests, the feature agent sends the research report to Slack for human review/decision.
        status = await send_slack_message(research)
        print("Status: Message sent to Slack")

        return "success"
    except Exception as e:
        print(f"Status: Failed to send message to Slack - {str(e)}")
        return "failed"

@function_tool
async def send_feature_research_to_slack(message: str) -> str:
    return await _send_slack_message_impl(message)

async def main():
    with open(input_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        feature_requests = [row for _, row in zip(range(3), reader)]
        print(f"Processing {len(feature_requests)} feature requests...")
        for index, row in enumerate(feature_requests, 1):
            if row.get("classification") != "feature request":
                continue
            request = row["content"]
            status = await _send_slack_message_impl(request)
            print(f"Feature request sent to Slack. Status: {status}")
    print(f"Feature research complete. Research reports saved in: {output_path}")

if __name__ == "__main__":
    asyncio.run(main()) 