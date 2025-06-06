"""
Board Simulation Module

This module contains the core functionality for simulating a virtual board meeting
with multiple personas discussing feature proposals.
"""

from collections import defaultdict
import logging
import random
from typing import List, Sequence, Tuple

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pathlib import Path
from dotenv import load_dotenv

from data_types import Persona, FeatureProposal

from agents import Agent, Runner, ModelSettings

# --- Determine Project Root and Load Env ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR

env_path = PROJECT_ROOT / ".env"
if not env_path.exists():
    print(f"Warning: .env file not found at {env_path}. Ensure OPENAI_API_KEY is set via environment variables.")
load_dotenv(dotenv_path=env_path)

# Configure LLM
FacilitatorLLM = ChatOpenAI(model="gpt-4.1", temperature=0.2)

# Configure interview questions
core_questions = [
        "What are your initial thoughts on the features?",
        "What are the pros and cons of each feature?",
        "What's the one feature Spotify should ship next quarter & why?"
    ]

max_followups = 1

logger = logging.getLogger(__name__)

def get_random_llm() -> ChatOpenAI:
    """Returns a randomly configured ChatOpenAI instance with random model and temperature."""
    models = ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"]
    temperature = random.uniform(0.3, 1.0)
    model = random.choice(models)
    
    return ChatOpenAI(
        model=model,
        temperature=temperature
    )

def generate_persona_agents(
    personas: Sequence[Persona]
) -> Sequence[Agent]:
    """For each persona, generate an agent that can simulate a conversation with the facilitator with system prompt based on persona's profile"""
    agents = []

    system_prompt = """
You are {persona_name}. Act and respond authentically based on this profile:
- Background: {persona_background}
- Overall Sentiment towards Spotify: {persona_sentiment}
- Key Pain Points/Frustrations: {persona_pain_points}

You are taking part in a **panel interview** together with other Spotify users.

For every question you receive:
1. Provide your answer.
2. If something another panelist said is relevant, explicitly mention their
   name and briefly react.
3. Explain *why* you think that — give a snippet of personal context.

Important rules:
- Never mention or reference other people unless you've actually seen their responses
- If no other responses are shown to you, focus only on your own perspective
- Keep your total response ≤120 words
- Don't repeat yourself, use different openers and act naturally.
"""

    for persona in personas:
        llm = get_random_llm()
        agent = Agent(
            name=persona.name,
            model=llm.model_name,
            model_settings=ModelSettings(temperature=llm.temperature),
            tools=[],
            instructions=system_prompt.format(
                persona_name=persona.name,
                persona_background=persona.background,
                persona_sentiment=persona.sentiment,
                persona_pain_points="; ".join(persona.pain_points)
            )
        )
        agents.append(agent)

    return agents

async def simulate_userboard(
    personas: Sequence[Persona],
    features: Sequence[FeatureProposal],
    rounds: int = 3
) -> Tuple[str, List[BaseMessage]]:
    """Run a board simulation with the given agents and features."""
    if not personas or not features:
        logger.warning("Missing personas (%d) or features (%d)", len(personas), len(features))
        return "", []

    logger.info("Initializing Agents for %d personas...", len(personas))
    agents = generate_persona_agents(personas)

    # Create facilitator agent
    facilitator_agent = Agent(
        name="Facilitator",
        instructions="""
You are a professional facilitator running a discussion about Spotify features.
Your role is to:
1. Ask clear, focused questions about the features
2. Keep the discussion on track
3. Ensure each participant gets a chance to speak
4. Summarize key points when needed
5. Ask follow-up questions when responses are interesting or unclear

Keep your questions and summaries concise and professional.
When asking follow-ups, reference specific points from the participant's response.
Don't repeat yourself, use different openers and act naturally.

Important:
- Start with a friendly greeting
- Address the group naturally (e.g., "everyone", "folks", "team")
- Avoid formal terms like "panelists" or "thank you" at the start
- Keep the tone conversational but professional
""",
        model="gpt-4.1"
    )

    # Initialize transcript and history
    transcript: List[str] = []
    global_history: List[BaseMessage] = []

    # Feature list for context
    feature_list_md = "\n".join(f"{i+1}. {f.description}" for i, f in enumerate(features))

    # Run the interview rounds
    for round_num in range(rounds):
        logger.info("Starting round %d", round_num + 1)
        
        # Get the core question for this round
        question = core_questions[round_num]
        
        # Facilitator asks the question
        fac_prompt = f"""
We are discussing these features:
{feature_list_md}

Please ask the following question to the panel:
{question}
"""
        fac_response = await Runner.run(facilitator_agent, fac_prompt)
        transcript.append(f"\n### 🎤 Facilitator – Round {round_num + 1}")
        transcript.append(fac_response.final_output)
        global_history.append(HumanMessage(content=fac_response.final_output))

        # Each persona responds
        for agent in agents:
            # Include previous responses for context
            context = "\n".join(transcript[-2:])  # Last facilitator question and previous response
            agent_prompt = f"""
{context}

As {agent.name}, please respond to the facilitator's question.
"""
            agent_response = await Runner.run(agent, agent_prompt)
            transcript.append(f"\n#### 👤 {agent.name}")
            transcript.append(agent_response.final_output)
            global_history.append(AIMessage(content=agent_response.final_output))

            # Facilitator may ask follow-up questions
            followup_count = 0
            while followup_count < max_followups:
                followup_prompt = f"""
Previous discussion:
{context}
{agent.name}'s response: {agent_response.final_output}

Based on {agent.name}'s response, ask ONE relevant follow-up question.
Only ask if you think it would add value to the discussion.
"""
                followup_response = await Runner.run(facilitator_agent, followup_prompt)
                if "no follow-up" in followup_response.final_output.lower():
                    break

                transcript.append(f"\n### 🎤 Facilitator – Follow-up")
                transcript.append(followup_response.final_output)
                global_history.append(HumanMessage(content=followup_response.final_output))

                # Get agent's response to follow-up
                followup_context = "\n".join(transcript[-2:])
                agent_followup_prompt = f"""
{followup_context}

As {agent.name}, please respond to the facilitator's follow-up question.
"""
                agent_followup_response = await Runner.run(agent, agent_followup_prompt)
                transcript.append(f"\n#### 👤 {agent.name}")
                transcript.append(agent_followup_response.final_output)
                global_history.append(AIMessage(content=agent_followup_response.final_output))

                followup_count += 1

    final_transcript_md = "\n".join(transcript)
    logger.info("Board simulation completed – %d messages in global history", len(global_history))

    return final_transcript_md, global_history 




    




