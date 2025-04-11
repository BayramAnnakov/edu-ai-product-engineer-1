import pandas as pd
import os, time
from typing import Dict, List, Tuple, Any, Optional, TypedDict, Annotated
import operator
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from data_loader import load_reviews
import json
from dotenv import load_dotenv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from string import punctuation
from heapq import nlargest
from collections import defaultdict

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt data...")
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Downloading NLTK stopwords data...")
    nltk.download('stopwords')

# Try to download punkt_tab if needed
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("Downloading NLTK punkt_tab data...")
    nltk.download('punkt_tab')

# Load environment variables from .env file
load_dotenv()

# Define the state schema for our agent
class SummaryReportAgentState(TypedDict):
    review_data: Optional[pd.DataFrame]
    extractive_summary: Optional[str]
    abstractive_summary: Optional[str]
    comparison_report: Optional[str]
    error_message: Optional[str]
    status: str

def extractive_summarize(text: str, num_sentences: int = 5) -> str:
    """
    Generate an extractive summary using NLTK.
    This approach selects the most important sentences based on word frequency.
    
    Args:
        text (str): The text to summarize
        num_sentences (int): Number of sentences to include in the summary
        
    Returns:
        str: The generated summary
    """
    try:
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        
        # Tokenize words and remove stopwords
        stop_words = set(stopwords.words('english') + list(punctuation))
        word_freq = defaultdict(int)
        
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            for word in words:
                if word not in stop_words:
                    word_freq[word] += 1
        
        # Calculate sentence scores based on word frequencies
        sentence_scores = defaultdict(int)
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            for word in words:
                if word in word_freq:
                    sentence_scores[sentence] += word_freq[word]
        
        # Get the top sentences
        summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        
        # Join sentences to create summary
        summary = ' '.join(summary_sentences)
        return summary
    except Exception as e:
        print(f"Error in extractive_summarize: {str(e)}")
        # Fallback to a simple approach if NLTK fails
        print("Using fallback summarization method...")
        # Split by periods and take the first few sentences
        sentences = text.split('.')
        summary_sentences = sentences[:num_sentences]
        return '. '.join(summary_sentences) + '.'
    
def node_load_review_data(state: SummaryReportAgentState) -> Dict[str, Any]:
    """Load review data from the CSV file."""
    try:
        df = load_reviews(file_path="Vladimir_Kovtunovskiy/Reviews.csv", nrows=100)
        return {"review_data": df, "status": "Data Loaded"}
    except Exception as e:
        return {"error_message": f"Error loading reviews: {str(e)}", "status": "Error"}
    
    
def node_extract_summary(state: SummaryReportAgentState) -> Dict[str, Any]:
    """Generates the extractive summary."""
    if state.get("review_data") is None:
        return {"error_message": "No review data available", "status": "Error"}
    
    try:
        # Get the review data
        df = state["review_data"]
        print(f"Loaded review data with {len(df)} rows")
        
        # Check if Text column exists
        if "Text" not in df.columns:
            print(f"Available columns: {df.columns.tolist()}")
            return {"error_message": "Text column not found in review data", "status": "Error"}
        
        # Combine all review texts into a single text
        all_reviews = " ".join(df["Text"].astype(str).tolist())
        print(f"Combined text length: {len(all_reviews)} characters")
        
        # Generate extractive summary
        summary = extractive_summarize(all_reviews, num_sentences=5)
        print(f"Generated extractive summary: {summary[:200]}...")
        
        # Update the state with the summary and change status
        return {"extractive_summary": summary, "status": "Extractive Done"}
    except Exception as e:
        print(f"Error in node_extract_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error_message": f"Error generating extractive summary: {str(e)}", "status": "Error"}

