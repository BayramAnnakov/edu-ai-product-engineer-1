#!/usr/bin/env python3
"""
Wrapper script to analyze app reviews and extract feature requests.

This script simplifies running the feature request analysis by:
1. Automatically finding review files in the appbot-client/results directory
2. Letting users select which review file to analyze
3. Running the analysis pipeline
"""
import os
import argparse
import glob
import json
from datetime import datetime
import sys
import subprocess
from pathlib import Path

# Get the absolute path to the app_review_analyzer directory
SCRIPT_DIR = Path(__file__).resolve().parent
ANALYZER_DIR = SCRIPT_DIR / "app_review_analyzer"
RESULTS_DIR = SCRIPT_DIR / "appbot-client" / "results"
OUTPUT_DIR = SCRIPT_DIR / "output"


def list_review_files():
    """Find and list all review JSON files in results directory."""
    review_files = glob.glob(str(RESULTS_DIR / "reviews_*.json"))

    if not review_files:
        print("No review files found in", RESULTS_DIR)
        return []

    print(f"Found {len(review_files)} review files:")
    for i, file_path in enumerate(review_files):
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # Size in KB

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                review_count = len(data.get("results", []))
            print(f"[{i+1}] {filename} ({file_size:.1f} KB, {review_count} reviews)")
        except Exception as e:
            print(f"[{i+1}] {filename} ({file_size:.1f} KB, unable to read: {e})")

    return review_files


def select_review_file(review_files, non_interactive=False):
    """Let user select a review file."""
    if not review_files:
        return None

    # In non-interactive mode, just pick the most recent file (last in list)
    if non_interactive:
        print(
            f"Auto-selecting the most recent file: {os.path.basename(review_files[-1])}"
        )
        return review_files[-1]

    try:
        selection = input(
            "\nEnter the number of the file to analyze (or press Enter to exit): "
        )
        if not selection:
            return None

        index = int(selection) - 1
        if 0 <= index < len(review_files):
            return review_files[index]
        else:
            print("Invalid selection!")
            return None
    except (ValueError, EOFError):
        print(
            "Non-interactive mode detected or invalid input. Selecting most recent file."
        )
        return review_files[-1]


def analyze_reviews(review_path):
    """Run the analysis on the selected review file."""
    if not os.path.exists(review_path):
        print(f"Error: File {review_path} not found!")
        return False

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate output filename based on input filename
    base_filename = os.path.basename(review_path)
    app_id = base_filename.split("_")[1]  # Extract app_id from filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"features_{app_id}_{timestamp}.json")

    # Build command
    main_script = os.path.join(ANALYZER_DIR, "src", "main.py")
    cmd = [
        sys.executable,  # Current Python executable
        main_script,
        "--reviews-path",
        review_path,
        "--output-path",
        output_path,
    ]

    print(f"\nAnalyzing reviews from {base_filename}...")
    print(f"Output will be saved to {output_path}\n")

    # Run the analysis
    try:
        subprocess.run(cmd, check=True)
        print(f"\nAnalysis complete! Results saved to: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running analysis: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Analyze app reviews for feature requests"
    )
    parser.add_argument("--file", type=str, help="Specific review file to analyze")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (auto-select most recent file)",
    )
    args = parser.parse_args()

    if args.file:
        # Use specified file
        if os.path.exists(args.file):
            analyze_reviews(args.file)
        else:
            print(f"Error: File {args.file} not found!")
    else:
        # Interactive or auto mode
        review_files = list_review_files()
        selected_file = select_review_file(
            review_files, non_interactive=args.non_interactive
        )

        if selected_file:
            analyze_reviews(selected_file)


if __name__ == "__main__":
    main()
