from dotenv import load_dotenv

load_dotenv()

import asyncio
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
        "Your role is to introduce the product idea, ask the provided questions, and then review individual customer responses. "
        "Based on each response, propose a personalized follow-up question to delve deeper into that customer's perspective, "
        "or reply 'None' if no follow-up is needed."
    )
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

async def main():
    print("=== Virtual User Board Simulation ===\n")
    
    # Initialize the scratchpad for context sharing between agents
    scratchpad = f"PRODUCT IDEA:\n{product_idea}\n\nDISCUSSION:\n"
    
    # Facilitator introduces the product idea.
    facilitator_intro = f"{scratchpad}\nIntroducing product idea:\n{product_idea}\nLet's begin our discussion."
    fac_intro_result = await Runner.run(facilitator_agent, facilitator_intro)
    intro_output = fac_intro_result.final_output
    
    # Update scratchpad with facilitator's introduction
    scratchpad += f"Facilitator: {intro_output}\n\n"
    print("Facilitator Intro:", intro_output, "\n")
    
    # Process each main facilitator question.
    for idx, question in enumerate(facilitator_questions, start=1):
        print(f"===== Round {idx}: Main Question =====\n")
        # Facilitator asks the main question.
        fac_question_prompt = f"{scratchpad}\nQuestion {idx}: {question}"
        fac_question_result = await Runner.run(facilitator_agent, fac_question_prompt)
        question_output = fac_question_result.final_output
        
        # Update scratchpad with facilitator's question
        scratchpad += f"Facilitator (Question {idx}): {question_output}\n\n"
        print("Facilitator asks:", question_output, "\n")
        
        # Process each customer agent individually.
        for agent in customer_agents:
            print(f"----- {agent.name}'s Response for Question {idx} -----\n")
            # Ask the main question to the customer agent.
            main_prompt = (
                f"{scratchpad}\n"
                f"Question: {question}\n"
                f"As {agent.name}, please share your thoughts."
            )
            main_result = await Runner.run(agent, main_prompt)
            customer_answer = main_result.final_output
            
            # Update scratchpad with customer's answer
            scratchpad += f"{agent.name}: {customer_answer}\n\n"
            print(f"{agent.name}:", customer_answer, "\n")
            
            # Facilitator reviews this particular customer's answer and proposes a personalized follow-up.
            facilitator_followup_prompt = (
                f"{scratchpad}\n"
                f"Review the following response from {agent.name} for the question:\n'{question}'\n"
                f"Customer response: '{customer_answer}'\n"
                "Based on this, propose a personalized follow-up question to further explore their perspective. "
                "If no follow-up is needed, simply answer with 'None'."
            )
            followup_result = await Runner.run(facilitator_agent, facilitator_followup_prompt)
            personalized_followup = followup_result.final_output.strip()
            
            # Update scratchpad with facilitator's follow-up
            scratchpad += f"Facilitator (Follow-up for {agent.name}): {personalized_followup}\n\n"
            print(f"Facilitator's suggested follow-up for {agent.name}:", personalized_followup, "\n")
            
            # If the facilitator suggests a follow-up (i.e. the response is not "None"), ask it to that specific agent.
            if personalized_followup.lower() not in ["none", "no follow-up", "n/a"]:
                followup_prompt = (
                    f"{scratchpad}\n"
                    f"Follow-Up Question for {agent.name}: {personalized_followup}\n"
                    f"As {agent.name}, please elaborate further."
                )
                followup_agent_result = await Runner.run(agent, followup_prompt)
                followup_answer = followup_agent_result.final_output
                
                # Update scratchpad with follow-up answer
                scratchpad += f"{agent.name} (follow-up): {followup_answer}\n\n"
                print(f"{agent.name} (follow-up):", followup_answer, "\n")
        
        print("-------------------------------------------------\n")
    
    # Finally, the facilitator summarizes the overall discussion.
    summary_prompt = (
        f"{scratchpad}\n"
        "Based on the entire discussion above, please summarize the key takeaways regarding the need for an "
        "automated Schengen days tracking app and the value of features such as multiple passport support and historical data management."
    )
    fac_summary_result = await Runner.run(facilitator_agent, summary_prompt)
    summary_output = fac_summary_result.final_output
    
    # Update scratchpad with final summary
    scratchpad += f"Facilitator (Final Summary): {summary_output}\n\n"
    print("Facilitator Summary:", summary_output)

if __name__ == "__main__":
    asyncio.run(main())
