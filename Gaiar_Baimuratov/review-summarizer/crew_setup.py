"""
CrewAI setup for app review summarization.

This module creates and configures a CrewAI crew consisting of three agents:
1. Extractive Summarizer - Uses TextRank to extract important sentences
2. Abstractive Summarizer - Uses GPT-4o to generate a coherent summary
3. Comparison Evaluator - Uses o1 to compare and evaluate both summaries
"""
import os
import time
from typing import Dict, List, Any, Optional

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our TextRank implementation
from text_rank import TextRankSummarizer

# Constants
MAX_TOKENS_PER_REVIEW = 100  # Approximate tokens per review
MAX_TOTAL_TOKENS = 4000      # Safe limit for GPT-4o context window
MAX_RETRIES = 3             # Number of retries for API calls
RETRY_DELAY = 2             # Seconds to wait between retries

class TextRankTool(BaseTool):
    """Tool for TextRank-based extractive summarization."""
    
    name: str = "Extractive Summarizer"
    description: str = "Extracts the most important sentences from app reviews using TextRank algorithm"
    summarizer: TextRankSummarizer = Field(default_factory=TextRankSummarizer)
    
    def _run(self, reviews_text: str, num_sentences: int = 5) -> str:
        """
        Run extractive summarization on the input text.
        
        Args:
            reviews_text: Text containing app reviews
            num_sentences: Number of sentences to extract
            
        Returns:
            Extractive summary
        """
        try:
            return self.summarizer.summarize(reviews_text, int(num_sentences))
        except Exception as e:
            raise RuntimeError(f"TextRank summarization failed: {str(e)}")


