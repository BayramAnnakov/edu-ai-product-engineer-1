import pandas as pd
from pathlib import Path
from typing import Optional
from loguru import logger

def load_reviews(
    file_path: str = "Reviews.csv",
    nrows: Optional[int] = None,
    chunksize: Optional[int] = None
) -> pd.DataFrame:
    """
    Load reviews from the CSV file.
    
    Args:
        file_path (str): Path to the Reviews.csv file
        nrows (int, optional): Number of rows to read. If None, reads all rows.
        chunksize (int, optional): If set, returns an iterator for chunk-by-chunk reading.
    
    Returns:
        pd.DataFrame: DataFrame containing the reviews data
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Reviews file not found at {file_path}")
            
        logger.info(f"Loading reviews from {file_path}")
        
        if chunksize:
            # Return an iterator for chunk-by-chunk reading
            return pd.read_csv(
                file_path,
                chunksize=chunksize,
                low_memory=False  # Helps with large files
            )
        else:
            # Read the entire file or specified number of rows
            return pd.read_csv(
                file_path,
                nrows=nrows,
                low_memory=False  # Helps with large files
            )
            
    except Exception as e:
        logger.error(f"Error loading reviews: {str(e)}")
        raise