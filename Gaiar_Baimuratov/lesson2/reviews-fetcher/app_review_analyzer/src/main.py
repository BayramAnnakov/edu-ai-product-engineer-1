#!/usr/bin/env python3
"""
Main script for app review feature request analysis.

This script ties together the functionality from review_processor.py
to analyze app reviews, extract feature requests, group them, and
generate interview questions.
"""
import json
import os
import argparse

from dotenv import load_dotenv
import openai

from review_processor import (
    load_reviews,
    chunk_reviews,
    extract_features_from_chunk,
    group_and_refine_features,
    generate_interview_questions,
)


def process_reviews(reviews_path: str, output_path: str, max_tokens: int = 4000):
    """
    Process reviews to extract feature requests and generate interview questions.

    Args:
        reviews_path: Path to the JSON file containing reviews.
        output_path: Path to save the output JSON file.
        max_tokens: Maximum number of tokens per chunk.
    """
    # Load environment variables
    load_dotenv()

    # Initialize OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    openai_client = openai.OpenAI(api_key=openai_api_key)

    # Load reviews
    print(f"Loading reviews from {reviews_path}...")
    reviews = load_reviews(reviews_path)
    print(f"Loaded {len(reviews)} reviews.")

    # Chunk reviews
    print(f"Chunking reviews (max tokens: {max_tokens})...")
    chunks = chunk_reviews(reviews, max_tokens)
    print(f"Created {len(chunks)} chunks.")

    # Extract feature requests from each chunk
    print("Extracting feature requests...")
    all_raw_feature_requests = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")

        try:
            features = extract_features_from_chunk(chunk, client=openai_client)
            print(f"Extracted {len(features)} feature requests.")
            all_raw_feature_requests.extend(features)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")

    # Save raw feature requests to a temporary file
    tmp_output_dir = os.path.dirname(output_path)
    if not os.path.exists(tmp_output_dir):
        os.makedirs(tmp_output_dir)

    tmp_features_path = os.path.join(tmp_output_dir, "raw_feature_requests.json")
    with open(tmp_features_path, "w", encoding="utf-8") as f:
        json.dump(all_raw_feature_requests, f, indent=2)

    print(
        f"Saved {len(all_raw_feature_requests)} raw feature requests to {tmp_features_path}"
    )

    # Group and refine feature requests
    print("Grouping and refining feature requests...")
    refined_features = group_and_refine_features(
        all_raw_feature_requests, client=openai_client
    )
    print(f"Refined to {len(refined_features)} unique feature topics.")

    # Generate interview questions for each refined feature
    print("Generating interview questions...")
    final_output_data = []

    for feature in refined_features:
        print(f"Generating questions for: {feature}")

        try:
            questions = generate_interview_questions(feature, client=openai_client)

            feature_entry = {
                "topic": feature,
                "core_questions": questions,
                "max_followups": 3,  # Constant value as specified
            }

            final_output_data.append(feature_entry)
        except Exception as e:
            print(f"Error generating questions for {feature}: {e}")

    # Write final output to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output_data, f, indent=2)

    print(f"Final output written to {output_path}")
    return final_output_data


def main():
    """Parse arguments and run the processing."""
    parser = argparse.ArgumentParser(
        description="Analyze app reviews for feature requests"
    )
    parser.add_argument(
        "--reviews-path",
        type=str,
        required=True,
        help="Path to the JSON file containing reviews",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="feature_requests_interview_plan.json",
        help="Path to save the output JSON file",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Maximum number of tokens per chunk",
    )

    args = parser.parse_args()
    process_reviews(args.reviews_path, args.output_path, args.max_tokens)


if __name__ == "__main__":
    main()
