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
from langchain import hub  # Updated import for hub
from data_loader import load_reviews
import json
from dotenv import load_dotenv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from string import punctuation
from heapq import nlargest
from collections import defaultdict
from summary_workflow import extractive_summarize


# Define tools for the agent
@tool
def extractive_summarizer(text: str, num_sentences: int = 5) -> str:
    """Generate an extractive summary using NLTK.
    
    Args:
        text: The text to summarize
        num_sentences: Number of sentences to include in the summary (default: 5)
        
    Returns: 
        A tuple containing the summary and the processing time
    """
    start_time = time.time()
    summary = extractive_summarize(text, num_sentences)
    processing_time = time.time() - start_time
    print(f"Extractive summary generated in {processing_time:.2f} seconds")
    return summary

@tool
def get_random_review_text(num_reviews: int = 10, file_path: str = "Vladimir_Kovtunovskiy/Reviews.csv") -> str:
    """Loads review data, selects a specified number of random reviews, and returns their combined text."""
    try:
        num_reviews = int(num_reviews)
        df = load_reviews(file_path=file_path, nrows=None) # Load enough to sample from
        if "Text" not in df.columns: return f"Error: 'Text' column not found in {file_path}."

        if len(df) < num_reviews:
            sample_df = df
        else:
            sample_df = df.sample(n=num_reviews, random_state=42)

        combined_text = " ".join(sample_df["Text"].fillna('').astype(str).tolist())
        return f"Combined text from {len(sample_df)} reviews: {combined_text}" # Return the text
    except Exception as e:
        return f"Error in get_random_review_text: {str(e)}"

def create_summary_agent():
    # Create the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create the tools
    tools = [extractive_summarizer, get_random_review_text]
    
    # Create a proper prompt for the react agent
    prompt = hub.pull("hwchase17/react")

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools,verbose=True, 
    handle_parsing_errors=True, 
    max_iterations=5)

    return agent_executor

if __name__ == "__main__":
    # Create the agent
    agent = create_summary_agent()
    
    # Run the agent with a more specific prompt
    inputs = {
        "input": "Load 15 random reviews and generate an extractive summary of these reviews using 5 sentences and tools. Then generate an abstractive summary of these reviews without using tools. After that, compare the two summaries and generate a report on the differences.", 
        "chat_history": []
    }
    
    # Invoke the agent
    start_time = time.time()
    result = agent.invoke(inputs)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print("\nFinal Result:")
    print(result)
