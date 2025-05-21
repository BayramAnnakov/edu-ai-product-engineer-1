# main.py
# This file implements the main function for the Agents SDK.
from agents import Runner
import pandas as pd
import asyncio
import json

from ai_agents.triage_agent import triage_agent
from dotenv import load_dotenv
import os


def load_reviews(csv_path, review_column="content", num_rows=None):
    df = pd.read_csv(csv_path)
    if num_rows:
        df = df.head(num_rows)
    return df[review_column].dropna().astype(str).tolist()


async def classify_review(review):
    result = await Runner.run(triage_agent, review)
    output = (result.final_output or "").strip()
    print(f"Classification output: {output}")
    try:
        classification = json.loads(output)["classification"]
    except Exception:
        classification = "N/A"
    return classification


async def main():
    load_dotenv()

    data_dir = "data"
    csv_path = os.path.join(data_dir, "viber.csv")
    review_column = "content"
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        return
    
    reviews = load_reviews(csv_path, review_column=review_column, num_rows=3)
    print(f"Loaded {len(reviews)} reviews")

    for idx, review in enumerate(reviews, 1):
        print(f"\n--- Processing Review #{idx} ---\n{review}\n")
        classification = await classify_review(review)
        print(f"Classification: {classification}\n")


if __name__ == "__main__":
    asyncio.run(main())
