"""
Module for creating user personas based on product reviews using OpenAI API.
"""

import pandas as pd
import logging
import re
from typing import List, Dict
from src.llm_client import call_openai_api
from src.logger_config import setup_logger

# Prompt template for persona description generation
PERSONA_DESCRIPTION_PROMPT_TEMPLATE = """
You are an expert in user research and persona creation. Based on the provided user reviews, identify {num_personas} unique personas in the form of short, expressive descriptions.

Each persona description should be:
- Concise (1-2 sentences)
- Vivid and evocative, instantly conveying their role, context, and motivation
- Similar in style to these examples:
  - "A social media influencer using their platform to share news and resources on Amazon deforestation"
  - "A retired professional athlete who believes in the captain's abilities and encourages her to aim for greatness"
  - "An electrical engineering graduate student conducting research on using machine learning algorithms for audio recognition"

Instructions:
1. Read the user reviews below
2. Identify recurring patterns in imagery, context, motivation, pain points, and behavior
3. Craft a short but expressive description for each persona
4. Number each persona (1., 2., etc.)

Review Data:
{reviews_summary}
"""

class PersonaCreatorAgent:
    """Agent responsible for creating user personas from review data."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Persona Creator Agent.
        
        Args:
            api_key (str): OpenAI API key for authentication
        """
        self.api_key = api_key
        self.logger = setup_logger(__name__)
    
    def _prepare_reviews_summary(self, reviews_df: pd.DataFrame, max_reviews: int = 100) -> str:
        """
        Prepare a summary of reviews for persona creation.
        
        Args:
            reviews_df (pd.DataFrame): DataFrame containing product reviews
            max_reviews (int): Maximum number of reviews to process
            
        Returns:
            str: Formatted string containing review summaries
            
        Raises:
            ValueError: If reviews_df is empty or required columns are missing
        """
        if reviews_df.empty:
            self.logger.warning("Empty DataFrame provided to _prepare_reviews_summary")
            return ""
        
        # Select required columns
        needed_columns = ['Summary', 'Text', 'ProfileName']
        if not all(col in reviews_df.columns for col in needed_columns):
            missing_cols = [col for col in needed_columns if col not in reviews_df.columns]
            error_msg = f"Missing required columns: {', '.join(missing_cols)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Sample reviews if needed
        if len(reviews_df) > max_reviews:
            self.logger.info(
                f"Limiting reviews from {len(reviews_df)} to {max_reviews} for summary"
            )
            reviews_sample = reviews_df.sample(n=max_reviews, random_state=42)
        else:
            reviews_sample = reviews_df
        
        # Prepare summary text
        summary_parts = []
        
        # Add overall statistics
        total_reviews = len(reviews_df)
        unique_reviewers = reviews_df['ProfileName'].nunique()
        summary_parts.append(
            f"Overall Statistics:\n"
            f"- Total reviews: {total_reviews}\n"
            f"- Unique reviewers: {unique_reviewers}"
        )
        
        # Add sampled reviews
        summary_parts.append("\nSample Reviews:")
        for idx, row in reviews_sample.iterrows():
            summary_parts.append(
                f"\nReview {idx + 1}:\n"
                f"Reviewer: {row['ProfileName']}\n"
                f"Summary: {row['Summary']}\n"
                f"Text: {row['Text']}"
            )
        
        return "\n\n".join(summary_parts)
    
    def _parse_persona_descriptions(
        self, 
        llm_response: str, 
        num_personas: int
    ) -> List[Dict[str, str]]:
        """
        Parse the LLM response to extract structured persona information.
        
        Args:
            llm_response (str): Raw response from the LLM containing persona descriptions
            num_personas (int): Expected number of personas to extract
            
        Returns:
            List[Dict[str, str]]: List of dictionaries containing parsed personas
                Each dict has 'name', 'background', 'needs', and 'goals' keys
        """
        if not llm_response:
            self.logger.warning("Empty LLM response provided to _parse_persona_descriptions")
            return []
        
        personas = []
        
        # Split response into persona blocks using numbered list pattern
        persona_blocks = re.split(r'\n\d+\.', llm_response)
        
        # Remove any empty blocks and process each persona
        for block in persona_blocks:
            if not block.strip():
                continue
                
            try:
                # Extract name and background (usually in first paragraph)
                name_match = re.search(r'^(.+?)(?:\n|$)', block.strip(), re.MULTILINE)
                background_match = re.search(r'(?:background:?\s*)(.*?)(?:\n|$)', 
                                          block, re.MULTILINE | re.IGNORECASE)
                
                # Extract needs/pain points
                needs_match = re.search(r'(?:needs|pain points):?\s*(.*?)(?:\n|$)', 
                                      block, re.MULTILINE | re.IGNORECASE)
                
                # Extract goals/motivations
                goals_match = re.search(r'(?:goals|motivations):?\s*(.*?)(?:\n|$)', 
                                      block, re.MULTILINE | re.IGNORECASE)
                
                persona = {
                    'name': name_match.group(1).strip() if name_match else 'Unknown',
                    'background': background_match.group(1).strip() if background_match else '',
                    'needs': needs_match.group(1).strip() if needs_match else '',
                    'goals': goals_match.group(1).strip() if goals_match else ''
                }
                
                personas.append(persona)
                
            except Exception as e:
                self.logger.warning(f"Error parsing persona block: {str(e)}")
                continue
        
        # Ensure we don't return more personas than requested
        return personas[:num_personas]
        
    def create_personas(
        self, 
        reviews_df: pd.DataFrame, 
        num_personas: int = 4
    ) -> List[Dict[str, str]]:
        """
        Create user personas based on review data.
        
        Args:
            reviews_df (pd.DataFrame): DataFrame containing product reviews
            num_personas (int): Number of personas to generate
            
        Returns:
            List[Dict[str, str]]: List of generated personas, each containing
                                 'name', 'background', 'needs', and 'goals' keys
        """
        self.logger.info("Agent 2: Starting persona creation...")
        
        if reviews_df.empty:
            self.logger.warning("Empty DataFrame provided to create_personas")
            return []
        
        try:
            # Prepare review summary
            reviews_summary = self._prepare_reviews_summary(reviews_df)
            if not reviews_summary:
                self.logger.error("Failed to prepare reviews summary")
                return []
                
            self.logger.info(
                f"Prepared review summary for LLM processing "
                f"(length: {len(reviews_summary)} chars)"
            )
            
            # Format the prompt for persona generation
            full_prompt = PERSONA_DESCRIPTION_PROMPT_TEMPLATE.format(
                num_personas=num_personas,
                reviews_summary=reviews_summary
            )
            
            # Call OpenAI API
            system_message = (
                "You are a market research expert specializing in creating detailed "
                "user personas from customer reviews and feedback. Be specific and "
                "realistic in your persona descriptions."
            )
            
            llm_response = call_openai_api(
                prompt=full_prompt,
                system_message=system_message,
                api_key=self.api_key
            )
            
            if llm_response is None:
                self.logger.error("Failed to get response from OpenAI API")
                return []
                
            self.logger.debug(f"Raw LLM response: {llm_response[:500]}...")
            
            # Parse personas from the response
            personas = self._parse_persona_descriptions(llm_response, num_personas)
            self.logger.info(f"Successfully created {len(personas)} personas")
            
            return personas
            
        except Exception as e:
            self.logger.error(f"Error during persona creation: {str(e)}")
            return []