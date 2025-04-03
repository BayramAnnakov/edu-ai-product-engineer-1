from agents import Agent, function_tool, Runner
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import os
import time
from utils import get_article_text
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
def extractive_summarizer(text: str, num_sentences: int) -> tuple[str, float]:
    """Generate an extractive summary using NLTK."""
    start_time = time.time()
    summary = extractive_summarize(text, num_sentences)
    processing_time = time.time() - start_time
    return summary, processing_time

@function_tool
def abstractive_summarizer(text: str, max_length: int) -> tuple[str, float]:
    """Generate an abstractive summary using OpenAI."""
    start_time = time.time()
    summary = abstractive_summarize(text, max_length)
    processing_time = time.time() - start_time
    return summary, processing_time

@function_tool
def comparison_report(extractive: str, abstractive: str) -> str:
    """Generate a comparison report between extractive and abstractive summaries."""
    return generate_comparison_report(extractive, abstractive)

@function_tool
def visualization_tool(text: str, extractive: str, abstractive: str, extractive_time: float, abstractive_time: float) -> str:
    """Generate a visualization comparing the summaries."""
    # Use analyze_summaries to handle metrics calculation and visualization
    return analyze_summaries(text, extractive, abstractive, extractive_time, abstractive_time, output_file="visualization_text_analysis.png")

# Main agent with tools
text_summarizer_agent = Agent(
    name="Text Summarizer",
    instructions="""You are a text summarization expert. Your task is to:
    1. Generate both extractive and abstractive summaries
    2. Compare the two approaches and provide insights about their differences
    3. Generate a visualization of the comparison
    
    For extractive summary, use 5 sentences.
    For abstractive summary, limit to 150 words.
    """,
    tools=[extractive_summarizer, abstractive_summarizer, comparison_report, visualization_tool],
    model="gpt-4o-mini"
)

async def main():
    load_dotenv()
    
    # Read text from file
    file_path = "oreilly_endofprogramming.txt"
    text = get_article_text(file_path)
    
    if text.startswith("Error reading file"):
        print(f"Error: {text}")
        return
    
    result = await Runner.run(
        text_summarizer_agent, 
        f"""Please analyze this text and provide:
        1. An extractive summary using 5 sentences
        2. An abstractive summary limited to 150 words
        3. A comparison of the two approaches
        4. A visualization of the comparison
        
        Text to analyze:
        {text}
        """
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())