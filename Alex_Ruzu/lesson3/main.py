from agents import Agent, function_tool, Runner

import pandas as pd
import asyncio

from ai_agents.triage_agent import triage_agent
from dotenv import load_dotenv
import os
import json


def load_reviews(csv_path, review_column="content", num_rows=None):
    df = pd.read_csv(csv_path)
    if num_rows:
        df = df.head(num_rows)
    return df[review_column].dropna().astype(str).tolist()


async def classify_review(review):
    # Use the triage agent to classify the review
    result = await Runner.run(triage_agent, review)

    # Try to extract the classification from the agent's output
    output = (result.final_output or "").strip().lower()
    try:
        classification = json.loads(output).get("classification", "other")
    except Exception:
        classification = "other"

    return classification


async def main():
    load_dotenv()

    data_dir = "data"
    csv_path = os.path.join(data_dir, "viber.csv")
    review_column = "content"
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        return
    
    reviews = load_reviews(csv_path, review_column=review_column, num_rows=15)
    print(f"Loaded {len(reviews)} reviews")

    for idx, review in enumerate(reviews, 1):
        #print(f"Review #{idx}: {review}")
        print(f"Review #{idx}:")
        classification = await classify_review(review)
        print(f"Classification: {classification}\n")


if __name__ == "__main__":
    asyncio.run(main())
