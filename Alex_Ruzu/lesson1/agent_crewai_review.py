from crewai import Agent, Task, Crew
from crewai.tools import tool
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import os
import time

from utils import get_reviews_from_csv
from utils import get_article_text
from extractive_summarizer import extractive_summarize
from abstractive_summarizer import abstractive_summarize
from compare_summarizers import generate_comparison_report
from visualization_tool import generate_visualization, analyze_summaries

########################################
# Define tools
########################################
@tool
def extractive_summarizer(text: str, num_sentences: int) -> tuple[str, float]:
    """Generate an extractive summary using NLTK."""
    start_time = time.time()
    summary = extractive_summarize(text, num_sentences)
    processing_time = time.time() - start_time
    return summary, processing_time

@tool
def abstractive_summarizer(text: str, max_length: int) -> tuple[str, float]:
    """Generate an abstractive summary using OpenAI."""
    start_time = time.time()
    summary = abstractive_summarize(text, max_length)
    processing_time = time.time() - start_time
    return summary, processing_time

@tool
def comparison_report(extractive: str, abstractive: str) -> str:
    """Generate a comparison report between extractive and abstractive summaries."""
    return generate_comparison_report(extractive, abstractive)

@tool
def visualization_tool(text: str, extractive: str, abstractive: str, extractive_time: float, abstractive_time: float) -> str:
    """Generate a visualization comparing the summaries."""
    # Use analyze_summaries to handle metrics calculation and visualization
    return analyze_summaries(text, extractive, abstractive, extractive_time, abstractive_time, output_file="visualization_text_analysis.png")

########################################
# Define Agents and Tasks
########################################
# Text Summarizer Agent
text_summarizer_agent = Agent(
    role="Text Summarizer",
    goal="""You are a text summarization expert. Your task is to:
    1. Generate both extractive and abstractive summaries
    2. Compare the two approaches and provide insights about their differences
    
    For extractive summary, use 5 sentences.
    For abstractive summary, limit to 150 words.
    """,
    backstory=("An AI specialized in text summarization."),
    llm="gpt-4o-mini",
    verbose=False,  # Reduce verbosity
    memory=True,    
    tools=[extractive_summarizer, abstractive_summarizer, comparison_report],
    max_iter=3,
    cache=False,  # Disable cache for this agent    
)


async def main():
    load_dotenv()

    # Path to the CSV file
    csv_path = "Reviews.csv"
    
    # Check if the file exists
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        return
    
    print(f"Starting review analysis for file: {csv_path}")
    print("Note: Only the first 5 rows of the CSV file will be processed.")
    print("Note: Reviews are expected to be in the 'Text' column.")
    
    # Load reviews directly using the utility function
    text = get_reviews_from_csv(csv_path, num_rows=5)
    
    if text.startswith("Error") or text.startswith("No reviews"):
        print(f"Error: {text}")
        return

    # Create tasks for your agents
    extractive_summarization = Task(
        description=f"Generate an extractive summary using NLTK for the following text: {text}",
        expected_output="Extractive summary with 5 sentences.",
        agent=text_summarizer_agent,
        tools=[extractive_summarizer]
    )

    abstractive_summarization = Task(
        description=f"Generate an abstractive summary using OpenAI for the following text: {text}",    
        expected_output="Abstractive summary with maximum 150 words.",
        agent=text_summarizer_agent,
        tools=[abstractive_summarizer]
    )

    comparison_task = Task(
        description="Generate a comparison report between the extractive and abstractive summaries.",
        expected_output="Comparison report.",
        agent=text_summarizer_agent,
        tools=[comparison_report],
        context=[extractive_summarization, abstractive_summarization]
    )

    # Instantiate your crew with a sequential process
    crew = Crew(
        agents=[text_summarizer_agent],
        tasks=[extractive_summarization, abstractive_summarization, comparison_task],
        verbose=False,  # Reduce verbosity
        memory=True,
        planning=False  # Disable planning feature
    )

    # Kick off the crew and execute the tasks
    try:
        result = crew.kickoff()
        
        # Print a clean, organized output with each summary only once
        print("\n" + "="*50)
        print("TEXT SUMMARIZATION RESULTS")
        print("="*50)
        
        # Print the extractive summary
        if hasattr(extractive_summarization, 'output'):
            print("\nEXTRACTIVE SUMMARY:")
            print("-"*50)
            print(extractive_summarization.output)
        
        # Print the abstractive summary
        if hasattr(abstractive_summarization, 'output'):
            print("\nABSTRACTIVE SUMMARY:")
            print("-"*50)
            print(abstractive_summarization.output)

        # Print the final result
        print("\nCOMPARISON:")
        print("\nFINAL RESULT:")
        print("-"*50)
        print(result)
            
    except Exception as e:
        print(f"An error occurred during task execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())