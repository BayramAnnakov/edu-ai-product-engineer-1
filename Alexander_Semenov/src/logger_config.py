"""
Module for configuring logging across the application.
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Configure and return a logger instance with both file and console handlers.
    
    Args:
        name (str): Name for the logger, defaults to module name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers if they already exist
    if logger.hasHandlers():
        return logger
        
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and configure file handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f'app_{datetime.now().strftime("%Y%m%d")}.log'
    )
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Add file handler to logger (console handler already added via basicConfig)
    logger.addHandler(file_handler)
    
    return logger