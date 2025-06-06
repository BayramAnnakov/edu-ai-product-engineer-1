from typing import Dict
from nltk.tokenize import sent_tokenize, word_tokenize
import pandas as pd
import re
from datetime import datetime
from agents import Agent, Runner
import time


def get_article_text(file_path: str) -> str:
    """Read text from a file and return it as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""


def get_reviews_from_csv(csv_path: str, num_rows: int = 5) -> str:
    """Read reviews from a CSV file and return them as a formatted string.
    
    Args:
        csv_path: Path to the CSV file.
        num_rows: Number of rows to read (default: 5).
        
    Returns:
        A formatted string of reviews or an error message.
    """
    try:
        # Try to read the CSV with only num_rows
        df = pd.read_csv(csv_path, nrows=num_rows)
        if df.empty:
            return "No reviews found in the CSV file."

        # Check if "Text" column exists, otherwise find the first text-based column
        if "Text" in df.columns:
            review_column = "Text"
        else:
            # Select first non-numeric column as a fallback
            text_columns = df.select_dtypes(include=['object', 'string']).columns
            if not text_columns.any():
                return "No text columns found in the CSV file."
            review_column = text_columns[0]  # Pick the first available text column

        # Convert column to string and drop NaN values
        reviews = df[review_column].dropna().astype(str).tolist()

        # Remove empty or whitespace-only reviews
        valid_reviews = [review.strip() for review in reviews if review.strip()]

        if not valid_reviews:
            return "No valid reviews found in the CSV file."

        # Format the reviews with numbering
        combined_text = "\n\n".join([f"REVIEW {i+1}:\n{review}" for i, review in enumerate(valid_reviews)])

        return combined_text
    except Exception as e:
        return f"Error reading CSV file: {e}"


def save_to_markdown(content, filename="virtual_user_board_summary.md"):
    """Save content to a markdown file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Virtual User Board Discussion\n\n")
        f.write(f"*Generated on: {timestamp}*\n\n")
        f.write(content)
    
    print(f"\nDiscussion saved to {filename}")


def extract_personas(text):
    """Extract simple personas from the output of the review_summarizer_agent."""
    personas = []
    # Look for persona sections in the text - pattern: PERSONA: followed by description
    persona_sections = re.findall(r'PERSONA:\s*(.*?)(?=PERSONA:|$)', text, re.DOTALL)
    
    for section in persona_sections:
        section = section.strip()
        if not section:
            continue
            
        # Try to extract persona type and description
        parts = section.split('-', 1)
        if len(parts) >= 2:
            persona_type = parts[0].strip()
            description = parts[1].strip()
        else:
            persona_type = "Consumer"
            description = section
        
        personas.append({
            "type": persona_type,
            "description": description
        })
    
    # Limit to 3 personas
    return personas[:3]


def create_persona_agents(personas):
    """Create persona agents based on the extracted personas."""
    persona_agents = []
    
    for i, persona in enumerate(personas, 1):
        # Create a name with "Persona:" prefix for clarity
        display_name = f"Persona: {persona['type']}"
        
        agent = Agent(
            name=display_name,
            instructions=(
                f"You are a {persona['type']}. {persona['description']} "
                f"Provide honest feedback on product ideas and features based on this perspective. "
                f"In group discussions, you should stay in character, consider others' viewpoints, "
                f"and work toward constructive recommendations. "
                f"When suggesting features, limit yourself to 2-3 specific, focused ideas."
            ),
            model="gpt-4o-mini"
        )
        persona_agents.append(agent)
    
    return persona_agents


