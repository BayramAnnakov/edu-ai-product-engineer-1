"""
Module for loading and validating CSV files containing product reviews.
"""

import pandas as pd
from typing import List, Dict
import logging
from src.logger_config import setup_logger

# Required columns that must be present in the CSV file
REQUIRED_COLUMNS = [
    'Id',                       # Unique identifier for the review
    'ProductId',                # Product identifier
    'Score',                    # Numerical rating (1-5 stars)
    'Text',                     # The actual review content
    'Time'                      # Time when the review was written
]

def load_reviews(csv_path: str) -> pd.DataFrame:
    """
    Load and validate product reviews from a CSV file.
    
    Args:
        csv_path (str): Path to the CSV file containing product reviews

    Returns:
        pd.DataFrame: DataFrame containing the product reviews

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If the CSV file cannot be parsed or is missing required columns
    """
    logger = setup_logger(__name__)
    logger.info(f"Loading reviews from {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        
        # Check for required columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            missing_cols_str = ", ".join(missing_columns)
            error_msg = f"Missing required columns in CSV: {missing_cols_str}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Successfully validated CSV structure")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        # Re-raise FileNotFoundError as it already provides appropriate context
        raise
    except pd.errors.ParserError as e:
        error_msg = f"Failed to parse CSV file: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error reading CSV file: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)