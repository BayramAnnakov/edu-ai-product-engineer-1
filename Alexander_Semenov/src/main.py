import argparse
from agents import Agent, Runner
import os
from dotenv import load_dotenv
import logging
import asyncio
from src.data_loader import load_reviews
from src.logger_config import setup_logger
from src.reviews_preparer import prepare_reviews
from src.product_manager_agent import ProductManagerAgent

async def main():
    """
    Main function that handles the review analysis and focus group simulation.
    
    This function:
    1. Processes command line arguments
    2. Validates environment variables
    3. Loads and processes the CSV file with reviews
    4. Performs review analysis using Product Manager agent
    """
    # Set up logging
    logger = setup_logger(__name__)
    logger.info("Starting pipeline...")
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Analyze product reviews and simulate focus group discussions'
    )
    parser.add_argument(
        '--csv-path', '-c',
        required=True,
        help='Path to the CSV file containing product reviews'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get CSV path from arguments
    csv_path = args.csv_path
    
    # Load environment variables
    load_dotenv()
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Check if API key exists
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        exit(1)
    
    # Load and validate reviews
    try:
        reviews_df = load_reviews(csv_path)
        logger.info(f"Successfully loaded {len(reviews_df)} reviews")
    except FileNotFoundError:
        logger.error(f"CSV file not found at path: {csv_path}")
        exit(1)
    except ValueError as e:
        logger.error(str(e))
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        exit(1)

    # Prepare formatted reviews
    reviews = ""
    try:
        reviews = prepare_reviews(reviews_df, max_reviews=10)
        logger.info("\nFormatted reviews:")
        for review in reviews:
            logger.info(f"\n{review}")
    except ValueError as e:
        logger.error(str(e))
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        exit(1)
    
    # Initialize product manager agent and analyze reviews
    product_manager = ProductManagerAgent()
    
    # Get features
    features = await product_manager.identify_key_user_pain_points(reviews)
    logger.info("\nIdentified features:")
    for idx, feature in enumerate(features, 1):
        logger.info(f"\nFeature {idx}:\n{feature}")
        
    # Get personas
    personas = await product_manager.identify_user_personas(reviews)
    logger.info("\nIdentified user personas:")
    for idx, persona in enumerate(personas, 1):
        logger.info(f"\nPersona {idx}:\n{persona}")

    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)

    dynamic_prompt = f"""
You are a senior product manager conducting a simulated user research session to test several new product features.
Multiple users with different backgrounds are participating in this session.

Participants:
{personas}

Features to discuss:
{features}

Your task:
- Act as the product manager (facilitator) and conduct the conversation around each proposed feature.
- Simulate a real-time discussion where users first react independently, then respond to each other's opinions (agreeing, disagreeing, adding new thoughts).
- The conversation should feel natural, dynamic, and collaborative, similar to a live virtual whiteboard session.

Conversation format (Virtual Board Conversation):
- Use dialogue style with names or labels for each participant.
- Include clarifying questions from the product manager between answers.
- Allow users to reference or respond directly to previous comments.
- Encourage deeper insights through follow-up questions and challenges.

After the conversation:
- Write a concise Facilitator Summary in plain text (.txt).
- The summary must include:
  - Key positive feedback.
  - Main concerns or pain points discovered.
  - Unexpected insights.
  - Opportunities for improvement.

Guidelines:
- Keep participant responses vivid, realistic, and 2–4 sentences long.
- Allow natural variation: agreement, disagreement, hesitations.
- Product manager should adapt the flow based on the evolving conversation.
""".format(personas="\n\n".join(personas)).format(features="\n\n".join(features))

    agent = Agent(
        name="UserResearchPM",
        instructions=dynamic_prompt,
        model="gpt-4",
    )

    result = await Runner.run(agent, "Start the user research session.")
    
    # Save result to file
    output_file = os.path.join(output_dir, 'summary.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.final_output)
    
    logger.info(f"\nSaved user research session summary to: {output_file}")
    logger.info("\nFacilitator Summary:")
    logger.info(result.final_output)
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    asyncio.run(main())