def reviews_to_text(reviews: List[Dict], max_reviews: Optional[int] = None) -> str:
    """
    Convert review dictionaries to a single text string.
    
    Args:
        reviews: List of review dictionaries
        max_reviews: Maximum number of reviews to include (None for all)
        
    Returns:
        Reviews formatted as text
    """
    # Calculate max reviews based on token limits if not specified
    if max_reviews is None:
        max_reviews = min(len(reviews), MAX_TOTAL_TOKENS // MAX_TOKENS_PER_REVIEW)
    
    # Limit number of reviews if needed
    limited_reviews = reviews[:max_reviews]
    
    reviews_text = []
    for review in limited_reviews:
        rating = review.get("rating", "Unknown")
        body = review.get("body", "").strip()
        if body:
            reviews_text.append(f"Rating: {rating} stars\n{body}")
    
    return "\n\n".join(reviews_text)


def create_crew(reviews: List[Dict], verbose: bool = False) -> Crew:
    """
    Create and configure a CrewAI crew for summarizing app reviews.
    
    Args:
        reviews: List of review dictionaries
        verbose: Enable verbose mode
        
    Returns:
        Configured CrewAI crew
    """
    # Convert reviews to text with token limit consideration
    reviews_text = reviews_to_text(reviews)
    
    # Create TextRank tool
    text_rank_tool = TextRankTool()
    
    # Create the extractive summarizer agent
    extractive_agent = Agent(
        role="Extractive Summarizer",
        goal="Extract the most important sentences from app reviews",
        backstory=(
            "You are an expert in Natural Language Processing and text analysis. "
            "Your specialty is identifying the most significant sentences in text "
            "using advanced algorithms like TextRank. You have a keen eye for "
            "identifying key themes and important user feedback in app reviews."
        ),
        tools=[text_rank_tool],
        verbose=verbose,
        allow_delegation=False,
        memory=True
    )
    
    # Create the abstractive summarizer agent
    abstractive_agent = Agent(
        role="Abstractive Summarizer",
        goal="Create a coherent, readable summary of app reviews",
        backstory=(
            "You are a skilled content writer and analyst with expertise in "
            "synthesizing large amounts of information into clear, concise summaries. "
            "You excel at identifying patterns and trends in user feedback and "
            "presenting them in an engaging, informative way."
        ),
        llm="gpt-4o",
        verbose=verbose,
        allow_delegation=False,
        memory=True
    )
    
    # Create the comparison agent
    comparison_agent = Agent(
        role="Summary Evaluator",
        goal="Evaluate and compare different summarization approaches",
        backstory=(
            "You are an expert in evaluating and comparing different types of "
            "summaries. You have a deep understanding of both extractive and "
            "abstractive summarization techniques and can provide insightful "
            "analysis of their respective strengths and weaknesses."
        ),
        llm="o1",
        verbose=verbose,
        allow_delegation=False,
        memory=True
    )
    
    # Create tasks
    extractive_task = Task(
        description=f"""
        Analyze these app reviews and extract the 5-7 most important sentences that capture the main points.
        Focus on sentences that represent common themes, significant issues, or notable praise.
        
        APP REVIEWS:
        {reviews_text}
        """,
        agent=extractive_agent,
        expected_output="A list of the most important sentences from the reviews.",
        output_file="extractive_summary.txt",
        name="extractive_task"
    )
    
    abstractive_task = Task(
        description=f"""
        Create a coherent, well-written summary of these app reviews. Your summary should:
        1. Highlight the main themes and trends
        2. Mention both positive and negative feedback
        3. Note any specific features or issues that appear frequently
        4. Keep the summary concise (around 150-200 words)
        
        APP REVIEWS:
        {reviews_text}
        """,
        agent=abstractive_agent,
        expected_output="A well-written summary of the reviews in paragraph form.",
        output_file="abstractive_summary.txt",
        name="abstractive_task"
    )
    
    comparison_task = Task(
        description="""
        Compare these two summaries of app reviews and evaluate their strengths and weaknesses:
        
        EXTRACTIVE SUMMARY:
        {extractive_summary}
        
        ABSTRACTIVE SUMMARY:
        {abstractive_summary}
        
        Analyze both summaries based on:
        1. Completeness - Which summary captures more important information?
        2. Accuracy - Which summary better represents the original reviews?
        3. Readability - Which summary is easier to understand?
        4. Usefulness - Which summary would be more helpful for app developers?
        
        Provide a structured evaluation with specific examples from each summary.
        Conclude with a recommendation of which summary is more effective overall.
        """,
        agent=comparison_agent,
        expected_output="A detailed comparison of both summaries with a final recommendation.",
        output_file="comparison.txt",
        name="comparison_task"
    )
    
    # Create crew with sequential process
    crew = Crew(
        agents=[extractive_agent, abstractive_agent, comparison_agent],
        tasks=[extractive_task, abstractive_task, comparison_task],
        process=Process.sequential,
        verbose=verbose
    )
    
    return crew


def run_crew(reviews: List[Dict], verbose: bool = False) -> Dict[str, str]:
    """
    Run the CrewAI pipeline on app reviews.
    
    Args:
        reviews: List of review dictionaries
        verbose: Enable verbose mode
        
    Returns:
        Dictionary with summary results
        
    Raises:
        ValueError: If OpenAI API key is missing
        RuntimeError: If summarization pipeline fails
    """
    # Ensure we have an OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Print debug information
    if verbose:
        print(f"OpenAI API Key format: {os.environ['OPENAI_API_KEY'][:10]}...")
        print(f"Number of reviews to process: {len(reviews)}")
    
    # Create crew
    crew = create_crew(reviews, verbose)
    
    # Run the crew with retries
    for attempt in range(MAX_RETRIES):
        try:
            if verbose:
                print(f"Attempt {attempt + 1} of {MAX_RETRIES}")
            result = crew.kickoff()
            break
        except Exception as e:
            if verbose:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Summarization pipeline failed after {MAX_RETRIES} attempts: {str(e)}")
            time.sleep(RETRY_DELAY)
    
    # Parse results
    try:
        # Get task outputs from the result list
        return {
            "extractive_summary": result.tasks_output[0],  # First task output
            "abstractive_summary": result.tasks_output[1],  # Second task output
            "comparison": result.tasks_output[2]  # Third task output
        }
    except Exception as e:
        if verbose:
            print(f"Raw result: {result}")
        raise RuntimeError(f"Error parsing crew output: {str(e)}")


if __name__ == "__main__":
    # Simple test
    test_reviews = [
        {"body": "This app is great! I love the new features they added.", "rating": 5},
        {"body": "The app crashes every time I try to open it. Very frustrating.", "rating": 1},
        {"body": "Good app but it drains my battery too quickly.", "rating": 3},
        {"body": "The latest update fixed many bugs. Much better performance now.", "rating": 4},
        {"body": "Interface is confusing and not user-friendly.", "rating": 2}
    ]
    
    results = run_crew(test_reviews, verbose=True)
    
    print("\n=== EXTRACTIVE SUMMARY ===")
    print(results["extractive_summary"])
    
    print("\n=== ABSTRACTIVE SUMMARY ===")
    print(results["abstractive_summary"])
    
    print("\n=== COMPARISON ===")
    print(results["comparison"])