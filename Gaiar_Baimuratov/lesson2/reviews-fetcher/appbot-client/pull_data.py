#!/usr/bin/env python3
"""
Script to pull and save data from AppBot API.
"""
import argparse
import csv
import json
import os
from datetime import datetime, timedelta

from appbot import AppBotClient


def save_to_json(data, filename):
    """
    Save data to a JSON file.

    Args:
        data: Data to save.
        filename: Name of the file to save to.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")


def save_reviews_to_csv(reviews, filename):
    """
    Save reviews to a CSV file.

    Args:
        reviews: Reviews data from the API.
        filename: Name of the file to save to.
    """
    if not reviews.get("results"):
        print("No reviews found.")
        return

    # Extract keys from first review for headers
    fieldnames = reviews["results"][0].keys()

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews["results"])

    print(f"Reviews saved to {filename}")


def pull_reviews(app_id, start_date, end_date, output_format="json"):
    """
    Pull reviews for an app.

    Args:
        app_id: ID of the app to pull reviews for.
        start_date: Start date for reviews (YYYY-MM-DD).
        end_date: End date for reviews (YYYY-MM-DD).
        output_format: Format to save reviews in ('json' or 'csv').
    """
    client = AppBotClient()

    print(f"Pulling reviews for app {app_id} from {start_date} to {end_date}...")

    # Pull reviews (handling pagination if needed)
    all_reviews = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        reviews = client.get_reviews(
            app_id=app_id, start=start_date, end=end_date, page=page
        )

        all_reviews.extend(reviews.get("results", []))
        total_pages = reviews.get("total_pages", 1)
        print(
            f"Fetched page {page} of {total_pages} ({len(reviews.get('results', []))} reviews)"
        )

        # Break if we reached the last page
        if page >= total_pages:
            break

        page += 1

    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Prepare output data
    output = {
        "app_id": app_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_count": len(all_reviews),
        "results": all_reviews,
    }

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_format == "json":
        save_to_json(output, f"results/reviews_{app_id}_{timestamp}.json")
    else:  # csv
        save_reviews_to_csv(output, f"results/reviews_{app_id}_{timestamp}.csv")


def pull_sentiment(app_id, start_date, end_date):
    """
    Pull sentiment data for an app.

    Args:
        app_id: ID of the app to pull sentiment for.
        start_date: Start date for sentiment (YYYY-MM-DD).
        end_date: End date for sentiment (YYYY-MM-DD).
    """
    client = AppBotClient()

    print(f"Pulling sentiment data for app {app_id} from {start_date} to {end_date}...")

    # Pull sentiment breakdown
    sentiment = client.get_sentiment_breakdown(
        app_id=app_id, start=start_date, end=end_date
    )

    # Pull sentiment timeline
    timeline = client.get_sentiment_timeline(
        app_id=app_id, start=start_date, end=end_date, force_daily=True
    )

    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save breakdown
    save_to_json(sentiment, f"results/sentiment_breakdown_{app_id}_{timestamp}.json")

    # Save timeline
    save_to_json(timeline, f"results/sentiment_timeline_{app_id}_{timestamp}.json")


def pull_popular_words(app_id, start_date, end_date):
    """
    Pull popular words for an app.

    Args:
        app_id: ID of the app to pull words for.
        start_date: Start date for words (YYYY-MM-DD).
        end_date: End date for words (YYYY-MM-DD).
    """
    client = AppBotClient()

    print(f"Pulling popular words for app {app_id} from {start_date} to {end_date}...")

    # Pull popular words
    popular_words = client.get_popular_words(
        app_id=app_id, start=start_date, end=end_date
    )

    # Pull critical words
    critical_words = client.get_critical_words(
        app_id=app_id, start=start_date, end=end_date
    )

    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save popular words
    save_to_json(popular_words, f"results/popular_words_{app_id}_{timestamp}.json")

    # Save critical words
    save_to_json(critical_words, f"results/critical_words_{app_id}_{timestamp}.json")


def list_available_apps():
    """List all available apps."""
    client = AppBotClient()
    apps = client.get_apps()

    print("Available Apps:")
    for app in apps:
        print(f"  {app.get('name')} (ID: {app.get('id')}, Store: {app.get('store')})")

    # Save to file
    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_to_json(apps, f"results/apps_list_{timestamp}.json")


def main():
    """Main function to parse arguments and pull data."""
    parser = argparse.ArgumentParser(description="Pull data from AppBot API")
    parser.add_argument("--list-apps", action="store_true", help="List available apps")
    parser.add_argument("--app-id", type=str, help="App ID to pull data for")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to pull data for (default: 30)",
    )
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--reviews", action="store_true", help="Pull reviews data")
    parser.add_argument("--sentiment", action="store_true", help="Pull sentiment data")
    parser.add_argument("--words", action="store_true", help="Pull popular words data")
    parser.add_argument(
        "--output-format",
        choices=["json", "csv"],
        default="json",
        help="Output format for reviews (default: json)",
    )

    args = parser.parse_args()

    # List apps and exit if --list-apps is specified
    if args.list_apps:
        list_available_apps()
        return

    # Check if app_id is provided
    if not args.app_id:
        app_id = os.environ.get("APPBOT_APP_ID")
        if not app_id:
            print(
                "Error: No app ID provided. Please specify --app-id or set APPBOT_APP_ID in .env"
            )
            return
    else:
        app_id = args.app_id

    # Calculate dates
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    # Pull data based on specified options
    if not (args.reviews or args.sentiment or args.words):
        # If no specific data type is specified, pull all
        pull_reviews(app_id, start_date, end_date, args.output_format)
        pull_sentiment(app_id, start_date, end_date)
        pull_popular_words(app_id, start_date, end_date)
    else:
        if args.reviews:
            pull_reviews(app_id, start_date, end_date, args.output_format)
        if args.sentiment:
            pull_sentiment(app_id, start_date, end_date)
        if args.words:
            pull_popular_words(app_id, start_date, end_date)


if __name__ == "__main__":
    main()
