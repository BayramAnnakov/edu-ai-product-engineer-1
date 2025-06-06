"""
Module for making OpenAI API calls with retry functionality.
"""

from openai import OpenAI
import logging
from typing import Optional
import time
from src.logger_config import setup_logger

def call_openai_api(
    prompt: str,
    api_key: str,
    model: str = "gpt-4",
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Optional[str]:
    """
    Make an OpenAI API call with exponential backoff retry logic.
    
    Args:
        prompt (str): The user message/prompt to send
        api_key (str): OpenAI API key
        model (str): OpenAI model to use, defaults to "gpt-4"
        max_retries (int): Maximum number of retry attempts, defaults to 3
        initial_delay (float): Initial delay between retries in seconds, defaults to 1.0
        
    Returns:
        Optional[str]: Generated text if successful, None if all retries failed
    """
    logger = setup_logger(__name__)
    
    # Initialize OpenAI client with just the API key
    client = OpenAI(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            # Make the API call with just the user message
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and return the response
            result = response.choices[0].message.content
            logger.info(
                f"Successfully generated response (attempt {attempt + 1}/{max_retries})"
            )
            return result
            
        except Exception as e:
            # Handle any errors
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed after {max_retries} attempts. Last error: {str(e)}"
                )
                return None
                
            # Calculate exponential backoff delay
            delay = initial_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                f"Retrying in {delay:.1f} seconds..."
            )
            time.sleep(delay)
    
    return None