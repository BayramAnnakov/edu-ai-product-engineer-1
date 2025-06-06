from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServer, MCPServerStdio



@function_tool
def get_product_reviews(product_name: str) -> list[str]:
    """
    This function returns a list of reviews for a given product.
    """
    return ["Review 1", "Review 2", "Review 3"]


product_reviews_agent = Agent(
    name = "Product Reviews Agent",
    instructions = """
    You are an expert product reviewer.
    Your task is to review the customer reviews and provide insights about the product.
    """,
    tools = [get_product_reviews]
)

product_reviews_agent.as_tool(
    tool_name = "get_product_reviews",
    description = "Get the reviews for a given product"
)









