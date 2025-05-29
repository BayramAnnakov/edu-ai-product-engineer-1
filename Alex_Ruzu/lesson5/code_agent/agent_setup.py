# agent_setup.py
from dotenv import load_dotenv
load_dotenv()
import os
from agents import Agent, Runner, function_tool


# Load OpenAI API key from environment (ensure OPENAI_API_KEY is set)
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("Please set the OPENAI_API_KEY environment variable")

# Import tool functions from other modules
from csv_tool import preview_csv
from docker_tool import execute_python


# Define the planning agent (o3) for high-level analysis planning
planning_agent = Agent(
    name="AnalysisPlanner",
    instructions=(
        "You are a data analysis planning AI. Your role is to break down complex analysis requests into clear, "
        "sequential steps. Focus on creating a logical flow of analysis that will answer the user's questions. "
        "Be specific about what data needs to be examined and what insights should be derived."
    ),
    model="o3",
    tools=[preview_csv]  # Only needs preview capability for planning
)

# Define the execution agent (o4-mini) for running analysis steps
execution_agent = Agent(
    name="AnalysisExecutor",
    instructions=(
        "You are a data analysis execution AI. Your role is to implement specific analysis steps using Python code. "
        "Write efficient, clean code that follows best practices. Focus on data manipulation, statistical analysis, "
        "and visualization. Use libraries like pandas, numpy, matplotlib, seaborn, plotly, tabulate, statsmodels, scipy. Always validate your results and handle errors gracefully."
    ),
    model="o3",
    tools=[preview_csv, execute_python]  # Needs both preview and execution capabilities
)

# Define the summarization agent (o3) for final insights and recommendations
summarization_agent = Agent(
    name="AnalysisSummarizer",
    instructions=(
        "You are a data analysis summarization AI. Your role is to synthesize analysis results into clear, "
        "actionable insights and recommendations. Focus on identifying patterns, trends, and opportunities for "
        "improvement. Present your findings in a structured, easy-to-understand format."
    ),
    model="gpt-4.1",
    tools=[preview_csv]  # Only needs preview capability for reference
)

# Export all agents
agents = {
    "planner": planning_agent,
    "executor": execution_agent,
    "summarizer": summarization_agent
}
