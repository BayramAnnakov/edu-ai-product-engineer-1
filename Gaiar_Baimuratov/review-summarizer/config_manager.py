"""
Configuration management for the App Review Summarization tool.

This module handles loading and validating configuration from multiple sources:
1. Default values
2. Environment variables (loaded from .env or system environment)
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Removed yaml import as it's no longer needed
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    "appbot_app_id": None,
    "appbot_api_username": None,
    "appbot_api_password": None,
    "openai_api_key": None,
    "days": 30,
    "limit": 100,
    "min_rating": 1,
    "max_rating": 5,
    "extractive_sentences": 5,
    "verbose": False,
    "output_format": "text",
}

def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary with configuration from environment variables
    """
    env_config = {}
    
    # Map environment variables to config keys
    env_mappings = {
        "APPBOT_APP_ID": "appbot_app_id",
        "APPBOT_API_USERNAME": "appbot_api_username",
        "APPBOT_API_PASSWORD": "appbot_api_password",
        "OPENAI_API_KEY": "openai_api_key",
        "REVIEW_DAYS": "days",
        "REVIEW_LIMIT": "limit",
        "MIN_RATING": "min_rating",
        "MAX_RATING": "max_rating",
        "EXTRACTIVE_SENTENCES": "extractive_sentences",
        "VERBOSE": "verbose",
        "OUTPUT_FORMAT": "output_format",
    }
    
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert types as needed
            if config_key in ["days", "limit", "min_rating", "max_rating", "extractive_sentences"]:
                try:
                    value = int(value)
                except ValueError:
                    print(f"Warning: Could not convert {env_var}={value} to integer", file=sys.stderr)
                    continue
            elif config_key == "verbose":
                value = value.lower() in ("1", "true", "yes", "y")
            
            env_config[config_key] = value
    
    return env_config

def load_config() -> Dict[str, Any]:
    """
    Load configuration from all sources, with priority:
    1. Environment variables (highest)
    2. Default values (lowest)
    
    Returns:
        Merged configuration dictionary
    """
    # Start with default values
    config = DEFAULT_CONFIG.copy()
    
    # Update with environment variables
    # load_dotenv() ensures variables from .env are loaded into os.environ
    env_config = load_env_config()
    config.update(env_config)
    
    return config

def validate_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate configuration and return any errors.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of error messages, empty if valid
    """
    errors = {}
    
    # Check required values
    if not config.get("appbot_api_username"):
        errors["appbot_api_username"] = "AppBot API username is required"
    
    if not config.get("appbot_api_password"):
        errors["appbot_api_password"] = "AppBot API password is required"
    
    if not config.get("openai_api_key"):
        errors["openai_api_key"] = "OpenAI API key is required"
    
    # Validate numeric ranges
    if not (1 <= config.get("min_rating", 1) <= 5):
        errors["min_rating"] = "Min rating must be between 1 and 5"
    
    if not (1 <= config.get("max_rating", 5) <= 5):
        errors["max_rating"] = "Max rating must be between 1 and 5"
    
    if config.get("min_rating", 1) > config.get("max_rating", 5):
        errors["rating_range"] = "Min rating cannot be greater than max rating"
    
    if config.get("limit", 100) <= 0:
        errors["limit"] = "Review limit must be positive"
    
    if config.get("days", 30) <= 0:
        errors["days"] = "Days must be positive"
    
    # Validate output format
    valid_formats = ["text", "json", "markdown"]
    if config.get("output_format") not in valid_formats:
        errors["output_format"] = f"Output format must be one of: {', '.join(valid_formats)}"
    
    return errors

if __name__ == "__main__":
    # Example usage: Load and print the configuration
    config = load_config()
    print("Current Configuration (Defaults + Environment Variables):")
    for key, value in config.items():
        print(f"{key}: {value}")
    
    # Validate
    errors = validate_config(config)
    if errors:
        print("\nConfiguration Errors:")
        for key, error in errors.items():
            print(f"  {key}: {error}")
    else:
        print("\nConfiguration is valid.")