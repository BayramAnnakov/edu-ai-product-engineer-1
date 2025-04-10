"""
Examples of using the AppBot client.
"""
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from appbot import AppBotClient

# Load environment variables
load_dotenv()


def get_token_info():
    """Get token information."""
    client = AppBotClient()
    result = client.get_token_info()
    print("Token Info:")
    print(f"  API Key: {result.get('api_key')}")
    print(f"  Description: {result.get('desc')}")
    print(f"  Team ID: {result.get('team')}")


def list_apps():
    """List all apps associated with the team."""
    client = AppBotClient()
    apps = client.get_apps()
    
    print("Available Apps:")
    for app in apps:
        print(f"  {app.get('name')} (ID: {app.get('id')}, Store: {app.get('store')})")
    
    return apps


def get_app_reviews(app_id=None):
    """Get recent reviews for an app."""
    # Use app_id from environment if not provided
    app_id = app_id or os.environ.get("APPBOT_APP_ID")
    if not app_id:
        print("No app ID provided. Please set APPBOT_APP_ID in .env or provide as argument.")
        return
    
    # Calculate dates for the last week
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    client = AppBotClient()
    reviews = client.get_reviews(app_id=app_id, start=start_date, end=end_date)
    
    print(f"Recent Reviews (from {start_date} to {end_date}):")
    print(f"  Total reviews: {reviews.get('total_count')}")
    
    for review in reviews.get("results", [])[:5]:  # Show first 5 reviews
        print(f"\n  Review by {review.get('author')} ({review.get('rating')} stars):")
        print(f"  {review.get('subject')}")
        print(f"  {review.get('body')[:100]}..." if len(review.get('body', '')) > 100 else review.get('body', ''))


def get_sentiment_analysis(app_id=None):
    """Get sentiment analysis for an app."""
    # Use app_id from environment if not provided
    app_id = app_id or os.environ.get("APPBOT_APP_ID")
    if not app_id:
        print("No app ID provided. Please set APPBOT_APP_ID in .env or provide as argument.")
        return
    
    # Calculate dates for the last month
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    client = AppBotClient()
    breakdown = client.get_sentiment_breakdown(app_id=app_id, start=start_date, end=end_date)
    
    print(f"Sentiment Breakdown (from {start_date} to {end_date}):")
    results = breakdown.get("results", {})
    total = sum(results.values())
    
    if total > 0:
        print(f"  Positive: {results.get('positive', 0)} ({results.get('positive', 0)/total*100:.1f}%)")
        print(f"  Negative: {results.get('negative', 0)} ({results.get('negative', 0)/total*100:.1f}%)")
        print(f"  Neutral: {results.get('neutral', 0)} ({results.get('neutral', 0)/total*100:.1f}%)")
        print(f"  Mixed: {results.get('mixed', 0)} ({results.get('mixed', 0)/total*100:.1f}%)")
    else:
        print("  No sentiment data available for this period.")


def get_popular_topics(app_id=None):
    """Get popular words for an app."""
    # Use app_id from environment if not provided
    app_id = app_id or os.environ.get("APPBOT_APP_ID")
    if not app_id:
        print("No app ID provided. Please set APPBOT_APP_ID in .env or provide as argument.")
        return
    
    # Calculate dates for the last month
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    client = AppBotClient()
    words = client.get_popular_words(app_id=app_id, start=start_date, end=end_date)
    
    print(f"Popular Words (from {start_date} to {end_date}):")
    for word in words.get("results", [])[:10]:  # Show top 10 words
        print(f"  '{word.get('word')}' - mentioned {word.get('counter')} times")
        print(f"    (positive: {word.get('positive')}, negative: {word.get('negative')})")


def main():
    """Run example functions."""
    print("\n1. Token Information:")
    get_token_info()
    
    print("\n2. App Listing:")
    apps = list_apps()
    
    if not apps:
        print("No apps found. Please check your API credentials.")
        return
    
    app_id = os.environ.get("APPBOT_APP_ID")
    if not app_id and apps:
        # Use the first app if no app_id is specified in .env
        app_id = apps[0].get('id')
        print(f"\nUsing app ID {app_id} for examples.")
    
    print("\n3. Recent Reviews:")
    get_app_reviews(app_id)
    
    print("\n4. Sentiment Analysis:")
    get_sentiment_analysis(app_id)
    
    print("\n5. Popular Topics:")
    get_popular_topics(app_id)


if __name__ == "__main__":
    main()