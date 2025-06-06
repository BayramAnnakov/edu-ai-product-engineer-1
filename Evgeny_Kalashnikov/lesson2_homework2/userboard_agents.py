from agents import Agent, Runner
from pydantic import BaseModel
import asyncio

class IssueSolution(BaseModel):
    issue: str
    solution: str

class ReviewAnalysis(BaseModel):
    summary: str
    top_issues: list[str]
    solutions: list[IssueSolution]

class ReviewAnalyzer:
    def __init__(self):
        self.agent = Agent(
            name="Review Analyzer",
            instructions="""You are an expert at analyzing product reviews and identifying key issues.
            Your task is to:
            1. Read through all the provided reviews
            2. Identify and describe the product based on the reviews (what it is, its main features, typical use cases)
            3. Analyze the overall product sentiment and customer satisfaction
            4. List the top 3 most frequently mentioned issues or concerns
            
            Format your response as a structured analysis with:
            - A comprehensive summary paragraph that includes:
              * Brief product description based on reviews
              * Main features and typical use cases
              * Overall sentiment and satisfaction level
              * Key strengths and weaknesses
            - A numbered list of the top 3 issues
            
            Focus on concrete issues that can be addressed, not general sentiments.
            Use specific examples from the reviews when possible.""",
            output_type=ReviewAnalysis
        )
    
    async def analyze_reviews(self, reviews: str) -> ReviewAnalysis:
        """
        Analyze product reviews and return a structured analysis.
        
        Args:
            reviews (str): The reviews to analyze
            
        Returns:
            ReviewAnalysis: Structured analysis containing summary and top issues
        """
        prompt = f"""Please analyze these product reviews and provide your expert insights.
        Focus on understanding what the product is, how it's used, and what customers think about it.

{reviews}

Please provide a comprehensive analysis that helps understand both the product and customer sentiment.
Focus on identifying concrete issues that can be addressed and provide actionable insights."""
        
        result = await Runner.run(self.agent, prompt)
        return result.final_output

class SolutionAnalyzer:
    def __init__(self):
        self.agent = Agent(
            name="Solution Analyzer",
            instructions="""You are an expert at providing concise, actionable solutions to product issues.
            Your task is to:
            1. Understand the product and its context from the provided summary
            2. Analyze the specific issue that needs to be addressed
            3. Propose a single, most effective solution that is:
               * Practical and implementable
               * Cost-effective
               * Addresses the core issue
               * Provides sustainable improvement
            
            Guidelines:
            - Keep the solution brief and to the point
            - Focus on one clear, actionable solution
            - No need to explain why or provide alternatives
            - Solution should be 1-2 sentences maximum""",
            output_type=str
        )
    
    async def propose_solution(self, product_summary: str, issue: str) -> str:
        """
        Propose a concise solution for a specific product issue.
        
        Args:
            product_summary (str): Summary of the product and its context
            issue (str): The specific issue to address
            
        Returns:
            str: A concise, actionable solution
        """
        prompt = f"""Based on the following product summary and issue, provide a single, concise solution:

Product Summary:
{product_summary}

Issue to Address:
{issue}

Provide one clear, actionable solution in 1-2 sentences. Focus on what to do, not why."""
        
        result = await Runner.run(self.agent, prompt)
        return result.final_output

class UserPersonaAnalyzer:
    def __init__(self):
        self.agent = Agent(
            name="User Persona Psychologist",
            instructions="""You are a professional psychologist specializing in consumer behavior and user persona analysis.
            Your task is to create a concise profile of the user.
            
            Analyze the user's reviews to identify only what is explicitly shown in their reviews:
            1. Review Style:
               * How they write reviews (length, detail level)
               * Common phrases they use
               * How they express satisfaction/dissatisfaction
            
            2. Focus Areas:
               * What aspects of products they consistently mention
               * What they care about most in products
            
            3. Decision Factors:
               * What makes them recommend or not recommend products
               * Their deal-breakers based on their reviews
            
            Create a brief prompt that includes only what is directly observable from their reviews.
            Do not make assumptions or include information not present in the reviews.
            Keep the prompt focused and actionable.""",
            output_type=str
        )
    
    async def analyze_user_persona(self, reviews: str) -> str:
        """
        Analyze user reviews to create a concise prompt for user agent creation.
        
        Args:
            reviews (str): User reviews to analyze
            
        Returns:
            str: A brief prompt for configuring a user agent
        """
        prompt = f"""Analyze these user reviews to create a brief profile of the user:

{reviews}

Create a concise profile that only includes what is directly observable from their reviews.
Focus on their review style, what they consistently mention, and their decision factors.
Do not include any assumptions or information not present in the reviews.
Do not include headers or other text that is not part of the profile."""
        
        result = await Runner.run(self.agent, prompt)
        return result.final_output

class User:
    def __init__(self, user_name: str, user_profile: str):
        """
        Initialize a user agent based on their name and profile.
        
        Args:
            user_name (str): Name of the user
            user_profile (str): Profile description of the user based on their reviews
        """
        self.agent = Agent(
            name=user_name,
            instructions=f"""You are a user who has previously left reviews for one or more products. You have agreed to participate in a user board meeting to discuss product features and issues.
Ask questions about the product when you have genuine curiosity or feedback.
Comment on other participants' answers when you have something meaningful to add.
Stay silent if you have nothing to contribute.
This is how you have been described:
{user_profile}
Act naturally and authentically, using your profile to inform your questions and comments. Only participate when you have something relevant to say.""",
            output_type=str
        )
    
    async def respond(self, context: str) -> str:
        """
        Generate a response based on the given context.
        
        Args:
            context (str): The current discussion context or question
            
        Returns:
            str: The user's response or empty string if they have nothing to contribute
        """
        prompt = f"""You have been asked to respond to the following:
        {context}
        Answer in the first person, using your profile to inform your response. """
        
        result = await Runner.run(self.agent, prompt)
        return result.final_output

    async def react(self, question: str, other_user_response: str) -> str | None:
        """
        React to another user's response in a group discussion.
        
        Args:
            question (str): The original question being discussed
            other_user_response (str): Another user's response to react to
            
        Returns:
            str | None: A comment on the other user's response, or None if there's nothing meaningful to add
        """
        prompt = f"""You are in a userboard meeting. Everyone is asked the same question. 
        You have option to react to another participant's response.
        Only react when you are absolutely sure that you have something meaningful to add in context of the other user's response.
        If you don't have anything meaningful to add, just stay silent, return None.
        The question is:
        {question}

        Another participant responded:
        {other_user_response}

        Only comment if you have something meaningful to add specifically in context of the other user's response.
        
        Your comment should be brief and directly related to what was said.
        If you have nothing new to add, return None.
        If you what you want to say is related to the question without mentioning the other user's response, just return None.
        If you have a follow-up question, ask it directly.
        
        Remember: Only respond if you have something truly valuable to add to the discussion."""
        
        result = await Runner.run(self.agent, prompt)
        response = result.final_output.strip()
        
        # Return None if the response is empty or just "None"
        if not response or response.lower() == "none":
            return None
            
        return response

# Create default instances for convenience
review_analyzer = ReviewAnalyzer()
solution_analyzer = SolutionAnalyzer()
user_persona_analyzer = UserPersonaAnalyzer() 