def node_abstractive_summary(state: SummaryReportAgentState) -> Dict[str, Any]:
    """Generates the abstractive summary using OpenAI's GPT-4o-mini model."""
    if state.get("extractive_summary") is None:
        return {"error_message": "No extractive summary available", "status": "Error"}
    
    try:
        # Get the review data
        df = state["review_data"]
        print(f"Loaded review data with {len(df)} rows")
        
        # Check if Text column exists
        if "Text" not in df.columns:
            print(f"Available columns: {df.columns.tolist()}")
            return {"error_message": "Text column not found in review data", "status": "Error"}
        
        # Combine all review texts into a single text
        all_reviews = " ".join(df["Text"].astype(str).tolist())
        
        # Create the LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        # Create a prompt template for abstractive summarization
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at summarizing product reviews. Your task is to create a concise, coherent, and informative abstractive summary based on reviews provided. The abstractive summary should capture the key points, sentiment, and insights from the reviews in a natural, flowing narrative."),
            ("human", "Here is an extractive summary of product reviews:\n\n{all_reviews}\n\nPlease create an abstractive summary that captures the key points, sentiment, and insights from these reviews in a natural, flowing narrative. The summary should be concise (around 3-5 sentences).")
        ])
        
        # Create a chain to generate the abstractive summary
        chain = prompt | llm
        
        # Generate the abstractive summary
        start_time = time.time()
        response = chain.invoke({"all_reviews": all_reviews})
        abstractive_summary = response.content
        processing_time = time.time() - start_time
        
        print(f"Generated abstractive summary in {processing_time:.2f} seconds")
        
        # Update the state with the summary and change status
        return {"abstractive_summary": abstractive_summary, "status": "Abstractive Done"}
    except Exception as e:
        print(f"Error in node_abstractive_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error_message": f"Error generating abstractive summary: {str(e)}", "status": "Error"}

def node_comparison_report(state: SummaryReportAgentState) -> Dict[str, Any]:
    """Generates the comparison report."""
    if state.get("abstractive_summary") is None:
        return {"error_message": "No abstractive summary available", "status": "Error"}
    if state.get("extractive_summary") is None:
        return {"error_message": "No extractive summary available", "status": "Error"}
    
    try:
        # Get the extractive summary from the state
        extractive_summary = state["extractive_summary"]
        abstractive_summary = state["abstractive_summary"]
        
        # Create the comparison report
        report = f"Comparison Report:\n\n"
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at comparing two summaries of product reviews. Your task is to create a concise, coherent, and informative comparison report based on the two summaries provided. The comparison report should capture the key points, sentiment, and insights from the two summaries in a natural, flowing narrative."),
            ("human", "Here are the two summaries of product reviews:\n\nExtractive Summary:\n{extractive_summary}\n\nAbstractive Summary:\n{abstractive_summary}\n\nPlease create a comparison report that captures the key points, sentiment, and insights from the two summaries in a natural, flowing narrative.")
        ])

        chain = prompt | llm
        response = chain.invoke({"extractive_summary": extractive_summary, "abstractive_summary": abstractive_summary})
        
        # Update the state with the report and change status
        return {"comparison_report": response.content, "status": "Comparison Done"}
    except Exception as e:
        print(f"Error in node_comparison_report: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error_message": f"Error generating comparison report: {str(e)}", "status": "Error"}

    # Update the state with the report and change status
    return {"comparison_report": "Comparison report placeholder", "status": "Comparison Done"}
    
def create_basic_workflow():
    # Create a state graph
    graph = StateGraph(SummaryReportAgentState)

    # Add nodes with unique names that don't conflict with state keys
    graph.add_node("load_data_node", node_load_review_data)
    graph.add_node("extract_summary_node", node_extract_summary)
    graph.add_node("abstractive_summary_node", node_abstractive_summary)
    graph.add_node("comparison_report_node", node_comparison_report)

    # Add edges
    graph.add_edge("load_data_node", "extract_summary_node")
    graph.add_edge("extract_summary_node", "abstractive_summary_node")
    graph.add_edge("abstractive_summary_node", "comparison_report_node")
    graph.add_edge("comparison_report_node", END)

    # Set entry point
    graph.set_entry_point("load_data_node")

    # Compile the graph
    return graph.compile()

if __name__ == "__main__":
    # Create the agent
    agent = create_basic_workflow()
    
    # Create initial state
    initial_state = {
        "review_data": None,
        "extractive_summary": None,
        "abstractive_summary": None,
        "comparison_report": None,
        "error_message": None,
        "status": "Pending"
    }
    
    # Run the agent
    start_time = time.time()
    result = agent.invoke(initial_state)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Print the result
    print("\n=== Agent Execution Result ===")
    print(f"Status: {result['status']}")
    
    if result.get('error_message'):
        print(f"Error: {result['error_message']}")
    else:
        print("\n=== Summary Report ===")
        if result.get('extractive_summary'):
            print("\n--- Extractive Summary ---")
            print(result['extractive_summary'])
        else:
            print("Extractive Summary: Not available")
            
        if result.get('abstractive_summary'):
            print("\n--- Abstractive Summary ---")
            print(result['abstractive_summary'])
        else:
            print("Abstractive Summary: Not available")
            
        if result.get('comparison_report'):
            print("\n--- Comparison Report ---")
            print(result['comparison_report'])
        else:
            print("Comparison Report: Not available")
    
    
    
    