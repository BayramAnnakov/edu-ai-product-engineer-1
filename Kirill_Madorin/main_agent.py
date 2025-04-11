# Main orchestration script using OpenAI Agents SDK (Conceptual)

import pandas as pd
import asyncio
import os
import argparse
from io import StringIO
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from agents import set_tracing_disabled

from extractive_summarizer import generate_extractive_summaries
from abstractive_summarizer import generate_abstractive_summaries, generate_abstractive_summaries_async
from comparison_reporter import generate_comparison_report

# Load environment variables from .env file
load_dotenv()

# Check if the API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables or .env file")
    print("Please set your API key in the .env file or as an environment variable")
    
# Set API key for tracing if available
if os.getenv("OPENAI_API_KEY"):
    from agents import set_tracing_export_api_key
    set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
else:
    # Disable tracing if no API key is available
    set_tracing_disabled(disabled=True)

# Define our tools as functions first
def extractive_summarizer_tool(csv_path: str):
    """Generate extractive summaries from reviews in a CSV file.
    
    Args:
        csv_path: Path to the CSV file containing reviews
        
    Returns:
        JSON string representation of a DataFrame with Id, Text, and ExtractiveSummary columns
    """
    df = generate_extractive_summaries(csv_path)
    return df.to_json()

async def abstractive_summarizer_tool(df_json: str):
    """Generate abstractive summaries for reviews in the provided DataFrame.
    
    Args:
        df_json: JSON string representation of a DataFrame with Id, Text columns
        
    Returns:
        JSON string representation of a DataFrame with Id, Text, and AbstractiveSummary columns
    """
    # Convert JSON string back to DataFrame using StringIO
    df = pd.read_json(StringIO(df_json))
    result_df = await generate_abstractive_summaries_async(df)
    return result_df.to_json()

def comparison_reporter_tool(df_json: str):
    """Generate a comparison report for the provided summaries.
    
    Args:
        df_json: JSON string representation of a DataFrame with Id, Text, 
                ExtractiveSummary, and AbstractiveSummary columns
        
    Returns:
        String containing the markdown formatted comparison report
    """
    # Convert JSON string back to DataFrame using StringIO
    df = pd.read_json(StringIO(df_json))
    return generate_comparison_report(df)

# Define our main summarization agent
def create_summarization_agent():
    """Create and return the main summarization agent with its tools."""
    
    # Create tools
    extractive_tool = function_tool(
        func=extractive_summarizer_tool,
        name_override="extractive_summarizer", 
        description_override="Extracts the first sentence from reviews as a deterministic summary."
    )
    
    abstractive_tool = function_tool(
        func=abstractive_summarizer_tool,
        name_override="abstractive_summarizer",
        description_override="Generates an abstractive summary using LLMs for each review."
    )
    
    comparison_tool = function_tool(
        func=comparison_reporter_tool,
        name_override="comparison_reporter",
        description_override="Generates a comparison report between extractive and abstractive summaries."
    )
    
    # Define the agent with tools
    summarization_agent = Agent(
        name="review_summarization_agent",
        instructions="You are an expert review analysis agent that creates and compares different types of summaries. Process customer reviews to generate both extractive and abstractive summaries, then compare them. You were designed to help analyze customer feedback by generating different summary types and comparing their effectiveness.",
        tools=[extractive_tool, abstractive_tool, comparison_tool]
    )
    
    return summarization_agent

async def run_agent_workflow(csv_path: str, output_report_path: str = "comparison_report.md"):
    """
    Run the complete agent workflow to summarize and compare reviews.
    """
    print(f"Starting review summarization agent workflow for: {csv_path}")
    
    # Create the agent
    agent = create_summarization_agent()
    
    # Prepare the user message with instructions
    user_message = f"""
    Analyze the customer reviews in the file '{csv_path}'. 
    
    Please follow these steps:
    1. First, generate extractive summaries for the reviews
    2. Then, generate abstractive summaries for the same reviews
    3. Finally, create a comparison report between both summary types and save it to '{output_report_path}'
    
    After completing these steps, provide a brief explanation of what you found.
    """
    
    # Run the agent
    print("Starting agent execution...")
    result = await Runner.run(agent, user_message)
    
    print("Agent execution completed!")
    print(f"Final output: {result.final_output}")
    
    # First try to directly process the reviews and generate the comparison report
    try:
        # Process the reviews - this ensures we generate a report no matter what
        df = generate_extractive_summaries(csv_path)
        df = await generate_abstractive_summaries_async(df.copy())
        report = generate_comparison_report(df)
        
        # Save the report
        with open(output_report_path, 'w') as f:
            f.write(report)
        print(f"Report was successfully generated and saved to: {output_report_path}")
        
    except Exception as e:
        print(f"Error generating report directly: {e}")
        
        # Check if the report was saved by the agent
        if os.path.exists(output_report_path):
            print(f"Report was found at: {output_report_path}")
        else:
            print(f"Report was not found at: {output_report_path}")
            # Try to save the agent's output as a fallback
            try:
                with open(output_report_path, 'w') as f:
                    f.write(result.final_output)
                print(f"Saved agent output to: {output_report_path} as fallback")
            except Exception as e:
                print(f"Error saving fallback report: {e}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Review Summarization Agent')
    parser.add_argument('--input', type=str, default='First10Reviews.csv',
                        help='Path to the input CSV file containing reviews')
    parser.add_argument('--output', type=str, default='comparison_report.md',
                        help='Path to save the output comparison report')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Run the agent
    async def main():
        await run_agent_workflow(args.input, args.output)
    
    # Run the async main function
    asyncio.run(main())

    # Note: The abstractive summarizer currently uses placeholders.
    # Integrating a real LLM would require setting up API keys and using
    # either the OpenAI client library directly or the Agents SDK constructs
    # once its API for calling models/sub-agents is clearer.
    # The `nltk.download('punkt')` might run on first execution. 