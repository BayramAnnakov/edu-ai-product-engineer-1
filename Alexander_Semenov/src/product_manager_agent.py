"""
Module for Product Manager agent that analyzes reviews and generates feature suggestions.
"""

import asyncio
from agents import Agent, Runner
from typing import List
from src.logger_config import setup_logger
from src.llm_client import call_openai_api

class ProductManagerAgent:
    """
    Agent that acts as a senior product manager to analyze reviews and suggest features.
    """
    
    def __init__(self):
        self.agent = Agent(
            name="SeniorProductManagerAgent",
            instructions="""
            You are a senior product manager with extensive experience working on digital products.
            Your primary tasks are to analyze user reviews and feedback, identify key problems and user pain points, formulate specific product tasks and features to address these issues, and build a target user profile based on the reviews.
            You are also responsible for conducting user research when necessary.
            Respond clearly and professionally.
            """,
            model="gpt-4",
        )
    
    def _parse_response(self, response: str, parse_type: str = "feature") -> List[str]:
        """
        Parse LLM response into a list based on type.
        
        Args:
            response (str): Raw LLM response text
            parse_type (str): Type of parsing to perform ("feature" or "persona")
            
        Returns:
            List[str]: List of parsed items (features or personas)
        """
        if not response:
            return []
            
        items = []
        # Split response by '---' delimiter and remove empty blocks
        blocks = [block.strip() for block in response.split('---') if block.strip()]
        
        for block in blocks:
            try:
                if parse_type == "feature":
                    # Find feature name and description using the prefixes
                    name_start = block.find("Feature Name:")
                    desc_start = block.find("Description:")
                    
                    if name_start != -1 and desc_start != -1:
                        # Extract name (text between "Feature Name:" and "Description:")
                        name = block[name_start + len("Feature Name:"):desc_start].strip()
                        # Extract description (text after "Description:")
                        description = block[desc_start + len("Description:"):].strip()
                        # Format the feature string
                        item = f"Feature Name: {name}\nDescription: {description}"
                        items.append(item)
                        
                elif parse_type == "persona":
                    # Find persona description
                    persona_start = block.find("Persona:")
                    
                    if persona_start != -1:
                        # Extract persona description (text after "Persona:")
                        description = block[persona_start + len("Persona:"):].strip()
                        if description:
                            items.append(f"Persona: {description}")
                            
            except Exception as e:
                logger = setup_logger(__name__)
                logger.warning(f"Error parsing {parse_type} block: {str(e)}")
                continue
        
        return items
        
    async def identify_key_user_pain_points(self, reviews: List[str]) -> List[str]:
        """
        Analyze user reviews to identify key pain points and problems.
        
        Args:
            reviews (List[str]): List of user reviews to analyze
            
        Returns:
            List[str]: List of identified features, where each feature includes its name and description
        """
        logger = setup_logger(__name__)
        
        prompt = """
You are a Senior Product Manager with extensive experience in digital products.
I'm going to share a set of user reviews with you.
Your task is to deeply analyze the feedback and identify the key user pain points.

Here's how you should approach it:
1. Carefully read all the reviews. Pay attention not only to explicit complaints but also to subtle signs of frustration, unmet needs, or unspoken expectations.
2. Group similar feedback together. If multiple reviews touch on the same issue (e.g., "slow loading" and "freezes on startup"), treat them as one common problem.
3. Based on these insights, define 3 new product features. Focus on the issues that are the most critical or most frequently mentioned.

Feature writing guidelines:
One feature = one paragraph.
* Each paragraph should be clear, cohesive, and no longer than 7 sentences.
* The description must explain which user problem it addresses, how the feature works, and what benefit it brings to users.
* Avoid vague statements or generalities — be specific, professional, and actionable.
* Focus on features that would directly solve the identified problems and could realistically be implemented.
* Write in a clear, logical, and structured way. Avoid phrases like "users are unhappy" — instead, clearly define problems in a way that can immediately guide solution design.
* The output must contain only the list of features in the specified format — no additional summaries, explanations, or conclusions.

Response format:

Feature Name: [Feature Name]
Description: [Feature description in one paragraph]
---
Feature Name: [Feature Name]
Description: [Feature description in one paragraph]
---
Feature Name: [Feature Name]
Description: [Feature description in one paragraph]

---
Reviews to analyze:
{reviews_text}
        """.format(reviews_text="\n\n".join(reviews))

        result = await Runner.run(self.agent, prompt)
        return self._parse_response(result.final_output, parse_type="feature")
    
    async def identify_user_personas(self, reviews: List[str]) -> List[str]:
        """
        Analyze user reviews to identify unique user personas.
        
        Args:
            reviews (List[str]): List of user reviews to analyze
            
        Returns:
            List[str]: List of identified user personas
        """
        logger = setup_logger(__name__)
        
        prompt = """
You are a user research and persona creation expert. Based on a set of user reviews, your task is to identify 3–5 unique personas.

Each persona description must:
- Be concise (1–2 sentences).
- Be vivid, specific, and clearly convey who the person is, the context in which they use the product, their goals, and the challenges they face.

Follow the style of these examples:
- A social media influencer using their platform to share news and resources on Amazon deforestation.
- A retired professional athlete who believes in the captain's abilities and encourages her to aim for greatness.
- An electrical engineering graduate student conducting research on using machine learning algorithms for audio recognition.

Instructions:
1. Carefully read the user reviews.
2. Identify recurring patterns in user profiles, usage scenarios, motivations, pain points, and behaviors.
3. For each pattern, create a short, vivid persona description in 1–2 sentences.
4. Avoid generic or vague descriptions (e.g., "a user who likes apps" — unacceptable).
5. Output only the list of personas, without additional explanations or commentary.

Response format:
Persona: [1-2 sentence description]
---
Persona: [1-2 sentence description]
---
Persona: [1-2 sentence description]
---
Persona: [1-2 sentence description]
---
Persona: [1-2 sentence description]

---
Input (user reviews):
{reviews_text}
        """.format(reviews_text="\n\n".join(reviews))

        result = await Runner.run(self.agent, prompt)
        return self._parse_response(result.final_output, parse_type="persona")