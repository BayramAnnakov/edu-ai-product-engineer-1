#!/usr/bin/env python3
"""
Batch processing script for running multiple feature interviews with UserBoard4.

This script takes the output from analyze_all_markets.py and processes each feature
through UserBoard4, generating interview transcripts with personas from personas.csv.
"""

import os
import sys
import json
import logging
import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from feature_adapter import (
    load_features_from_file,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("batch_interviews")


def setup_directories(output_dir: str) -> Dict[str, str]:
    """
    Set up output directories for batch processing

    Args:
        output_dir: Base output directory

    Returns:
        Dictionary of directory paths
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dirs = {
        "base": output_dir,
        "transcripts": os.path.join(output_dir, "interview_transcripts"),
        "configs": os.path.join(output_dir, "configs"),
        "summaries": os.path.join(output_dir, "summaries"),
        "timestamp": timestamp,
    }

    # Create directories
    for key, path in dirs.items():
        if key != "timestamp":
            os.makedirs(path, exist_ok=True)

    return dirs


def process_feature_batch(
    features_file: str,
    personas_file: str,
    output_dir: str,
    userboard_script_path: str,
    max_followups: int = 2,
    max_features: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process a batch of features using UserBoard4

    Args:
        features_file: Path to the features JSON file from analyze_all_markets.py
        personas_file: Path to the personas CSV file
        output_dir: Directory to store results
        userboard_script_path: Path to the userboard4-baimuratov.py script
        max_followups: Maximum number of follow-up questions per feature
        max_features: Maximum number of features to process (for testing)

    Returns:
        Dictionary with processing results and statistics
    """
    # Create directories
    dirs = setup_directories(output_dir)
    logger.info(f"Set up output directories in {output_dir}")

    # Load features
    features = load_features_from_file(features_file)
    logger.info(f"Loaded {len(features)} features from {features_file}")

    # Limit features if specified
    if max_features is not None and max_features > 0:
        features = features[:max_features]
        logger.info(f"Limited to processing {len(features)} features")

    # Process each feature
    results = []
    for i, feature in enumerate(features, 1):
        logger.info(f"Processing feature {i}/{len(features)}: {feature['topic']}")

        # Create a temporary interview_config.json for this feature
        feature_config = {"features": [feature], "max_followups": max_followups}

        # Generate a safe filename from the topic
        safe_topic = "".join(
            c if c.isalnum() or c in ["-", "_"] else "_" for c in feature["topic"][:50]
        )
        config_filename = f"feature_{i}_{safe_topic}.json"
        config_path = os.path.join(dirs["configs"], config_filename)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(feature_config, f, indent=2, ensure_ascii=False)

        # Set up environment variables for UserBoard4
        env = os.environ.copy()
        env["INTERVIEW_CONFIG"] = config_path
        env["PERSONAS_CSV"] = personas_file

        # Run UserBoard4 for this feature
        logger.info(f"Running UserBoard4 for feature: {feature['topic']}")

        try:
            # Run the userboard script as a subprocess
            subprocess.run(
                [sys.executable, userboard_script_path],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

            # Check if the transcript was created
            transcript_dir = (
                Path(userboard_script_path).parent / "interview_transcripts"
            )

            # Find the most recently created transcript file
            if transcript_dir.exists():
                transcript_files = list(transcript_dir.glob("*.md"))
                if transcript_files:
                    # Sort by modification time (most recent first)
                    latest_transcript = max(
                        transcript_files, key=lambda f: f.stat().st_mtime
                    )

                    # Copy to our output directory
                    shutil.copy(
                        latest_transcript,
                        os.path.join(
                            dirs["transcripts"], f"feature_{i}_{safe_topic}.md"
                        ),
                    )

                    logger.info(f"Copied transcript to {dirs['transcripts']}")

                    results.append(
                        {
                            "feature_id": i,
                            "topic": feature["topic"],
                            "transcript_file": f"feature_{i}_{safe_topic}.md",
                            "status": "success",
                        }
                    )
                    continue

            # If we get here, no transcript was found
            logger.warning(
                f"No transcript generated for feature {i}: {feature['topic']}"
            )
            results.append(
                {"feature_id": i, "topic": feature["topic"], "status": "no_transcript"}
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running UserBoard4 for feature {i}: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")

            results.append(
                {
                    "feature_id": i,
                    "topic": feature["topic"],
                    "status": "error",
                    "error_message": str(e),
                }
            )

    # Generate summary
    summary = {
        "timestamp": dirs["timestamp"],
        "total_features": len(features),
        "successful_interviews": sum(1 for r in results if r["status"] == "success"),
        "failed_interviews": sum(1 for r in results if r["status"] != "success"),
        "results": results,
    }

    # Save summary
    summary_path = os.path.join(
        dirs["summaries"], f"batch_summary_{dirs['timestamp']}.json"
    )
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved summary to {summary_path}")
    logger.info(
        f"Processed {summary['total_features']} features: "
        + f"{summary['successful_interviews']} successful, "
        + f"{summary['failed_interviews']} failed"
    )

    return summary


def main():
    """Main entry point for the batch processing script"""
    parser = argparse.ArgumentParser(
        description="Run batch interviews for feature requests"
    )
    parser.add_argument(
        "features_file",
        help="Path to the features JSON file from analyze_all_markets.py",
    )
    parser.add_argument(
        "--personas",
        "-p",
        help="Path to the personas CSV file",
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "userboard", "personas.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Directory to store results",
        default="batch_interviews_output",
    )
    parser.add_argument(
        "--userboard-script",
        "-u",
        help="Path to the userboard4-baimuratov.py script",
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "userboard",
            "userboard4-baimuratov.py",
        ),
    )
    parser.add_argument(
        "--max-followups",
        "-m",
        help="Maximum number of follow-up questions per feature",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--max-features",
        "-n",
        help="Maximum number of features to process (for testing)",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    # Verify paths exist
    for path_name, path in [
        ("Features file", args.features_file),
        ("Personas file", args.personas),
        ("UserBoard4 script", args.userboard_script),
    ]:
        if not os.path.exists(path):
            logger.error(f"{path_name} not found: {path}")
            return 1

    # Process batch
    try:
        summary = process_feature_batch(
            features_file=args.features_file,
            personas_file=args.personas,
            output_dir=args.output_dir,
            userboard_script_path=args.userboard_script,
            max_followups=args.max_followups,
            max_features=args.max_features,
        )

        # Print summary
        print("\nBatch Interview Processing Summary:")
        print(f"Total features processed: {summary['total_features']}")
        print(f"Successful interviews: {summary['successful_interviews']}")
        print(f"Failed interviews: {summary['failed_interviews']}")
        print(f"Results saved to: {args.output_dir}")

        return 0
    except Exception as e:
        logger.exception(f"Error processing batch: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