async def agent_discussion(facilitator: Agent, participants: list, context: str, rounds: list = None, output_file: str = "discussion_summary.md") -> dict:
    """
    Facilitate a structured discussion between a facilitator agent and participant agents.
    
    Args:
        facilitator: The Agent object that will lead the discussion
        participants: List of Agent objects representing discussion participants
        context: Background information or prompt for the discussion
        rounds: List of discussion topics or questions for each round
        output_file: Filename to save the discussion summary
        
    Returns:
        Dictionary containing the discussion summary and recommendations
    """
    try:
        start_time = time.time()
        print("\n=== Starting Agent Discussion ===\n")
        
        # Initialize discussion tracking
        scratchpad = f"CONTEXT: {context}\n\nDISCUSSION:\n"
        markdown_content = f"## Context\n\n{context}\n\n"
        
        # Default discussion rounds if none provided
        if not rounds:
            rounds = [
                "What challenges or pain points do you currently face that are related to this topic?",
                "What specific solutions or features would address these challenges?",
                "Which of the proposed solutions would be most valuable, and why?"
            ]
        
        # Add participants to markdown
        markdown_content += "### Participants\n\n"
        for agent in participants:
            markdown_content += f"- **{agent.name}**\n"
        markdown_content += "\n"
        
        # Introduction by facilitator
        intro_prompt = f"You're facilitating a discussion about: {context}. Please introduce the discussion "
        intro_prompt += "and explain that we'll be exploring several aspects in a structured format."
        
        result = await Runner.run(facilitator, intro_prompt)
        facilitator_intro = result.final_output
        scratchpad += f"Facilitator: {facilitator_intro}\n\n"
        markdown_content += f"### Introduction\n\n**Facilitator**: {facilitator_intro}\n\n"
        print(f"Facilitator: {facilitator_intro}\n")
        
        recommendations = {}
        
        # Process each round of questions
        for idx, question in enumerate(rounds, start=1):
            round_title = f"Round {idx}: " + (
                "Problem Exploration" if idx == 1 else 
                "Solution Proposals" if idx == 2 else 
                f"Discussion Topic {idx}"
            )
            
            print(f"----- {round_title} -----\n")
            markdown_content += f"### {round_title}\n\n"
            
            # Facilitator asks the main question
            question_prompt = f"{scratchpad}\nQuestion for Round {idx}: {question}"
            result = await Runner.run(facilitator, question_prompt)
            facilitator_question = result.final_output
            
            scratchpad += f"Facilitator (Question {idx}): {facilitator_question}\n\n"
            markdown_content += f"**Facilitator**: {facilitator_question}\n\n"
            print(f"Facilitator: {facilitator_question}\n")
            
            # Process each participant individually
            for agent in participants:
                print(f"----- {agent.name}'s Response for Round {idx} -----\n")
                
                # Ask the main question, customized by round
                agent_prompt = f"{scratchpad}\n\nAs {agent.name}, please respond to this question: {question}"
                
                result = await Runner.run(agent, agent_prompt)
                response = result.final_output
                
                scratchpad += f"{agent.name}: {response}\n\n"
                markdown_content += f"**{agent.name}**: {response}\n\n"
                print(f"{agent.name}: {response}\n")
                
                # Facilitator provides personalized follow-up for this participant
                followup_prompt = f"{scratchpad}\nReview the response from {agent.name}. Based on their specific answer, "
                followup_prompt += f"propose a personalized follow-up question to explore their perspective further. "
                followup_prompt += f"If no follow-up is needed, respond with 'None'."
                
                result = await Runner.run(facilitator, followup_prompt)
                personalized_followup = result.final_output.strip()
                
                if personalized_followup.lower() not in ["none", "no follow-up", "n/a"]:
                    scratchpad += f"Facilitator (to {agent.name}): {personalized_followup}\n\n"
                    markdown_content += f"**Facilitator (to {agent.name})**: {personalized_followup}\n\n"
                    print(f"Facilitator (to {agent.name}): {personalized_followup}\n")
                    
                    # Get the participant's response to the follow-up
                    followup_response_prompt = f"{scratchpad}\nAs {agent.name}, please respond to this follow-up question: {personalized_followup}"
                    result = await Runner.run(agent, followup_response_prompt)
                    followup_response = result.final_output
                    
                    scratchpad += f"{agent.name} (follow-up): {followup_response}\n\n"
                    markdown_content += f"**{agent.name} (follow-up)**: {followup_response}\n\n"
                    print(f"{agent.name} (follow-up): {followup_response}\n")
            
            # Facilitator summarizes this round before moving to the next
            if idx < len(rounds):
                summary_prompt = f"{scratchpad}\nPlease summarize the key points from this round of discussion, "
                summary_prompt += f"highlighting common themes and interesting insights. Then, transition to the next round's focus."
                
                result = await Runner.run(facilitator, summary_prompt)
                round_summary = result.final_output
                
                scratchpad += f"Facilitator (Round {idx} Summary): {round_summary}\n\n"
                markdown_content += f"**Facilitator Summary**: {round_summary}\n\n"
                print(f"Facilitator (Round {idx} Summary): {round_summary}\n")
        
        # Final recommendations
        final_prompt = f"{scratchpad}\n\nBased on the entire discussion, please provide a final summary of the top 3 recommended features "
        final_prompt +="for market testing, ranked by priority. For each feature: 1) Provide a clear name and description, 2) Explain how it addresses "
        final_prompt +="specific problems identified in Round 1, 3) Incorporate the refinements and feedback from the discussion, and "
        final_prompt +="4) Include a brief justification for its priority."

        result = await Runner.run(facilitator, final_prompt)
        final_recommendations = result.final_output
        scratchpad += f"Facilitator (Final Recommendations): {final_recommendations}\n\n"
        
        print("\n----- RECOMMENDATIONS -----\n")
        print(final_recommendations)
        
        # Add recommendations to markdown
        markdown_content += f"## Recommendations\n\n{final_recommendations}\n"
        
        # Calculate and display total discussion time
        end_time = time.time()
        total_time = end_time - start_time
        timing_message = f"\nDiscussion time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)"
        print(timing_message)
        
        # Add timing information to markdown
        timing_info = f"\n## Performance Metrics\n\n{timing_message}\n"
        markdown_content += timing_info
        
        # Save discussion to markdown file
        save_to_markdown(markdown_content, output_file)
        
        return {
            "recommendations": final_recommendations,
            "full_discussion": markdown_content,
            "processing_time": total_time
        }
    except Exception as e:
        print(f"Error in agent discussion: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "recommendations": "Error occurred during discussion"
        }