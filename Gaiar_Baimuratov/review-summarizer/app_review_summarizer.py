#!/usr/bin/env python3
"""
App Review Summarization Tool

This script ties together all components of the app review summarization tool:
- AppBot client for fetching reviews
- TextRank for extractive summarization
- CrewAI for orchestrating agents
- Configuration management

Run this script to analyze app reviews with both extractive and abstractive summarization.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union

# Import local modules
from config_manager import load_config, validate_config
from text_rank import TextRankSummarizer
from crew_setup import run_crew

# Import AppBot client
try:
    from appbot import AppBotClient
except ImportError:
    print("Error: AppBot client not found. Please install it first.")
    sys.exit(1)

def fetch_app_reviews(
    app_id: Union[str, int],
    days: int = 30,
    limit: int = 500,
    min_rating: int = 1,
    max_rating: int = 5,
) -> List[Dict]:
    """
    Fetch app reviews from AppBot API.
    
    Args:
        app_id: AppBot app ID
        days: Number of days to look back
        limit: Maximum number of reviews to return (default: 500)
        min_rating: Minimum rating filter (1-5)
        max_rating: Maximum rating filter (1-5)
        
    Returns:
        List of review dictionaries
    """
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    print(f"Fetching reviews from {start_date} to {end_date}...")
    
    # Initialize AppBot client
    client = AppBotClient()
    
    # Fetch reviews with pagination (API returns 100 reviews per page)
    reviews = []
    page = 1
    
    while len(reviews) < limit:
        reviews_data = client.get_reviews(
            app_id=app_id,
            start=start_date,
            end=end_date,
            page=page
        )
        
        # Filter and format reviews
        page_results = reviews_data.get("results", [])
        if not page_results:
            # No more results available
            break
            
        for review in page_results:
            rating = review.get("rating")
            
            # Apply rating filter
            if min_rating <= rating <= max_rating:
                reviews.append({
                    "body": review.get("body", ""),
                    "rating": rating,
                    "author": review.get("author"),
                    "date": review.get("date"),
                    "subject": review.get("subject", ""),
                    "version": review.get("version", ""),
                    "country": review.get("country", ""),
                })
            
            # Respect the limit
            if len(reviews) >= limit:
                break
        
        # Move to next page
        page += 1
        
        # If we got fewer results than expected, we've reached the end
        if len(page_results) < 100:
            break
    
    print(f"Fetched {len(reviews)} reviews")
    return reviews

def generate_filename(app_id: str, format: str) -> str:
    """
    Generate a filename for saving the summary.
    
    Args:
        app_id: AppBot app ID
        format: Output format (text, json, markdown)
        
    Returns:
        Filename string
    """
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    extensions = {
        "text": "txt",
        "json": "json",
        "markdown": "md"
    }
    
    ext = extensions.get(format, "txt")
    return f"review_summary_{app_id}_{date_str}.{ext}"

def save_output(output: str, filename: Optional[str] = None, format: str = "text") -> str:
    """
    Save output to a file.
    
    Args:
        output: Output content
        filename: Optional filename
        format: Output format
        
    Returns:
        Path to saved file
    """
    # Generate filename if not provided
    if not filename:
        filename = generate_filename("app", format)
    
    path = Path(filename)
    path.write_text(output)
    
    return str(path)

def main():
    """Main function to run the app review summarization tool."""
    # Load configuration
    config = load_config()
    
    # Validate configuration
    errors = validate_config(config)
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for key, error in errors.items():
            print(f"  {key}: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Get app ID from config or arguments
    app_id = None
    if len(sys.argv) > 1:
        app_id = sys.argv[1]
    else:
        app_id = config.get("appbot_app_id")
    
    if not app_id:
        print("Error: No app ID provided.", file=sys.stderr)
        print("Please specify an app ID as argument or set APPBOT_APP_ID in environment.", file=sys.stderr)
        sys.exit(1)
    
    # Set up parameters
    days = config.get("days", 30)
    limit = config.get("limit", 100)
    min_rating = config.get("min_rating", 1)
    max_rating = config.get("max_rating", 5)
    output_format = config.get("output_format", "text")
    verbose = config.get("verbose", False)
    
    # Fetch reviews
    try:
        print(f"Analyzing app ID: {app_id}")
        reviews = fetch_app_reviews(app_id, days, limit, min_rating, max_rating)
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(reviews)} reviews. Starting analysis...")
    
    if not reviews:
        print("No reviews found matching the criteria.")
        sys.exit(0)
    
    # Run CrewAI pipeline
    try:
        results = run_crew(reviews, verbose=verbose)
    except Exception as e:
        print(f"Error running CrewAI pipeline: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Format output
    if output_format == "json":
        import json
        output = json.dumps(results, indent=2)
    elif output_format == "markdown":
        output = f"# App Review Summary for {app_id}\n\n"
        output += f"*Analysis of {len(reviews)} reviews from the past {days} days*\n\n"
        output += "## Extractive Summary\n\n"
        output += results["extractive_summary"] + "\n\n"
        output += "## Abstractive Summary\n\n"
        output += results["abstractive_summary"] + "\n\n"
        output += "## Comparison Analysis\n\n"
        output += results["comparison"] + "\n\n"
        output += f"*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*"
    else:  # text format
        output = f"APP REVIEW SUMMARY FOR {app_id}\n"
        output += f"Analysis of {len(reviews)} reviews from the past {days} days\n\n"
        output += "EXTRACTIVE SUMMARY:\n"
        output += results["extractive_summary"] + "\n\n"
        output += "ABSTRACTIVE SUMMARY:\n"
        output += results["abstractive_summary"] + "\n\n"
        output += "COMPARISON:\n"
        output += results["comparison"] + "\n\n"
        output += f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
    
    # Save or display output
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        filepath = save_output(output, output_file, output_format)
        print(f"Summary saved to: {filepath}")
    else:
        print("\n" + output)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()