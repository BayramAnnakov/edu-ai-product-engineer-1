# runner.py
from dotenv import load_dotenv
load_dotenv()

import sys
import os
import shutil
from agent_setup import agents
from agents import Runner
from csv_tool import CSV_FILE_PATH

# Constants
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'sandbox_output')
CSV_FILE = "users_analytics.csv"
CONTAINER_OUTPUT_DIR = "/app/output"  # Directory inside Docker container
CONTAINER_CSV_PATH = "/app/data.csv"  # Path where CSV is mounted in container

def ensure_output_dir():
    """Ensure the output directory exists and is empty."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)  # Clear existing output
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def validate_csv_file(csv_path):
    """Validate that the CSV file exists and is readable."""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    try:
        import pandas as pd
        pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def save_container_outputs():
    """Check if any files were generated in the container output directory."""
    if os.path.exists(OUTPUT_DIR):
        files = os.listdir(OUTPUT_DIR)
        if files:
            print(f"\nFiles saved to {OUTPUT_DIR}:")
            for file in files:
                print(f"- {file}")
        else:
            print(f"\nNo files were generated in {OUTPUT_DIR}")

user_query = """
You are a senior digital-analytics consultant.  
You think in hypotheses, back them with reproducible code, and separate facts from speculation.  
Stay neutral; surface multiple interpretations of the data and flag uncertainty levels.

Context  
An event-level CSV ("users_analytics.csv") logs user behaviour for a website funnel:
landing_page → signup_start → signup_complete → onboarding_start → onboarding_complete → purchase  
Key columns: timestamp, session_id, user_id, event, traffic_source, device_type, country, browser, experiment_variant, is_new_user.

Objectives  
1. Funnel health  
   • Compute overall conversion and step-by-step drop-offs (session-based).  
   • Visualise as a funnel chart and a table of absolute counts & % rates.  
2. Segment stress-test  
   • Re-run the funnel split by  
     – traffic_source  
     – device_type  
     – experiment_variant  
   • Highlight the 2–3 worst-performing slices and quantify the gap vs. overall.
   • Visualize the results.
3. Behavioural diagnostics  
   • Median time between consecutive steps; flag steps where p95 time-to-next > 24 h (possible friction).  
   • Identify sessions that drop after signup_complete but before onboarding_start; estimate loss in potential revenue.  
   • Visualize the results.
4. Executive summary & recommendations  
   • 5-bullet "So what?" summary: root causes, confidence level, impact estimate.  
   • 3 concrete, testable recommendations (e.g., improve mobile signup UX, revisit paid-traffic targeting, tweak onboarding flow).  
   • Optional: suggest KPIs and next tracking events to add.

Output format  
Section 1 – Plain-language insight bullets; cite numbers from Section 1.  
Section 2 – Recommendations table (Action | Rationale | Expected lift | Priority).  
Keep prose concise (≤ 4 lines per paragraph).
"""

def main():
    # Ensure output directory exists and is empty
    ensure_output_dir()
    
    # Set the global CSV file path for the tools to use
    csv_path = CSV_FILE
    validate_csv_file(csv_path)
    
    # Set the global variable in csv_tool module
    import csv_tool
    csv_tool.CSV_FILE_PATH = os.path.abspath(csv_path)
    print(f"Using CSV file: {csv_tool.CSV_FILE_PATH}")

    # Step 1: Use planning agent (o3) to create analysis plan
    print("\n=== Planning Phase (o3) ===")
    planning_result = Runner.run_sync(agents["planner"], user_query, max_turns=5)
    analysis_plan = planning_result.final_output
    print("\nAnalysis Plan:")
    print(analysis_plan)

    # Step 2: Use execution agent (o4-mini) to implement the plan
    print("\n=== Execution Phase (o4-mini) ===")
    execution_prompt = f"""
    Based on the following analysis plan, implement each step using Python code.
    Focus on data manipulation, statistical analysis, and visualization.
    
    IMPORTANT: The CSV file is mounted at {CONTAINER_CSV_PATH} in the container.
    Save any charts to {CONTAINER_OUTPUT_DIR} directory (this will be mounted to {OUTPUT_DIR} on the host).

    Analysis Plan:
    {analysis_plan}
    """
    execution_result = Runner.run_sync(agents["executor"], execution_prompt, max_turns=20)
    execution_output = execution_result.final_output
    print("\nExecution Results:")
    print(execution_output)

    # Step 3: Use summarization agent (o3) to synthesize results
    print("\n=== Summarization Phase (o3) ===")
    summarization_prompt = f"""
    Based on the following execution results, provide a comprehensive summary with insights and recommendations.
    Focus on key findings, patterns, and actionable recommendations.

    Execution Results:
    {execution_output}
    """
    summarization_result = Runner.run_sync(agents["summarizer"], summarization_prompt, max_turns=5)
    final_summary = summarization_result.final_output

    # Print the final summary
    print("\nFinal Summary:")
    print(final_summary)

    # Check for any generated files
    save_container_outputs()

if __name__ == "__main__":
    main()