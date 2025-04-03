from agents import Agent, function_tool, Runner
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import os
import time
from utils import get_reviews_from_csv
from extractive_summarizer import extractive_summarize
from abstractive_summarizer import abstractive_summarize
from compare_summarizers import generate_comparison_report
from visualization_tool import generate_visualization, analyze_summaries



class SummaryOutput(BaseModel):
    extractive_summary: str
    abstractive_summary: str
    comparison: str
    visualization_path: str

@function_tool
def extractive_summarizer(text: str, max_length: int) -> str:
    """Generate an extractive summary using NLTK."""
    try:
        start_time = time.time()
        # The extractive_summarize function only returns the summary, not a tuple
        summary = extractive_summarize(text, max_length)
        processing_time = time.time() - start_time
        return f"Extractive Summary ({processing_time:.2f}s):\n{summary}"
    except Exception as e:
        print(f"Error in extractive_summarizer: {str(e)}")
        traceback.print_exc()
        return f"Error creating extractive summary: {str(e)}"

@function_tool
def abstractive_summarizer(text: str, max_length: int) -> str:
    """Generate an abstractive summary using OpenAI."""
    try:
        start_time = time.time()
        # The abstractive_summarize function only returns the summary, not a tuple
        summary = abstractive_summarize(text, max_length)
        processing_time = time.time() - start_time
        return f"Abstractive Summary ({processing_time:.2f}s):\n{summary}"
    except Exception as e:
        print(f"Error in abstractive_summarizer: {str(e)}")
        traceback.print_exc()
        return f"Error creating abstractive summary: {str(e)}"

@function_tool
def comparison_report(extractive: str, abstractive: str) -> str:
    """Generate a comparison report between extractive and abstractive summaries."""
    try:
        return generate_comparison_report(extractive, abstractive)
    except Exception as e:
        print(f"Error in comparison_report: {str(e)}")
        traceback.print_exc()
        return f"Error generating comparison report: {str(e)}"

@function_tool
def visualization_tool(text: str, extractive: str, abstractive: str, extractive_time: float, abstractive_time: float) -> str:
    """Generate a visualization comparing the summaries."""
    try:        
        # Use analyze_summaries to handle metrics calculation and visualization
        viz_path = analyze_summaries(text, extractive, abstractive, extractive_time, abstractive_time, output_file="visualization_review_analysis.png")
        return f"Visualization saved to: {viz_path}"
    except Exception as e:
        print(f"Error in visualization_tool: {str(e)}")
        traceback.print_exc()
        return f"Error generating visualization: {str(e)}"

# Main agent with tools
review_summarizer_agent = Agent(
    name="Review Summarizer",
    instructions="""You are a review summarization expert. Your task is to:
    1. Generate both extractive and abstractive summaries of the reviews
    2. Compare the two approaches and provide insights about their differences
    3. Generate a visualization of the comparison
    
    For extractive summary, use 10 sentences.
    For abstractive summary, limit to 300 words.
    """,
    tools=[extractive_summarizer, abstractive_summarizer, comparison_report, visualization_tool],
    model="gpt-4o-mini"
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
    reviews_text = get_reviews_from_csv(csv_path, num_rows=5)
    
    if reviews_text.startswith("Error") or reviews_text.startswith("No reviews"):
        print(f"Error: {reviews_text}")
        return
    
    try:
        result = await Runner.run(
            review_summarizer_agent,
            f"""Please analyze these reviews and provide:
            1. An extractive summary using 10 sentences
            2. An abstractive summary limited to 300 words
            3. A comparison of the two approaches
            4. A visualization of the comparison
            
            Reviews to analyze:
            {reviews_text}
            """
        )
        print(result.final_output)
    except Exception as e:
        print(f"Error running the agent: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())