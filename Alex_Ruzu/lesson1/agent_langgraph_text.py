from typing import Dict, List, Tuple, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import os
from dotenv import load_dotenv
import time

# Import the same tools used in CrewAI implementation
from extractive_summarizer import extractive_summarize
from abstractive_summarizer import abstractive_summarize
from compare_summarizers import generate_comparison_report
from visualization_tool import generate_visualization, analyze_summaries

# Load environment variables
load_dotenv()

# Define our state type
class SummarizationState(TypedDict):
    """State for the summarization workflow."""
    text: str
    extractive_summary: str
    abstractive_summary: str
    comparison_result: str
    current_step: str
    error_message: str

# Define our tools using the external modules
def extractive_summarizer(text: str) -> Tuple[str, float]:
    """Extract key sentences from text using the external module."""
    start_time = time.time()
    summary = extractive_summarize(text, num_sentences=5)  # Use 5 sentences as specified
    processing_time = time.time() - start_time
    return summary, processing_time

def abstractive_summarizer(text: str) -> Tuple[str, float]:
    """Generate a concise summary of the text using the external module."""
    start_time = time.time()
    summary = abstractive_summarize(text, max_length=150)  # Limit to 150 words as specified
    processing_time = time.time() - start_time
    return summary, processing_time

def comparison_report(state: SummarizationState) -> SummarizationState:
    """Generate comparison report between summaries."""
    report = generate_comparison_report(
        state["extractive_summary"],
        state["abstractive_summary"]
    )
    state["comparison_result"] = report
    return state

# Define our node functions
def extractive_node(state: SummarizationState) -> SummarizationState:
    """Node for extractive summarization."""
    try:
        summary, _ = extractive_summarizer(state["text"])
        return {
            **state,
            "extractive_summary": summary,
            "current_step": "abstractive",
            "error_message": ""
        }
    except Exception as e:
        return {
            **state,
            "error_message": f"Error in extractive summarization: {str(e)}",
            "current_step": "error"
        }

def abstractive_node(state: SummarizationState) -> SummarizationState:
    """Node for abstractive summarization."""
    try:
        summary, _ = abstractive_summarizer(state["text"])
        return {
            **state,
            "abstractive_summary": summary,
            "current_step": "comparison",
            "error_message": ""
        }
    except Exception as e:
        return {
            **state,
            "error_message": f"Error in abstractive summarization: {str(e)}",
            "current_step": "error"
        }

def comparison_node(state: SummarizationState) -> SummarizationState:
    """Node for comparison."""
    try:
        comparison, _ = comparison_report(
            state["extractive_summary"],
            state["abstractive_summary"]
        )
        return {
            **state,
            "comparison_result": comparison,
            "current_step": "end",
            "error_message": ""
        }
    except Exception as e:
        return {
            **state,
            "error_message": f"Error in comparison: {str(e)}",
            "current_step": "error"
        }

def should_continue(state: SummarizationState) -> str:
    """Determine the next node based on current state."""
    if state["error_message"]:
        return "error"
    return state["current_step"]

def error_node(state: SummarizationState) -> SummarizationState:
    """Handle errors in the workflow."""
    print(f"\nError occurred: {state['error_message']}")
    return state

# Create the graph
def create_summarization_workflow() -> StateGraph:
    """Create the summarization workflow graph."""
    # Create the graph
    workflow = StateGraph(SummarizationState)
    
    # Add nodes
    workflow.add_node("extractive", lambda state: {
        **state,
        "extractive_summary": extractive_summarizer(state["text"])[0]
    })
    
    workflow.add_node("abstractive", lambda state: {
        **state,
        "abstractive_summary": abstractive_summarizer(state["text"])[0]
    })
    
    workflow.add_node("comparison", comparison_report)
    
    # Add edges
    workflow.add_edge("extractive", "abstractive")
    workflow.add_edge("abstractive", "comparison")
    workflow.add_edge("comparison", END)
    
    # Set entry point
    workflow.set_entry_point("extractive")
    
    return workflow

def visualize_graph(graph: StateGraph):
    """Visualize the graph structure in the terminal."""
    try:
        # Try to use graphviz directly
        import graphviz
        
        # Create a new directed graph
        dot = graphviz.Digraph(comment='Summarization Workflow')
        dot.attr(rankdir='LR')  # Left to right layout
        
        # Add nodes
        dot.node('extractive', 'Extractive\nSummarization')
        dot.node('abstractive', 'Abstractive\nSummarization')
        dot.node('comparison', 'Comparison')
        dot.node('error', 'Error\nHandling')
        dot.node('end', 'END')
        
        # Add edges
        dot.edge('extractive', 'abstractive')
        dot.edge('abstractive', 'comparison')
        dot.edge('comparison', 'end')
        dot.edge('extractive', 'error')
        dot.edge('abstractive', 'error')
        dot.edge('comparison', 'error')
        dot.edge('error', 'end')
        
        # Try to display the graph
        try:
            from IPython.display import Image, display
            # Save to a temporary file and display
            dot.render('temp_graph', format='png', cleanup=True)
            display(Image('temp_graph.png'))
        except ImportError:
            # If IPython is not available, just print the graph structure
            print("\n=== GRAPH STRUCTURE ===")
            print("extractive -> abstractive -> comparison -> END")
            print("extractive -> error -> END")
            print("abstractive -> error -> END")
            print("comparison -> error -> END")
            print("=======================\n")
            
    except ImportError:
        # If graphviz is not available, print a text representation
        print("\n=== GRAPH STRUCTURE ===")
        print("extractive -> abstractive -> comparison -> END")
        print("extractive -> error -> END")
        print("abstractive -> error -> END")
        print("comparison -> error -> END")
        print("=======================\n")
    except Exception as e:
        # If there's any other error, just print a message
        print(f"\nCould not visualize graph: {str(e)}")
        print("Graph structure: extractive -> abstractive -> comparison -> END") 
        
def main():
    """Main function to run the text summarization workflow."""
    try:
        # Load text from file
        with open("oreilly_endofprogramming.txt", "r", encoding="utf-8") as file:
            text = file.read()
        
        # Create initial state
        initial_state: SummarizationState = {
            "text": text,
            "extractive_summary": "",
            "abstractive_summary": "",
            "comparison_result": "",
            "current_step": "extractive",
            "error_message": ""
        }
        
        # Create and compile the graph
        workflow = create_summarization_workflow()
        
        # Visualize the graph structure
        visualize_graph(workflow)
        
        # Compile the graph
        app = workflow.compile()
        
        # Run the workflow
        final_state = app.invoke(initial_state)
        
        # Check for errors
        if final_state["error_message"]:
            print(f"\nError in workflow: {final_state['error_message']}")
            return
        
        # Display results
        print("\n=== EXTRACTIVE SUMMARY ===")
        print(final_state["extractive_summary"])
        
        print("\n=== ABSTRACTIVE SUMMARY ===")
        print(final_state["abstractive_summary"])
        
        print("\n=== COMPARISON ===")
        print(final_state["comparison_result"])
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 