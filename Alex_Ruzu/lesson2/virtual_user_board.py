from agents import Agent, function_tool, Runner
import asyncio
from dotenv import load_dotenv
import os
import time

from utils import get_reviews_from_csv, save_to_markdown, extract_personas, create_persona_agents, agent_discussion
from openai import OpenAI


@function_tool
def abstractive_summarizer(text: str, max_length: int) -> str:
    """
    Generate an abstractive summary of reviews using OpenAI's GPT model.
    This creates a concise version focusing on the main themes and points.
    """
    try:
        # Handle default value inside the function
        if max_length is None or max_length <= 0:
            max_length = 150
            
        start_time = time.time()

        openai = OpenAI()
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a review summarization expert that creates concise, clear summaries. "
                                    "Focus on the main themes, key points, and common sentiments across reviews."},
                {"role": "user", "content": f"Please summarize the following reviews in {max_length} words or less:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=200
        )        
        summary = response.choices[0].message.content.strip()

        processing_time = time.time() - start_time
        print(f"Abstractive Summary - Processing time: {processing_time}")

        return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"


@function_tool
def insight_generator(summary: str, num_insights: int) -> str:
    """
    Generate key insights about the product based on the review summary.
    """
    try:
        # Handle default value inside the function
        if num_insights is None or num_insights <= 0:
            num_insights = 3
            
        start_time = time.time()

        openai = OpenAI()
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a product analyst who identifies key insights from customer feedback. "
                                     "Focus on finding meaningful patterns and trends."},
                {"role": "user", "content": f"Based on this review summary, identify exactly {num_insights} key insights about the product:\n\n{summary}"}
            ],
            temperature=0.1,
            max_tokens=250
        )        
        insights = response.choices[0].message.content.strip()

        processing_time = time.time() - start_time
        print(f"Insight Generation - Processing time: {processing_time}")

        return insights
    except Exception as e:
        return f"Error generating insights: {str(e)}"


@function_tool
def persona_creator(summary: str, insights: str, num_personas: int) -> str:
    """
    Create representative user personas based on the review summary and insights.
    """
    try:
        # Handle default value inside the function
        if num_personas is None or num_personas <= 0:
            num_personas = 3
            
        start_time = time.time()

        openai = OpenAI()
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a user research expert who creates representative personas based on customer data. "
                                     "Each persona should be labeled as 'PERSONA:' followed by a descriptive name and overview."},
                {"role": "user", "content": f"Based on this review summary and insights, create exactly {num_personas} distinct user personas. "
                              f"For each persona, provide a concise name and brief description of their needs and pain points.\n\n"
                              f"Summary: {summary}\n\nInsights: {insights}"}
            ],
            temperature=0.2,
            max_tokens=350
        )        
        personas = response.choices[0].message.content.strip()

        processing_time = time.time() - start_time
        print(f"Persona Creation - Processing time: {processing_time}")

        return personas
    except Exception as e:
        return f"Error generating personas: {str(e)}"


# Main agent with tools
user_research_agent = Agent(
    name="User Research Expert",
    instructions="""You are a review summarization expert with access to specialized tools. 
    Your task is to analyze customer reviews and produce:
    
    1. A concise abstractive summary of the main themes and points in the reviews, limited to 300 words
    2. Key insights about the product based on customer feedback
    3. Representative user personas based on the review analysis
    
    You have the following tools at your disposal:
    - abstractive_summarizer: Creates a concise summary focusing on main themes in reviews
    - insight_generator: Identifies key product insights from summarized information
    - persona_creator: Develops user personas based on review data
    
    Each persona should be clearly labeled as "PERSONA:" followed by a simple description of the user type, for example:
    PERSONA: Pet Owner - Quality-conscious individuals looking for nutritious and appealing food for their finicky pets.
    PERSONA: Discerning Snack Buyer - Consumers who prioritize accurate product descriptions and labeling while shopping for snacks.
    """,
    tools=[abstractive_summarizer, insight_generator, persona_creator],
    model="gpt-4o-mini"
)

