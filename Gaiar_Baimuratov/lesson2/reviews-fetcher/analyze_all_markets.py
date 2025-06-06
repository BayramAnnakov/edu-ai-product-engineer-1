#!/usr/bin/env python3
"""
Script to analyze review data from all markets.
Enhanced with rich UI for better progress visualization.
"""
import json
import sys
from pathlib import Path
import typer
from collections import Counter
from datetime import datetime
from typing import Optional
import openai
import os

# Add app_review_analyzer to path
sys.path.append(str(Path(__file__).parent / "app_review_analyzer"))
from src.review_processor import (
    chunk_reviews,
    extract_features_from_chunk,
    group_and_refine_features,
    generate_interview_questions,
)

# Import UI utilities
from src.ui_utils import (
    display_header,
    display_section,
    display_success,
    display_error,
    display_warning,
    display_info,
    display_stats_table,
    display_summary,
    create_progress,
    generate_llm_summary,
    display_markdown,
    TimedOperation,
)


def analyze_reviews_file(file_path, output_dir=None):
    """Analyze reviews from a JSON file."""
    display_header("APP REVIEW ANALYSIS")

    # Setup output directory
    if output_dir is None:
        output_dir = Path(__file__).parent / "all_markets_analysis"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)
    display_info(f"Output directory: {output_dir}")

    # Load reviews
    with TimedOperation(f"Loading reviews from {Path(file_path).name}"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            display_error(f"Failed to load JSON file: {e}")
            return None

    # Basic statistics
    app_id = data.get("app_id")
    total_reviews = len(data.get("results", []))
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    display_section("App Statistics")

    # App info table
    app_info = [
        {
            "App ID": app_id,
            "Date Range": f"{start_date} to {end_date}",
            "Total Reviews": total_reviews,
        }
    ]
    display_stats_table("App Information", app_info)

    # Country distribution
    countries = Counter(review.get("country") for review in data.get("results", []))

    if countries:
        country_data = [
            {
                "Country": country,
                "Reviews": count,
                "Percentage": f"{count/total_reviews*100:.1f}%",
            }
            for country, count in countries.most_common()
        ]
        display_section(f"Countries ({len(countries)})")
        display_stats_table("Reviews by Country", country_data[:10])

        if len(countries) > 10:
            display_info(f"...and {len(countries) - 10} more countries")

    # Language distribution
    languages = Counter(
        review.get("detected_language") for review in data.get("results", [])
    )

    if languages:
        language_data = [
            {
                "Language": lang or "Unknown",
                "Reviews": count,
                "Percentage": f"{count/total_reviews*100:.1f}%",
            }
            for lang, count in languages.most_common()
        ]
        display_section(f"Languages ({len(languages)})")
        display_stats_table("Reviews by Language", language_data[:10])

        if len(languages) > 10:
            display_info(f"...and {len(languages) - 10} more languages")

    # Rating distribution
    ratings = Counter(review.get("rating") for review in data.get("results", []))

    if ratings:
        rating_data = [
            {
                "Rating": rating,
                "Reviews": count,
                "Percentage": f"{count/total_reviews*100:.1f}%",
            }
            for rating, count in sorted(ratings.items(), reverse=True)
            if rating is not None
        ]
        display_section("Reviews by Rating")
        display_stats_table("Rating Distribution", rating_data)

    # Extract review texts
    review_texts = [review.get("body", "") for review in data.get("results", [])]
    review_texts = [text for text in review_texts if text]  # Filter empty reviews

    display_section("Analysis Plan")
    display_info(f"Processing {len(review_texts)} review texts")

    # Process with review_processor
    try:
        # Initialize result data
        result_data = {
            "app_id": app_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_count": total_reviews,
        }

        # Chunk reviews
        with TimedOperation("Chunking reviews"):
            chunks = chunk_reviews(review_texts)
            display_success(f"Created {len(chunks)} chunks")

        # Extract feature requests
        display_section("Extracting Feature Requests")
        all_raw_features = []

        with create_progress() as progress:
            extract_task = progress.add_task(
                "[cyan]Extracting features...", total=len(chunks)
            )

            for i, chunk in enumerate(chunks):
                progress.update(
                    extract_task,
                    description=f"[cyan]Extracting features from chunk {i+1}/{len(chunks)}",
                )
                features = extract_features_from_chunk(chunk)
                all_raw_features.extend(features)
                progress.update(extract_task, advance=1)

        # Display raw features statistics
        raw_feature_count = len(all_raw_features)
        display_success(f"Extracted {raw_feature_count} raw feature requests")

        # Count duplicates using Counter
        duplicate_counter = Counter(all_raw_features)
        unique_raw_count = len(duplicate_counter)
        duplicates_count = raw_feature_count - unique_raw_count

        duplicate_stats = [
            {"Metric": "Total Raw Features", "Count": raw_feature_count},
            {"Metric": "Unique Raw Features", "Count": unique_raw_count},
            {"Metric": "Duplicate Mentions", "Count": duplicates_count},
        ]
        display_stats_table("Feature Extraction Statistics", duplicate_stats)

        # Save raw features
        with TimedOperation("Saving raw features"):
            raw_features_file = (
                output_dir
                / f"raw_features_{app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(raw_features_file, "w", encoding="utf-8") as f:
                json.dump(all_raw_features, f, indent=2, ensure_ascii=False)

            display_success(f"Saved raw features to {raw_features_file.name}")

        # Show top raw features by frequency
        if duplicate_counter:
            top_raw_features = [
                {"Feature Request": feature, "Mentions": count}
                for feature, count in duplicate_counter.most_common(10)
            ]
            display_stats_table("Most Common Raw Feature Requests", top_raw_features)

        # Group and refine features
        display_section("Refining Feature Requests")
        with TimedOperation("Grouping and refining features"):
            refined_features = group_and_refine_features(all_raw_features)
            display_success(f"Refined to {len(refined_features)} unique feature topics")

        # Reduction stats
        reduction_stats = [
            {"Metric": "Raw Feature Requests", "Count": raw_feature_count},
            {"Metric": "Refined Feature Topics", "Count": len(refined_features)},
            {
                "Metric": "Reduction Ratio",
                "Count": f"{raw_feature_count/max(1, len(refined_features)):.1f}:1",
            },
        ]
        display_stats_table("Feature Refinement Statistics", reduction_stats)

        # Display refined features
        if refined_features:
            refined_feature_list = [
                {"#": i + 1, "Feature Topic": feature}
                for i, feature in enumerate(refined_features)
            ]
            display_stats_table("Refined Feature Topics", refined_feature_list)

        # Generate interview questions
        display_section("Generating Interview Questions")
        final_output = []

        with create_progress() as progress:
            question_task = progress.add_task(
                "[magenta]Generating questions...", total=len(refined_features)
            )

            for feature in refined_features:
                progress.update(
                    question_task,
                    description=f"[magenta]Generating questions for: {feature[:30]}...",
                )
                questions = generate_interview_questions(feature)
                feature_entry = {
                    "topic": feature,
                    "core_questions": questions,
                    "max_followups": 3,
                }
                final_output.append(feature_entry)
                progress.update(question_task, advance=1)

        display_success(
            f"Generated {len(final_output) * 3} questions for {len(final_output)} features"
        )

        # Save final output
        with TimedOperation("Saving final output"):
            final_output_file = (
                output_dir
                / f"features_{app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(final_output_file, "w", encoding="utf-8") as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)

        # Include result stats in the data for summary generation
        result_data.update(
            {
                "feature_count": len(refined_features),
                "raw_feature_count": raw_feature_count,
                "duplicates_count": duplicates_count,
                "top_features": refined_features[:10],
                "country_stats": {k: v for k, v in countries.most_common()},
            }
        )

        # Generate executive summary with GPT-4o if OpenAI API key is available
        summary = None
        if os.environ.get("OPENAI_API_KEY"):
            display_section("Generating Executive Summary")
            with TimedOperation("Generating analysis summary with GPT-4o"):
                try:
                    openai_client = openai.OpenAI()
                    summary = generate_llm_summary(result_data, openai_client)
                    display_markdown(summary)
                except Exception as e:
                    display_error(f"Failed to generate summary: {e}")

        # Final summary
        summary_text = f"""
        • Analyzed {total_reviews} reviews from {len(countries)} countries in {len(languages)} languages
        • Extracted {raw_feature_count} raw feature requests ({unique_raw_count} unique)
        • Refined into {len(refined_features)} actionable feature topics
        • Generated {len(final_output) * 3} interview questions
        • Results saved to:
          - Raw features: {raw_features_file.name}
          - Features with questions: {final_output_file.name}
        """

        # Add AI summary if available
        if summary:
            summary_text += f"\n\nAI SUMMARY:\n{summary}"

        display_summary("Analysis Complete", summary_text)
        return final_output_file

    except Exception as e:
        display_error(f"Error during analysis: {e}")
        return None


def main(
    file_path: str = typer.Argument(..., help="Path to the JSON file with reviews"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory"),
    generate_summary: bool = typer.Option(
        True, help="Generate an AI summary of the analysis"
    ),
):
    """
    Analyze app reviews and extract feature requests with interview questions.
    Enhanced with rich UI for better progress visualization.
    """
    # Set OpenAI API key if available
    if not os.environ.get("OPENAI_API_KEY") and not generate_summary:
        display_warning("No OpenAI API key found. Summary generation will be skipped.")

    try:
        output_file = analyze_reviews_file(file_path, output_dir)
        if output_file:
            return str(output_file)
        return None
    except Exception as e:
        display_error(f"An error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    typer.run(main)
