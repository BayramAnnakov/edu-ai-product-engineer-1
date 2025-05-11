import os
import pandas as pd
import time
from typing import Dict, List, Tuple, Any, Optional, TypedDict, Annotated
import operator
from pathlib import Path # For file path handling
from loguru import logger # Using Loguru for logging consistency
from dotenv import load_dotenv

# --- LangChain & LangGraph ---
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# --- Summarizer Imports ---
from data_loader import load_reviews
from summary_workflow import extractive_summarize

# --- Configuration ---
load_dotenv()
logger.info("Loading environment variables...")

CSV_FILE_PATH = "Vladimir_Kovtunovskiy/Reviews.csv" # <--- Adjust path if needed
NUM_REVIEWS_TO_SELECT = 15 # Number of reviews for the workflow
EXTRACTIVE_SUMMARY_SENTENCES = 5
LLM_MODEL_NAME = "gpt-4o-mini" # Or "gpt-3.5-turbo", "gpt-4", etc.

# --- API Key Check ---
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not found in environment variables.")
    raise ValueError("Missing OPENAI_API_KEY")

# --- Initialize LLM (Needed for Abstractive Summary & Comparison) ---
logger.info(f"Initializing LLM: {LLM_MODEL_NAME}")
try:
    llm = ChatOpenAI(model=LLM_MODEL_NAME, temperature=0.3) # Lower temp for more focused summaries/comparisons
    logger.info("LLM initialized successfully.")
except Exception as e:
    logger.error(f"FATAL: Error initializing LLM: {e}")
    exit()

# --- Define Agent State ---
class WorkflowState(TypedDict):
    """State for the multi-step summarization and comparison workflow."""
    # Inputs (can be set initially)
    num_reviews_to_select: int
    num_extractive_sentences: int
    file_path: str

    # Data flowing through the graph
    reviews_df: Optional[pd.DataFrame] = None # Loaded DataFrame
    selected_reviews_text: Optional[str] = None # Combined text of selected reviews
    extractive_summary: Optional[str] = None
    abstractive_summary: Optional[str] = None
    comparison_report: Optional[str] = None

    # Status & Error Handling
    error_message: Optional[str] = None
    status: str = "Pending"

# --- Define Node Functions ---
logger.info("Defining graph node functions...")

def node_load_and_select_reviews(state: WorkflowState) -> Dict[str, Any]:
    """Loads reviews, selects a random sample, and stores the combined text."""
    logger.info("--- Node: Load and Select Reviews ---")
    num_select = state['num_reviews_to_select']
    f_path = state['file_path']
    try:
        # Load enough data to sample from (adjust if dataset is huge)
        # Loading None might be too much, load maybe 2*num_select or 1000?
        df = load_reviews(file_path=f_path, nrows=max(num_select*2, 1000)) # Load more than needed to sample

        if len(df) < num_select:
            logger.warning(f"Only {len(df)} reviews loaded, using all.")
            sample_df = df
        else:
            logger.info(f"Selecting {num_select} random reviews...")
            sample_df = df.sample(n=num_select, random_state=42)

        # Combine text (handle potential NaN)
        combined_text = " ".join(sample_df["Text"].fillna('').astype(str).tolist())
        logger.info(f"Combined text generated ({len(combined_text)} chars).")

        # Don't store the whole df in state if not needed later, just the text
        # If you *do* need the sample_df later, return {"reviews_df": sample_df, ...}
        return {"selected_reviews_text": combined_text, "status": "Reviews Selected"}

    except Exception as e:
        logger.error(f"Error loading/selecting reviews: {e}")
        return {"error_message": f"Failed during review loading/selection: {e}", "status": "Failed"}

def node_generate_extractive_summary(state: WorkflowState) -> Dict[str, Any]:
    """Generates the extractive summary for the selected text."""
    logger.info("--- Node: Generate Extractive Summary ---")
    text = state.get("selected_reviews_text")
    num_sentences = state.get("num_extractive_sentences")

    if not text:
        logger.error("Cannot generate extractive summary: No text available.")
        return {"error_message": "Input text for extractive summary missing.", "status": "Failed"}

    try:
        summary = extractive_summarize(text, num_sentences)
        return {"extractive_summary": summary, "status": "Extractive Summary Done"}
    except Exception as e:
        logger.error(f"Error during extractive summarization: {e}")
        return {"extractive_summary": f"Error: {e}", "error_message": f"Extractive summarization failed: {e}", "status": "Failed"}

def node_generate_abstractive_summary(state: WorkflowState) -> Dict[str, Any]:
    """Generates an abstractive summary using the LLM."""
    logger.info("--- Node: Generate Abstractive Summary (LLM) ---")
    text = state.get("selected_reviews_text")

    if not text:
        logger.error("Cannot generate abstractive summary: No text available.")
        return {"error_message": "Input text for abstractive summary missing.", "status": "Failed"}

    try:
        # Simple prompt for abstractive summary
        prompt_text = f"""
        Based on the following collection of product reviews, please write a concise abstractive summary (1-2 paragraphs) capturing the main themes and overall sentiment. Do not just extract sentences.

        Reviews Text:
        \"\"\"
        {text[:15000]}
        \"\"\"

        Abstractive Summary:
        """ # Truncate input text to LLM to avoid context limits

        messages = [
            SystemMessage(content="You are a helpful assistant skilled at summarizing text."),
            HumanMessage(content=prompt_text)
        ]
        response = llm.invoke(messages)
        summary = response.content
        logger.info("Abstractive summary generated.")
        return {"abstractive_summary": summary, "status": "Abstractive Summary Done"}

    except Exception as e:
        logger.error(f"Error during abstractive summarization (LLM): {e}")
        return {"abstractive_summary": f"Error: {e}", "error_message": f"Abstractive summarization failed: {e}", "status": "Failed"}

