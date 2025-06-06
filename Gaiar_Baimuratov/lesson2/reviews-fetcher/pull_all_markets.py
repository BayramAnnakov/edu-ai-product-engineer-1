#!/usr/bin/env python3
"""
Script to pull reviews from all markets for the past 365 days.
Enhanced with rich UI for better progress visualization.
Uses parallel fetching for improved performance.
"""
import sys
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
import typer
from typing import Optional

# Add appbot-client to path
sys.path.append(str(Path(__file__).parent / "appbot-client"))
from appbot import AppBotClient

# Add app_review_analyzer to path for UI utilities
sys.path.append(str(Path(__file__).parent / "app_review_analyzer"))
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
    TimedOperation,
)


def get_all_countries(client, app_id):
    """Get all available countries for an app."""
    with TimedOperation(f"Fetching available countries for app {app_id}"):
        countries = client.get_countries(app_id)

        # Display countries in a table
        country_data = []
        for country in countries:
            country_data.append({"ID": country["id"], "Name": country["name"]})

        display_section(f"Found {len(countries)} countries")
        if len(countries) <= 20:  # Only show table if not too many countries
            display_stats_table("Available Countries", country_data)
        else:
            display_info(f"Showing first 10 of {len(countries)} countries:")
            display_stats_table("Sample Countries", country_data[:10])

        return countries


def fetch_country_reviews(client, app_id, country, start_date, end_date, progress=None):
    """
    Fetch reviews for a single country.

    Args:
        client: AppBotClient instance
        app_id: App ID to fetch reviews for
        country: Country dictionary with 'id' and 'name' keys
        start_date: Start date string in YYYY-MM-DD format
        end_date: End date string in YYYY-MM-DD format
        progress: Optional progress tracker for rich UI

    Returns:
        Tuple containing (country_name, country_id, reviews_list, stats_dict)
    """
    country_id = country["id"]
    country_name = country["name"]
    country_reviews = []
    page = 1
    total_pages = 1

    # Track statistics for this country
    language_stats = {}
    rating_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # Create a page task if progress is provided
    page_task = None
    if progress:
        page_task = progress.add_task(
            f"[cyan]Fetching pages for {country_name}", total=None, visible=True
        )

    while page <= total_pages:
        try:
            reviews = client.get_reviews(
                app_id=app_id,
                start=start_date,
                end=end_date,
                country=country_id,
                page=page,
            )

            results = reviews.get("results", [])
            country_reviews.extend(results)
            total_pages = reviews.get("total_pages", 1)

            # Update progress bar with total pages after first response
            if page == 1 and progress and page_task:
                progress.update(page_task, total=total_pages)

            # Update page progress
            if progress and page_task:
                progress.update(page_task, advance=1)

            # Increment page
            page += 1

            # Break early if there are no more pages
            if page > total_pages:
                break

        except Exception as e:
            if progress and page_task:
                progress.update(page_task, visible=False)
            return country_name, country_id, [], {"error": str(e)}

    # Hide page progress task after completion
    if progress and page_task:
        progress.update(page_task, visible=False)

    # Process review data for statistics
    for review in country_reviews:
        # Track ratings
        rating = review.get("rating")
        if rating and 1 <= rating <= 5:
            rating_stats[rating] += 1

        # Track languages
        language = review.get("detected_language")
        if language:
            language_stats[language] = language_stats.get(language, 0) + 1

    stats = {
        "count": len(country_reviews),
        "language_stats": language_stats,
        "rating_stats": rating_stats,
    }

    return country_name, country_id, country_reviews, stats


