from dotenv import load_dotenv

load_dotenv()

import asyncio
import random
from agents import Agent, Runner

# Define the product idea and hypotheses.
product_idea = """
Schengen 90/180 Calculator App:
- Product Idea: A mobile app to automatically track Schengen visa days,
  including support for multiple passports and maintaining historical data.
- Hypotheses to test:
    1. Users struggle with manually tracking Schengen days.
    2. Users are willing to pay for an enhanced, automated tracking solution.
"""

# Facilitator questions taken from the transcript.
facilitator_questions = [
    "What are your initial thoughts on the idea of a Schengen 90/180 Calculator App?",
    "How do you currently handle the tracking of your Schengen days?",
    "What features would you find most valuable in an automated solution? For example, support for multiple passports or historical data?",
    "Would you be willing to pay for a premium version that offers these advanced tracking features? Why or why not?"
]

# Create the facilitator agent.
facilitator_agent = Agent(
    name="Facilitator",
    instructions=(
        "You are a facilitator leading a virtual board meeting to validate a new product idea. "
        "Your role is to introduce the product idea, ask the provided questions, and then review each individual customer response. "
        "Based on each response, propose a personalized follow-up question if needed, or reply 'None' if no follow-up is warranted."
    ),
)

# Create customer persona agents.
julia = Agent(
    name="Julia",
    instructions=(
        "You are a 29-year-old freelance designer who frequently travels between Spain and Germany. "
        "Manual tracking of your Schengen days is challenging and frustrating. Provide candid, creative feedback."
    )
)

raj = Agent(
    name="Raj",
    instructions=(
        "You are a 35-year-old software developer and digital nomad based mostly in Lisbon. "
        "You value automation to reduce repetitive tasks. Offer detailed and thoughtful insights."
    )
)

chloe = Agent(
    name="Chloe",
    instructions=(
        "You are a 27-year-old content creator who travels extensively across EU countries. "
        "Manual tracking of travel days is tedious for you. Share honest opinions and suggest features that would delight you."
    )
)

# List of customer agents.
customer_agents = [julia, raj, chloe]

# Global conversation log.
entire_conversation = []

async def main():
    global entire_conversation

    # Facilitator introduces the product idea.
    facilitator_intro = f"Introducing product idea:\n{product_idea}\nLet's begin our discussion."
    fac_intro_result = await Runner.run(facilitator_agent, facilitator_intro)
    intro_text = f"Facilitator Intro: {fac_intro_result.final_output}\n"
    print(intro_text)
    entire_conversation.append(intro_text)
    
    # For each main facilitator question, process individual responses, personalized follow-ups, and a discussion phase.
    for idx, question in enumerate(facilitator_questions, start=1):
        round_header = f"===== Round {idx}: Main Question =====\n"
        print(round_header)
        entire_conversation.append(round_header)
        
        # Facilitator asks the main question.
        fac_question_prompt = f"Question {idx}: {question}"
        fac_question_result = await Runner.run(facilitator_agent, fac_question_prompt)
        facilitator_question_text = f"Facilitator asks: {fac_question_result.final_output}\n"
        print(facilitator_question_text)
        entire_conversation.append(facilitator_question_text)
        
        # List to record all responses in this round.
        conversation_round = []
        
        # Process each customer agent individually.
        for agent in customer_agents:
            agent_header = f"----- {agent.name}'s Response for Question {idx} -----\n"
            print(agent_header)
            entire_conversation.append(agent_header)
            
            # Customer answers the main question.
            main_prompt = (
                f"{product_idea}\n"
                f"Question: {question}\n"
                f"As {agent.name}, please share your thoughts."
            )
            main_result = await Runner.run(agent, main_prompt)
            customer_answer = main_result.final_output.strip()
            answer_text = f"{agent.name} (initial): {customer_answer}\n"
            conversation_round.append(answer_text)
            print(answer_text)
            
            # Facilitator reviews this individual response and proposes a personalized follow-up.
            facilitator_followup_prompt = (
                f"Review the following response from {agent.name} for the question:\n'{question}'\n"
                f"Customer response: '{customer_answer}'\n"
                "Based on this, propose a personalized follow-up question to further explore their perspective. "
                "If no follow-up is needed, simply answer with 'None'."
            )
            followup_result = await Runner.run(facilitator_agent, facilitator_followup_prompt)
            personalized_followup = followup_result.final_output.strip()
            followup_analysis_text = f"Facilitator's suggested follow-up for {agent.name}: {personalized_followup}\n"
            print(followup_analysis_text)
            entire_conversation.append(followup_analysis_text)
            
            # If follow-up is proposed (not 'None'), ask it.
            if personalized_followup.lower() not in ["none", "no follow-up", "n/a"]:
                followup_prompt = (
                    f"{product_idea}\n"
                    f"Follow-Up Question for {agent.name}: {personalized_followup}\n"
                    f"As {agent.name}, please elaborate further."
                )
                followup_agent_result = await Runner.run(agent, followup_prompt)
                followup_answer = followup_agent_result.final_output.strip()
                followup_text = f"{agent.name} (follow-up): {followup_answer}\n"
                conversation_round.append(followup_text)
                print(followup_text)
        
        # Discussion phase: allow agents to randomly chime in on the group discussion.
        discussion_header = f"===== Discussion Phase for Round {idx} =====\n"
        print(discussion_header)
        entire_conversation.append(discussion_header)
        
        # Construct the shared conversation context from the collected responses.
        shared_context = "\n".join(conversation_round)
        shared_context_text = f"Shared Conversation Context:\n{shared_context}\n"
        print(shared_context_text)
        entire_conversation.append(shared_context_text)
        
        # For each customer agent, use a random chance to decide if they chime in.
        for agent in customer_agents:
            # 50% chance for an agent to chime in.
            if random.random() < 0.5:
                discussion_prompt = (
                    f"{product_idea}\n"
                    f"Question: {question}\n"
                    f"Conversation so far:\n{shared_context}\n"
                    f"As {agent.name}, please add any thoughts or comments that build on what others said. "
                    "If you have nothing to add, you can simply say 'No additional comment.'"
                )
                discussion_result = await Runner.run(agent, discussion_prompt)
                discussion_response = discussion_result.final_output.strip()
                if discussion_response.lower() not in ["no additional comment", "none", "n/a"]:
                    discussion_text = f"{agent.name} (discussion): {discussion_response}\n"
                    conversation_round.append(discussion_text)
                    print(discussion_text)
        
        # Append the current round's conversation to the entire conversation log.
        entire_conversation.append("\n".join(conversation_round) + "\n")
        print("-------------------------------------------------\n")
        entire_conversation.append("-------------------------------------------------\n")
    
    # Final overall summary by the facilitator.
    summary_prompt = (
        "Based on the entire discussion, please summarize the key takeaways regarding the need for an "
        "automated Schengen days tracking app and the importance of features like multiple passport support and historical data management."
    )
    fac_summary_result = await Runner.run(facilitator_agent, summary_prompt)
    summary_text = f"Facilitator Summary: {fac_summary_result.final_output}\n"
    print(summary_text)
    entire_conversation.append(summary_text)
    
    # Write the complete conversation to a text file.
    conversation_log = "\n".join(entire_conversation)
    with open("conversation.txt", "w", encoding="utf-8") as f:
        f.write(conversation_log)
    print("The full conversation has been saved to 'conversation.txt'.")

if __name__ == "__main__":
    asyncio.run(main())
