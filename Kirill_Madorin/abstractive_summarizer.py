# Placeholder for abstractive summarizer logic using OpenAI Agents SDK / LLMs
# This will likely involve defining an Agent or using an AgentClient.

import pandas as pd
import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, Runner

# Load environment variables from .env file
load_dotenv()

# Make sure OPENAI_API_KEY is set in your environment variables or .env file
# Set API key for tracing if available
if os.getenv("OPENAI_API_KEY"):
    from agents import set_tracing_export_api_key
    set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

async def generate_abstractive_summary(text: str) -> str:
    """
    Generates an abstractive summary for the given text using an Agent from OpenAI Agents SDK.
    """
    if pd.isna(text) or not text.strip():
        return "Input text is empty."
    
    # Create an agent with instructions for summarizing
    summary_agent = Agent(
        name="abstractive_summarizer",
        instructions="You are an expert text summarizer who creates concise, informative summaries. Create an abstractive summary that captures the main points while using your own wording. You've been trained to distill text into its essence without losing important information."
    )
    
    # Run the agent with the text as input
    try:
        result = await Runner.run(summary_agent, f"Summarize this text concisely:\n\n{text}")
        summary = result.final_output
        return summary
    except Exception as e:
        print(f"Error generating abstractive summary: {e}")
        return f"Error generating summary: {str(e)}"


async def generate_abstractive_summaries_async(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Asynchronously adds abstractive summaries to the input DataFrame.
    """
    if 'Text' not in input_df.columns:
        raise ValueError("Input DataFrame must contain a 'Text' column.")

    # Ensure Text column is string type
    input_df['Text'] = input_df['Text'].astype(str)
    
    # Process each review asynchronously
    summaries = []
    for text in input_df['Text']:
        summary = await generate_abstractive_summary(text)
        summaries.append(summary)
    
    input_df['AbstractiveSummary'] = summaries
    return input_df


def generate_abstractive_summaries(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Synchronous wrapper for the async function.
    """
    return asyncio.run(generate_abstractive_summaries_async(input_df))


if __name__ == '__main__':
    # Example usage (requires a DataFrame, e.g., from extractive step):
    data = {'Id': [1, 2], 'Text': ["This is the first review text. It's quite good.", "This is the second review text. It could be better."]}
    example_df = pd.DataFrame(data)
    
    async def run_example():
        summaries_df = await generate_abstractive_summaries_async(example_df.copy())  # Pass a copy
        print("\nAbstractive Summaries:")
        print(summaries_df)
    
    asyncio.run(run_example()) 