def pull_all_markets_reviews(app_id, days=365, max_workers=5):
    """
    Pull reviews from all markets in parallel for specified days.

    Args:
        app_id: AppBot app ID
        days: Number of days back to fetch reviews
        max_workers: Maximum number of parallel worker threads
    """
    # Display header
    display_header(f"REVIEW DATA COLLECTION - APP ID: {app_id}")

    with TimedOperation("Initializing AppBot client"):
        client = AppBotClient()

    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    display_section(f"Date Range: {start_date} to {end_date} ({days} days)")

    # Get all countries
    countries = get_all_countries(client, app_id)

    # Create output directory
    output_dir = Path(__file__).parent / "all_markets_data"
    output_dir.mkdir(exist_ok=True)
    display_info(f"Output directory: {output_dir}")

    # Prepare for reviews collection
    all_reviews = []
    total_per_country = {}
    language_stats = {}
    rating_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # Display parallel processing info
    display_section(f"Parallel Processing with {max_workers} workers")
    display_info(f"Processing {len(countries)} countries in parallel batches")

    # Setup progress bars - using a single progress instance for all tasks
    with create_progress() as progress:
        # Create overall country progress task
        country_task = progress.add_task(
            "[bold green]Countries progress", total=len(countries)
        )

        # Process countries in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a client for each worker to avoid thread safety issues
            clients = [AppBotClient() for _ in range(max_workers)]

            # Create futures for each country batch
            country_batches = [
                countries[i : i + max_workers]
                for i in range(0, len(countries), max_workers)
            ]

            # Process countries in batches to show progress effectively
            for batch_num, batch in enumerate(country_batches):
                display_info(
                    f"Processing batch {batch_num+1}/{len(country_batches)} ({len(batch)} countries)"
                )

                # Submit all countries in this batch to the thread pool
                future_to_country = {
                    executor.submit(
                        fetch_country_reviews,
                        clients[
                            i % max_workers
                        ],  # Use different client for each worker
                        app_id,
                        country,
                        start_date,
                        end_date,
                        progress,  # Pass progress for UI updates
                    ): country
                    for i, country in enumerate(batch)
                }

                review_rate_start = time.time()
                batch_reviews = 0

                # Process completed futures as they arrive
                for future in concurrent.futures.as_completed(future_to_country):
                    country = future_to_country[future]
                    country_name = country["name"]
                    country_id = country["id"]

                    try:
                        # Get results from the future
                        country_name, country_id, country_reviews, stats = (
                            future.result()
                        )

                        # Track statistics
                        if country_reviews:
                            display_success(
                                f"Fetched {len(country_reviews)} reviews for {country_name}"
                            )

                            # Update statistics
                            total_per_country[country_name] = len(country_reviews)
                            all_reviews.extend(country_reviews)
                            batch_reviews += len(country_reviews)

                            # Merge language stats
                            for lang, count in stats["language_stats"].items():
                                language_stats[lang] = (
                                    language_stats.get(lang, 0) + count
                                )

                            # Merge rating stats
                            for rating, count in stats["rating_stats"].items():
                                rating_stats[rating] += count

                            # Save progress to a temporary file
                            temp_output = {
                                "app_id": app_id,
                                "country": country_name,
                                "country_id": country_id,
                                "start_date": start_date,
                                "end_date": end_date,
                                "total_count": len(country_reviews),
                                "results": country_reviews,
                            }

                            country_file = (
                                output_dir
                                / f"reviews_{app_id}_{country_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            )
                            with open(country_file, "w", encoding="utf-8") as f:
                                json.dump(temp_output, f, indent=2, ensure_ascii=False)

                            display_success(
                                f"Saved {len(country_reviews)} reviews to {country_file.name}"
                            )
                        else:
                            display_warning(f"No reviews found for {country_name}")

                        # Calculate and show review rate
                        elapsed = time.time() - review_rate_start
                        if elapsed > 5:  # Update rate calculation every 5 seconds
                            reviews_per_minute = batch_reviews / (elapsed / 60)
                            if reviews_per_minute > 0:
                                display_info(
                                    f"Current rate: {reviews_per_minute:.1f} reviews/minute"
                                )
                                review_rate_start = time.time()
                                batch_reviews = 0

                    except Exception as e:
                        display_error(f"Error processing {country_name}: {e}")

                    # Update overall progress
                    progress.update(country_task, advance=1)

    # Display statistics so far
    display_section("Collection Statistics")

    # Country stats
    country_stats_data = [
        {"Country": country, "Reviews": count}
        for country, count in sorted(
            total_per_country.items(), key=lambda x: x[1], reverse=True
        )
    ]
    if country_stats_data:
        display_stats_table("Reviews by Country", country_stats_data)

    # Language stats
    if language_stats:
        language_stats_data = [
            {"Language": lang, "Count": count}
            for lang, count in sorted(
                language_stats.items(), key=lambda x: x[1], reverse=True
            )
        ]
        display_stats_table("Reviews by Language", language_stats_data)

    # Rating stats
    rating_stats_data = [
        {
            "Rating": rating,
            "Count": count,
            "Percentage": f"{count / max(1, len(all_reviews)) * 100:.1f}%",
        }
        for rating, count in sorted(rating_stats.items(), reverse=True)
    ]
    if rating_stats_data:
        display_stats_table("Reviews by Rating", rating_stats_data)

    # Prepare final output data with all reviews
    output = {
        "app_id": app_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_count": len(all_reviews),
        "country_stats": total_per_country,
        "language_stats": language_stats,
        "rating_stats": rating_stats,
        "results": all_reviews,
    }

    # Save to final file
    with TimedOperation("Saving final output file"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"all_markets_reviews_{app_id}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    # Final summary
    summary_text = f"""
    • Total Reviews: {len(all_reviews)}
    • Countries: {len(total_per_country)} (of {len(countries)} available)
    • Languages: {len(language_stats)}
    • Date Range: {start_date} to {end_date} ({days} days)
    • Storage: {output_file}
    """

    display_summary("Collection Complete", summary_text)
    return output_file


def main(
    app_id: str = typer.Argument(..., help="AppBot app ID to fetch reviews for"),
    days: int = typer.Option(365, help="Number of days back to fetch reviews for"),
    workers: int = typer.Option(5, help="Number of parallel worker threads"),
    ios_app: Optional[str] = typer.Option(None, help="iOS app name (for preset IDs)"),
    android_app: Optional[str] = typer.Option(
        None, help="Android app name (for preset IDs)"
    ),
):
    """
    Pull app reviews from all markets for the specified period using parallel processing.
    Enhanced with rich UI for better progress visualization and parallel fetching for improved performance.
    """
    # Preset app IDs
    APP_IDS = {
        "lounge": {"ios": "933184", "android": "1597113"},
        "prive": {"ios": "1135555", "android": "1739848"},
    }

    # Check for app name presets
    if ios_app and ios_app.lower() in APP_IDS:
        app_id = APP_IDS[ios_app.lower()]["ios"]
        display_info(f"Using preset iOS app ID for {ios_app}: {app_id}")
    elif android_app and android_app.lower() in APP_IDS:
        app_id = APP_IDS[android_app.lower()]["android"]
        display_info(f"Using preset Android app ID for {android_app}: {app_id}")

    # Validate workers
    if workers < 1:
        display_warning(f"Invalid worker count: {workers}. Using default (5)")
        workers = 5
    elif workers > 10:
        display_warning("High worker count may cause rate limiting. Capping at 10")
        workers = 10

    # Pull reviews
    try:
        output_file = pull_all_markets_reviews(app_id, days, workers)
        return output_file
    except Exception as e:
        display_error(f"An error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    typer.run(main)
