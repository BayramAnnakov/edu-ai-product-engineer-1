from agents import Agent, ModelSettings, function_tool, WebSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings
from pydantic import BaseModel
from typing import List, Dict
import openai
import json

PLAN_INSTRUCTIONS = (
    "You are a helpful research assistant. Given a query, come up with a set of web searches "
    "to perform to best answer the query. Output between 3 and 5 terms to query for."
)

class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query."

    query: str
    "The search term to use for the web search."


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""

#stronger model to plan
feature_research_planner = Agent(
    name="Feature Research Planner Agent",
    instructions=PLAN_INSTRUCTIONS,
    model="gpt-4.1",
    output_type=WebSearchPlan
)

RESEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary "
    "itself."
)

#weaker model to execute
feature_research_executer = Agent(
    name="Feature Research Executer Agent",
    instructions=RESEARCH_INSTRUCTIONS,
    model="gpt-4.1-mini",
    tools=[WebSearchTool()],
    model_settings=ModelSettings(tool_choice="required"),
)

EVAL_INSTRUCTIONS = """
    You're an evaluator agent. Your goal is to assess research plan and give a verdict if it's
    accurate, realistic and accomplishes the initial feature request and developed research plan.
"""
research_eval_agent = Agent(
    name="Research Evaluater Agent",
    instructions=EVAL_INSTRUCTIONS,
    model="gpt-4.1"
)

class ResearchEvaluation(BaseModel):
    """Model for research evaluation results"""
    is_approved: bool
    """Whether the research is approved or needs rework"""
    score: float
    """Score from 0 to 1 indicating research quality"""
    feedback: List[str]
    """List of specific feedback points"""
    improvements_needed: List[str]
    """List of specific improvements needed if research is not approved"""
    strengths: List[str]
    """List of research strengths"""

@function_tool
def evaluate_research(research: str, research_plan: str, feature_description: str) -> ResearchEvaluation:
    """Evaluates research against the original research plan and feature description using OpenAI.
    
    Args:
        research: The completed research document
        research_plan: The original research plan that was approved
        feature_description: The original feature description/requirements
        
    Returns:
        ResearchEvaluation object containing approval status, score, and detailed feedback
    """
    # Create a prompt for the evaluation
    evaluation_prompt = f"""
    You are an expert research evaluator. Please evaluate the following research against the original plan and feature description.
    
    Feature Description:
    {feature_description}
    
    Original Research Plan:
    {research_plan}
    
    Completed Research:
    {research}
    
    Please provide a detailed evaluation including:
    1. A score from 0 to 1
    2. Whether the research should be approved (score >= 0.7 and minimal improvements needed)
    3. List of specific feedback points
    4. List of improvements needed
    5. List of research strengths
    
    Respond with a JSON object in the following format:
    {{
        "is_approved": boolean,
        "score": float,
        "feedback": [string],
        "improvements_needed": [string],
        "strengths": [string]
    }}
    
    Only respond with the JSON object, no additional text.
    """
    
    try:
        # Make direct OpenAI API call
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                 {"role": "system", "content": "You are an expert research evaluator. Respond only with valid JSON."},
                {"role": "user", "content": evaluation_prompt}
            ],
            temperature=0.3 # Lower temperature for more consistent output
        )
        
        # Parse the response
        eval_data = json.loads(response.choices[0].message.content)
        
        return ResearchEvaluation(
            is_approved=eval_data["is_approved"],
            score=eval_data["score"],
            feedback=eval_data["feedback"],
            improvements_needed=eval_data["improvements_needed"],
            strengths=eval_data["strengths"]
        )
    except Exception as e:
        # If parsing fails, return a default evaluation with error feedback
        return ResearchEvaluation(
            is_approved=False,
            score=0.0,
            feedback=[f"Error in evaluation: {str(e)}"],
            improvements_needed=["Failed to parse evaluation results"],
            strengths=[]
        )

feature_handler_manager_agent = Agent(
    name="Feature Handler Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You're the feature research manager Agent that works for Spotify. Your task is to create a research plan.
        Execute it using the tools, evaluate the research with @evaluate_research tool and if it doesn't pass modify the research according to the feedback.
        After post the report using mcp to Slack channel called test""",
    model="gpt-4.1",
    handoff_description="An agent that specializes in handling features proposals",
    tools=[feature_research_planner.as_tool(tool_name="plan_research", tool_description="create a plan for a research."),
            feature_research_executer.as_tool(tool_name="execute_research_plan", tool_description="execute each step of the research."),
            evaluate_research]
)