# Facilitator for the virtual user board
facilitator_agent = Agent(
    name="Facilitator",
    instructions="""You are a facilitator leading a virtual user board discussion.
    Your role is to guide the conversation, ask follow-up questions, and summarize insights.
    At the end, you need to:
    1. Synthesize the key points from the discussion
    2. Extract clear feature recommendations for market testing (limit to 3-5 top features)
    3. Rank these features by priority based on user consensus
    
    Keep your responses concise and focused on moving the discussion forward.
    
    In the first round, focus on understanding user problems, use cases, and pain points - 
    not specific feature suggestions. In later rounds, guide the discussion toward 
    concrete feature recommendations.
    """,
    model="gpt-4o-mini"
)


async def run_virtual_user_board(persona_agents, facilitator_agent, product_idea, review_summary=None):
    """Run a virtual user board with discussion and feature recommendations using the agent_discussion tool."""
    
    # Prepare context with product idea and review summary
    context = f"Product Idea: {product_idea}"
    if review_summary:
        context += f"\n\nReview Analysis: {review_summary}"
    
    # Define discussion questions
    discussion_questions = [
        "What challenges or pain points do you currently face that are related to this product?",
        "What specific features would you find most valuable in this product?",
        "Which of the proposed features do you think would solve the most critical problems, and why?"
    ]
    
    # Run the discussion using our new tool
    await agent_discussion(
        facilitator=facilitator_agent,
        participants=persona_agents,
        context=context,
        rounds=discussion_questions,
        output_file="virtual_user_board_summary.md"
    )
    
    # No return statement - function is now void


async def main():
    load_dotenv()
    
    # Path to the CSV file
    csv_path = "reviews.csv"
    
    # Check if the file exists
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        return
    
    print(f"Starting review analysis for file: {csv_path}")
    print("Note: Only the first 5 rows of the CSV file will be processed.")
    print("Note: Reviews are expected to be in the 'Text' column.")
    
    # Load reviews directly using the utility function
    text = get_reviews_from_csv(csv_path, num_rows=5)
    
    if text.startswith("Error") or text.startswith("No reviews"):
        print(f"Error: {text}")
        return
    
    try:
        # Track overall processing time
        overall_start_time = time.time()
        
        result = await Runner.run(
            user_research_agent,
            f"""Please analyze these reviews to produce:
            1. An abstractive summary of the main themes and points limited to 300 words
            2. 2-3 key insights about the product
            3. 2-3 representative user personas
            
            Reviews to analyze:
            {text}
            """
        )
        
        # Format the review summary for better readability
        formatted_summary = result.final_output
        
        # Create review summary content - without "Created Personas" section
        review_summary_md = "## Review Analysis\n\n" + formatted_summary
        
        # Extract and create persona agents
        personas = extract_personas(result.final_output)
        
        if personas:
            print(result.final_output)
            
            print(f"\nCreated {len(personas)} personas based on review analysis.")
            persona_agents = create_persona_agents(personas)
            
            # Example product idea for feedback (you can customize this)
            product_idea = """
            Based on the reviews analyzed, we're considering the following product enhancements:
            1. Improving the user interface for better usability
            2. Adding new features based on common user requests
            """
            # 3. Fixing reported bugs and issues
            
            # Run the virtual user board with discussion and recommendations
            print("\n===== STARTING VIRTUAL USER BOARD =====\n")
            # Pass just the review summary without duplicate personas
            await run_virtual_user_board(persona_agents, facilitator_agent, product_idea, review_summary_md)
            
            # Calculate and display total processing time
            overall_end_time = time.time()
            overall_total_time = overall_end_time - overall_start_time
            print(f"\n===== COMPLETE PROCESS FINISHED =====")
            print(f"Total processing time (including review analysis): {overall_total_time:.2f} seconds ({overall_total_time/60:.2f} minutes)")
            
        else:
            print("\nNo personas could be extracted from the analysis.")
            save_to_markdown(review_summary_md, "virtual_user_board_summary.md")
            
    except Exception as e:
        print(f"Error running the agent: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())