def node_generate_comparison_report(state: WorkflowState) -> Dict[str, Any]:
    """Compares the two summaries using the LLM."""
    logger.info("--- Node: Generate Comparison Report (LLM) ---")
    ext_summary = state.get("extractive_summary")
    abs_summary = state.get("abstractive_summary")
    original_text_snippet = state.get("selected_reviews_text", "")[:500] # Include snippet for context

    # Check if summaries are available and valid
    if not ext_summary or ext_summary.startswith("Error:"):
        msg = "Cannot compare: Extractive summary missing or invalid."
        logger.error(msg)
        return {"error_message": msg, "status": "Failed"}
    if not abs_summary or abs_summary.startswith("Error:"):
        msg = "Cannot compare: Abstractive summary missing or invalid."
        logger.error(msg)
        return {"error_message": msg, "status": "Failed"}

    try:
        prompt_text = f"""
        Compare the following two summaries generated from the same collection of product reviews.

        Original Text Snippet (for context):
        \"\"\"
        {original_text_snippet}...
        \"\"\"

        Extractive Summary:
        \"\"\"
        {ext_summary}
        \"\"\"

        Abstractive Summary:
        \"\"\"
        {abs_summary}
        \"\"\"

        Comparison Report:
        Please analyze the differences between the extractive and abstractive summaries. Consider:
        - Readability and flow.
        - Faithfulness to the original content (based on the summaries themselves).
        - Conciseness.
        - Information overlap and unique points.
        - Which summary might be better for getting a quick overview vs. understanding the nuanced themes?
        """
        messages = [
            SystemMessage(content="You are an AI assistant comparing text summarization methods."),
            HumanMessage(content=prompt_text)
        ]
        response = llm.invoke(messages)
        report = response.content
        logger.info("Comparison report generated.")
        return {"comparison_report": report, "status": "Completed"} # Final success state

    except Exception as e:
        logger.error(f"Error during comparison report generation (LLM): {e}")
        return {"comparison_report": f"Error: {e}", "error_message": f"Comparison report failed: {e}", "status": "Failed"}


logger.info("Node functions defined.")

# --- Build the Graph ---
logger.info("Building the LangGraph workflow...")
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("load_select", node_load_and_select_reviews)
workflow.add_node("summarize_extractive", node_generate_extractive_summary)
workflow.add_node("summarize_abstractive", node_generate_abstractive_summary)
workflow.add_node("compare_summaries", node_generate_comparison_report)

# Define edges (Sequential flow)
workflow.set_entry_point("load_select")
workflow.add_edge("load_select", "summarize_extractive")
# We can run abstractive in parallel *if desired*, but let's keep it simple first
workflow.add_edge("summarize_extractive", "summarize_abstractive")
workflow.add_edge("summarize_abstractive", "compare_summaries")
workflow.add_edge("compare_summaries", END) # End after comparison

# Compile the graph
app = workflow.compile()
logger.info("LangGraph workflow compiled successfully.")
logger.info("Graph Structure:")
# Requires graphviz: app.get_graph().print_ascii() or save png

# --- Main Execution Block ---
if __name__ == "__main__":
    logger.info("\n--- Starting LangGraph Workflow Execution ---")
    start_run_time = time.time()

    # Define initial inputs for the workflow state
    initial_inputs = {
        "num_reviews_to_select": NUM_REVIEWS_TO_SELECT,
        "num_extractive_sentences": EXTRACTIVE_SUMMARY_SENTENCES,
        "file_path": CSV_FILE_PATH,
    }

    logger.info(f"Initial Inputs: {initial_inputs}")

    # Invoke the graph with the initial inputs
    # The state dictionary is implicitly created from initial_inputs
    final_state = None
    try:
        # The config adds a recursion limit as a safety measure
        final_state = app.invoke(initial_inputs, config={"recursion_limit": 10})

        run_duration = time.time() - start_run_time
        logger.info(f"--- Workflow Execution Finished (Duration: {run_duration:.2f} seconds) ---")

        # Print results from the final state
        print("\n" + "="*50)
        print("WORKFLOW RESULTS")
        print("="*50)
        print(f"Final Status: {final_state.get('status', 'Unknown')}")
        if final_state.get('error_message'):
            print(f"Error Message: {final_state.get('error_message')}")

        print("\n--- Extractive Summary ---")
        print(final_state.get('extractive_summary', 'Not generated or error.'))

        print("\n--- Abstractive Summary ---")
        print(final_state.get('abstractive_summary', 'Not generated or error.'))

        print("\n--- Comparison Report ---")
        print(final_state.get('comparison_report', 'Not generated or error.'))
        print("="*50)

        # Optionally save the full state or specific fields to JSON/CSV
        # logger.info("Saving final state to results.json")
        # with open("results.json", "w") as f:
        #     # Need to handle non-serializable types like DataFrame if present
        #     serializable_state = {k: v for k, v in final_state.items() if k != 'reviews_df'}
        #     json.dump(serializable_state, f, indent=2)


    except Exception as e:
        run_duration = time.time() - start_run_time
        logger.error(f"--- Workflow Invocation Error (Duration: {run_duration:.2f} seconds) ---")
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        if final_state: # Print partial state if available
             print("\nPartial Final State:")
             # Handle non-serializable types if printing directly
             print({k: v for k, v in final_state.items() if k != 'reviews_df'})


    logger.info("Script finished.")