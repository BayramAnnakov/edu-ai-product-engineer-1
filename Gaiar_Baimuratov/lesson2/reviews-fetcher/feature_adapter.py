#!/usr/bin/env python3
"""
Feature adapter module to convert between analyze_all_markets.py output format
and UserBoard4 interview_config.json format.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("feature_adapter")


def load_features_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load features from the JSON file produced by analyze_all_markets.py

    Args:
        file_path: Path to the JSON file containing feature requests

    Returns:
        List of feature dictionaries with 'topic' and 'core_questions' keys
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feature file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            features = json.load(f)

        # Validate that it's a list of dictionaries with expected keys
        if not isinstance(features, list):
            raise ValueError(
                "Features file should contain a list of feature dictionaries"
            )

        for feature in features:
            if not isinstance(feature, dict):
                raise ValueError("Each feature should be a dictionary")
            if "topic" not in feature:
                raise ValueError("Each feature should have a 'topic' key")
            if "core_questions" not in feature:
                raise ValueError("Each feature should have a 'core_questions' key")

        return features
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in {file_path}")


def convert_to_userboard_format(
    features: List[Dict[str, Any]], max_followups: int = 2
) -> Dict[str, Any]:
    """
    Convert the list of features to the format expected by UserBoard4

    Args:
        features: List of feature dictionaries with 'topic' and 'core_questions' keys
        max_followups: Maximum number of follow-up questions per feature

    Returns:
        Dictionary with "features" and "max_followups" keys that can be saved as interview_config.json
    """
    # The format expected by UserBoard4 is:
    # {
    #   "features": [
    #     {
    #       "topic": "Feature topic",
    #       "core_questions": ["Q1", "Q2", "Q3"]
    #     },
    #     ...
    #   ],
    #   "max_followups": 2
    # }

    # The features we get from analyze_all_markets.py should already have the right structure,
    # so we just need to wrap them in a dictionary with the right keys
    userboard_config = {"features": features, "max_followups": max_followups}

    return userboard_config


def save_userboard_config(config: Dict[str, Any], output_file: str) -> None:
    """
    Save the UserBoard4 config to a JSON file

    Args:
        config: Dictionary with UserBoard4 config
        output_file: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved UserBoard4 config to {output_file}")


def group_similar_features(
    features: List[Dict[str, Any]], similarity_threshold: float = 0.75
) -> List[Dict[str, Any]]:
    """
    Group similar features to avoid redundant interviews

    Args:
        features: List of feature dictionaries
        similarity_threshold: Threshold for considering features similar (0.0-1.0)

    Returns:
        List of deduplicated feature dictionaries
    """
    # This is a placeholder for now - in a real implementation, you would use
    # NLP techniques to calculate similarity between feature topics and questions

    # For now, we'll just return the original features
    return features


def create_interview_config_for_feature_batch(
    input_file: str,
    output_file: str = None,
    max_followups: int = 2,
    group_similar: bool = False,
) -> Tuple[Dict[str, Any], str]:
    """
    Create an interview_config.json file for a batch of features

    Args:
        input_file: Path to the JSON file from analyze_all_markets.py
        output_file: Path to save the interview_config.json file (default: auto-generated)
        max_followups: Maximum number of follow-up questions per feature
        group_similar: Whether to group similar features

    Returns:
        Tuple of (config_dict, output_file_path)
    """
    # Load features from the input file
    features = load_features_from_file(input_file)
    logger.info(f"Loaded {len(features)} features from {input_file}")

    # Group similar features if requested
    if group_similar:
        features = group_similar_features(features)
        logger.info(f"Grouped into {len(features)} unique feature topics")

    # Convert to UserBoard4 format
    config = convert_to_userboard_format(features, max_followups)

    # Generate output file path if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"interview_config_{timestamp}.json"

    # Save to file
    save_userboard_config(config, output_file)

    return config, output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert feature requests to UserBoard4 interview config"
    )
    parser.add_argument(
        "input_file", help="Path to the JSON file from analyze_all_markets.py"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to save the interview_config.json file (default: auto-generated)",
        default=None,
    )
    parser.add_argument(
        "--max-followups",
        "-m",
        help="Maximum number of follow-up questions per feature",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--group-similar",
        "-g",
        help="Group similar features to avoid redundant interviews",
        action="store_true",
    )

    args = parser.parse_args()

    _, output_file = create_interview_config_for_feature_batch(
        args.input_file, args.output, args.max_followups, args.group_similar
    )

    print(f"Successfully created interview config at {output_file}")
