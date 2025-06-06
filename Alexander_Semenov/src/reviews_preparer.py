"""
Module for preparing and formatting review data.
"""

import pandas as pd
from typing import List
import logging
from src.logger_config import setup_logger


def prepare_reviews(reviews_df: pd.DataFrame, max_reviews: int = 100) -> List[str]:
    """
    Prepare reviews in a specific format with numbered reviews.
    
    Args:
        reviews_df (pd.DataFrame): DataFrame containing reviews
        max_reviews (int): Maximum number of reviews to include
        
    Returns:
        List[str]: List of formatted review strings
        
    Raises:
        ValueError: If required columns are missing from the DataFrame
    """
    logger = setup_logger(__name__)
    
    # Define required columns
    required_columns = ['Score', 'Summary', 'Text', 'ProfileName']
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in reviews_df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Sample reviews if needed
    if len(reviews_df) > max_reviews:
        reviews_sample = reviews_df.sample(n=max_reviews, random_state=42)
    else:
        reviews_sample = reviews_df.copy()
    
    formatted_reviews = []
    
    for idx, review in reviews_sample.iterrows():
        review_text = (
            f"Review {len(formatted_reviews) + 1}\n"
            f"ProfileName: {review['ProfileName']}\n"
            f"Score: {review['Score']}\n"
            f"Summary: {review['Summary']}\n"
            f"Text: {review['Text']}"
        )
        formatted_reviews.append(review_text)
    
    return formatted_reviews

