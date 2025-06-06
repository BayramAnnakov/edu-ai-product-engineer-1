#!/usr/bin/env python3
"""
Master script to orchestrate the entire process from feature extraction to report generation.

This script coordinates:
1. Running analyze_all_markets.py to extract features from reviews
2. Running batch_interviews.py to conduct interviews for each feature
3. Running report_generator.py to create consolidated reports
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("process_all_features")


def run_feature_extraction(
    review_data_file: str,
    output_dir: str,
) -> str:
    """
    Run analyze_all_markets.py to extract features from reviews

    Args:
        review_data_file: Path to the reviews data file
        output_dir: Directory to store output

    Returns:
        Path to the extracted features file
    """
    logger.info(f"Running feature extraction on {review_data_file}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Run analyze_all_markets.py
    script_path = os.path.join(os.path.dirname(__file__), "analyze_all_markets.py")

    try:
        process = subprocess.run(
            [sys.executable, script_path, review_data_file],
            check=True,
            capture_output=True,
            text=True,
        )

        # Extract the output file path from the output
        output = process.stdout
        logger.info(f"Feature extraction completed: {output}")

        # Look for the features file in the output directory
        features_files = list(Path(output_dir).glob("features_*.json"))
        if not features_files:
            raise FileNotFoundError(f"No features file found in {output_dir}")

        # Get the most recently created file
        features_file = str(max(features_files, key=lambda x: x.stat().st_mtime))
        logger.info(f"Found features file: {features_file}")

        return features_file

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running feature extraction: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Feature extraction failed: {e}")


def run_batch_interviews(
    features_file: str,
    personas_file: str,
    output_dir: str,
    userboard_script_path: str,
    max_followups: int = 2,
    max_features: Optional[int] = None,
) -> str:
    """
    Run batch_interviews.py to conduct interviews for each feature

    Args:
        features_file: Path to the features JSON file
        personas_file: Path to the personas CSV file
        output_dir: Directory to store results
        userboard_script_path: Path to the userboard4 script
        max_followups: Maximum number of follow-up questions per feature
        max_features: Maximum number of features to process (for testing)

    Returns:
        Path to the interview transcripts directory
    """
    logger.info(f"Running batch interviews for {features_file}")

    # Run batch_interviews.py
    script_path = os.path.join(os.path.dirname(__file__), "batch_interviews.py")

    cmd = [
        sys.executable,
        script_path,
        features_file,
        "--personas",
        personas_file,
        "--output-dir",
        output_dir,
        "--userboard-script",
        userboard_script_path,
        "--max-followups",
        str(max_followups),
    ]

    if max_features is not None:
        cmd.extend(["--max-features", str(max_features)])

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        logger.info("Batch interviews completed")

        # Return the transcripts directory
        transcripts_dir = os.path.join(output_dir, "interview_transcripts")
        if not os.path.exists(transcripts_dir):
            raise FileNotFoundError(
                f"No transcripts directory found at {transcripts_dir}"
            )

        return transcripts_dir

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running batch interviews: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Batch interviews failed: {e}")


def run_report_generation(
    transcripts_dir: str,
    output_dir: str,
) -> Tuple[str, str]:
    """
    Run report_generator.py to create consolidated reports

    Args:
        transcripts_dir: Directory containing interview transcripts
        output_dir: Directory to store reports

    Returns:
        Tuple of (json_report_path, markdown_report_path)
    """
    logger.info(f"Generating reports from {transcripts_dir}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Run report_generator.py
    script_path = os.path.join(os.path.dirname(__file__), "report_generator.py")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report_path = os.path.join(output_dir, f"consolidated_report_{timestamp}.json")
    markdown_report_path = os.path.join(
        output_dir, f"consolidated_report_{timestamp}.md"
    )

    try:
        subprocess.run(
            [
                sys.executable,
                script_path,
                transcripts_dir,
                "--output-json",
                json_report_path,
                "--output-markdown",
                markdown_report_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logger.info("Report generation completed")
        logger.info(f"JSON report: {json_report_path}")
        logger.info(f"Markdown report: {markdown_report_path}")

        return json_report_path, markdown_report_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Error generating reports: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Report generation failed: {e}")


def process_all_features(
    review_data_file: str,
    output_dir: str,
    personas_file: str,
    userboard_script_path: str,
    max_followups: int = 2,
    max_features: Optional[int] = None,
    skip_extraction: bool = False,
    features_file: Optional[str] = None,
    skip_interviews: bool = False,
    transcripts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process all features from review data to final reports

    Args:
        review_data_file: Path to the reviews data file
        output_dir: Directory to store all output
        personas_file: Path to the personas CSV file
        userboard_script_path: Path to the userboard4 script
        max_followups: Maximum number of follow-up questions per feature
        max_features: Maximum number of features to process (for testing)
        skip_extraction: Skip feature extraction (use features_file instead)
        features_file: Path to a pre-existing features file (if skipping extraction)
        skip_interviews: Skip interviews (use transcripts_dir instead)
        transcripts_dir: Path to a pre-existing transcripts directory (if skipping interviews)

    Returns:
        Dictionary with results and paths
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "timestamp": timestamp,
        "output_dir": output_dir,
    }

    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories
    features_dir = os.path.join(output_dir, "features")
    interviews_dir = os.path.join(output_dir, "interviews")
    reports_dir = os.path.join(output_dir, "reports")

    os.makedirs(features_dir, exist_ok=True)
    os.makedirs(interviews_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Step 1: Feature extraction
    if not skip_extraction:
        features_file = run_feature_extraction(review_data_file, features_dir)
    elif features_file is None or not os.path.exists(features_file):
        raise ValueError(
            "Must provide a valid features_file when skip_extraction is True"
        )

    results["features_file"] = features_file

    # Step 2: Batch interviews
    if not skip_interviews:
        transcripts_dir = run_batch_interviews(
            features_file,
            personas_file,
            interviews_dir,
            userboard_script_path,
            max_followups,
            max_features,
        )
    elif transcripts_dir is None or not os.path.exists(transcripts_dir):
        raise ValueError(
            "Must provide a valid transcripts_dir when skip_interviews is True"
        )

    results["transcripts_dir"] = transcripts_dir

    # Step 3: Report generation
    json_report_path, markdown_report_path = run_report_generation(
        transcripts_dir, reports_dir
    )

    results["json_report_path"] = json_report_path
    results["markdown_report_path"] = markdown_report_path

    return results


def main():
    """Main entry point for the process_all_features script"""
    parser = argparse.ArgumentParser(
        description="Process all features from review data to final reports"
    )

    parser.add_argument(
        "--review-data",
        "-r",
        help="Path to the reviews data file",
        default=None,
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        help="Directory to store all output",
        default="feature_processing_output",
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
        "--userboard-script",
        "-u",
        help="Path to the userboard4 script",
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

    parser.add_argument(
        "--skip-extraction",
        "-s",
        help="Skip feature extraction (use --features-file instead)",
        action="store_true",
    )

    parser.add_argument(
        "--features-file",
        "-f",
        help="Path to a pre-existing features file (if skipping extraction)",
        default=None,
    )

    parser.add_argument(
        "--skip-interviews",
        "-i",
        help="Skip interviews (use --transcripts-dir instead)",
        action="store_true",
    )

    parser.add_argument(
        "--transcripts-dir",
        "-t",
        help="Path to a pre-existing transcripts directory (if skipping interviews)",
        default=None,
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.skip_extraction and args.review_data is None:
        parser.error("--review-data is required unless --skip-extraction is specified")

    if args.skip_extraction and args.features_file is None:
        parser.error("--features-file is required when --skip-extraction is specified")

    if args.skip_interviews and args.transcripts_dir is None:
        parser.error(
            "--transcripts-dir is required when --skip-interviews is specified"
        )

    # Process all features
    try:
        results = process_all_features(
            review_data_file=args.review_data,
            output_dir=args.output_dir,
            personas_file=args.personas,
            userboard_script_path=args.userboard_script,
            max_followups=args.max_followups,
            max_features=args.max_features,
            skip_extraction=args.skip_extraction,
            features_file=args.features_file,
            skip_interviews=args.skip_interviews,
            transcripts_dir=args.transcripts_dir,
        )

        # Print summary
        print("\nFeature Processing Complete:")
        print(f"- Features file: {results['features_file']}")
        print(f"- Transcripts directory: {results['transcripts_dir']}")
        print(f"- JSON report: {results['json_report_path']}")
        print(f"- Markdown report: {results['markdown_report_path']}")
        print(f"- All output saved to: {args.output_dir}")

        return 0

    except Exception as e:
        logger.exception(f"Error processing features: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
