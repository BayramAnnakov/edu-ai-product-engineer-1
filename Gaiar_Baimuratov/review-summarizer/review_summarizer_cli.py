#!/usr/bin/env python3
"""
CLI for app review summarization using CrewAI and AppBot.
This is the main entry point for the review summarization tool.
"""
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from appbot import AppBotClient

# Load environment variables
load_dotenv()

# Initialize Typer app
app = typer.Typer(
    help="App Review Summarization using CrewAI and AppBot",
    add_completion=False,
)
console = Console()

class OutputFormat(str, Enum):
    """Output format options."""
    text = "text"
    json = "json"
    markdown = "markdown"

@app.callback()
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode (very verbose)"),
):
    """Common options for all commands."""
    # Initialize the context object
    ctx.obj = {
        "verbose": verbose,
        "debug": debug,
        "console": console,
    }

@app.command("summarize")
def summarize(
    ctx: typer.Context,
    app_id: Optional[str] = typer.Option(
        None, "--app-id", "-a", help="AppBot application ID"
    ),
    days: int = typer.Option(90, "--days", "-d", help="Number of days of reviews to analyze"),
    limit: int = typer.Option(500, "--limit", "-l", help="Maximum number of reviews to process"),
    min_rating: int = typer.Option(
        1, "--min-rating", "-m", help="Minimum rating (1-5 stars)"
    ),
    max_rating: int = typer.Option(
        5, "--max-rating", "-M", help="Maximum rating (1-5 stars)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.text, "--format", "-f", help="Output format"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """
    Summarize app reviews using extractive and abstractive techniques,
    then compare the results.
    """
    console = ctx.obj["console"]
    verbose = ctx.obj["verbose"]
    
    # Use app_id from environment if not provided
    app_id = app_id or os.environ.get("APPBOT_APP_ID")
    if not app_id:
        console.print("[bold red]Error:[/] No app_id provided. Use --app-id or set APPBOT_APP_ID environment variable.")
        raise typer.Exit(code=1)
    
    # Validate rating range
    if min_rating < 1 or min_rating > 5 or max_rating < 1 or max_rating > 5 or min_rating > max_rating:
        console.print("[bold red]Error:[/] Invalid rating range. Min rating must be 1-5, max rating must be min_rating-5.")
        raise typer.Exit(code=1)
    
    # Display run parameters in verbose mode
    if verbose:
        console.print(f"[bold blue]App ID:[/] {app_id}")
        console.print(f"[bold blue]Time range:[/] {days} days")
        console.print(f"[bold blue]Review limit:[/] {limit}")
        console.print(f"[bold blue]Rating range:[/] {min_rating}-{max_rating} stars")
    
    # Initialize AppBot client
    try:
        client = AppBotClient()
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(code=1)
    
    # Fetch reviews
    with console.status(f"Fetching up to {limit} reviews from the past {days} days..."):
        reviews = fetch_reviews(client, app_id, days, limit, min_rating, max_rating)
    
    if not reviews:
        console.print("[bold yellow]Warning:[/] No reviews found for the specified criteria.")
        raise typer.Exit(code=0)
    
    console.print(f"Found [bold green]{len(reviews)}[/] reviews. Running summarization pipeline...")
    
    # Run CrewAI pipeline
    try:
        from crew_setup import run_crew
        results = run_crew(reviews, verbose=ctx.obj["verbose"])
        
        # Format output
        result = {
            "extractive_summary": results["extractive_summary"],
            "abstractive_summary": results["abstractive_summary"],
            "comparison": results["comparison"],
        }
    except Exception as e:
        console.print(f"[bold red]Error running summarization pipeline:[/] {str(e)}")
        raise typer.Exit(code=1)
    
    output = format_output(result, output_format)
    
    # Write output to file or display
    if output_file:
        try:
            # Ensure parent directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output)
            console.print(f"Summary written to [bold green]{output_file}[/]")
        except Exception as e:
            console.print(f"[bold red]Error writing to file:[/] {str(e)}")
            raise typer.Exit(code=1)
    else:
        console.print(output)


@app.command("list-apps")
def list_apps(ctx: typer.Context):
    """List all apps accessible with your AppBot API credentials."""
    console = ctx.obj["console"]
    
    # Initialize AppBot client
    try:
        client = AppBotClient()
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(code=1)
    
    # Fetch apps
    with console.status("Fetching apps..."):
        try:
            apps = client.get_apps()
        except Exception as e:
            console.print(f"[bold red]Error fetching apps:[/] {str(e)}")
            raise typer.Exit(code=1)
    
    if not apps:
        console.print("No apps found. Please check your API credentials.")
        raise typer.Exit(code=0)
    
    # Display apps
    console.print("[bold]Available Apps:[/]")
    for app in apps:
        console.print(f"  [bold green]{app.get('name')}[/] (ID: {app.get('id')}, Store: {app.get('store')})")


def fetch_reviews(
    client: AppBotClient, 
    app_id: Union[str, int], 
    days: int, 
    limit: int,
    min_rating: int = 1,
    max_rating: int = 5
) -> List[dict]:
    """
    Fetch reviews from AppBot API.
    
    Args:
        client: AppBot API client
        app_id: ID of the app to fetch reviews for
        days: Number of days to look back
        limit: Maximum number of reviews to fetch
        min_rating: Minimum rating (1-5 stars)
        max_rating: Maximum rating (1-5 stars)
        
    Returns:
        List of review dictionaries
    """
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Fetch reviews with pagination (API returns 100 reviews per page)
    reviews = []
    page = 1
    
    while len(reviews) < limit:
        reviews_data = client.get_reviews(
            app_id=app_id, 
            start=start_date, 
            end=end_date,
            page=page,
            dlangs=["de"]  # German language
        )
        
        # Filter by rating
        page_results = reviews_data.get("results", [])
        if not page_results:
            # No more results available
            break
            
        for review in page_results:
            rating = review.get("rating")
            if min_rating <= rating <= max_rating:
                reviews.append({
                    "body": review.get("body", ""),
                    "rating": rating,
                    "author": review.get("author"),
                    "date": review.get("date"),
                    "subject": review.get("subject", ""),
                })
            
            if len(reviews) >= limit:
                break
                
        # Move to next page
        page += 1
        
        # If we got fewer results than expected, we've reached the end
        if len(page_results) < 100:
            break
    
    reviews_data = client.get_reviews(
        app_id=app_id, 
        start=start_date, 
        end=end_date,
        page=1,
        dlangs=["de"]  # German language
    )
    total_count = reviews_data.get('total_count', 0)
    print(f"Total reviews available: {total_count}")
    
    return reviews


def format_output(result: dict, format_type: OutputFormat) -> str:
    """
    Format the summarization results based on output format.
    
    Args:
        result: Dictionary with summary results
        format_type: Output format type
        
    Returns:
        Formatted string output
    """
    if format_type == OutputFormat.json:
        import json
        return json.dumps(result, indent=2)
    
    elif format_type == OutputFormat.markdown:
        md = "# App Review Summary\n\n"
        md += "## Extractive Summary\n\n"
        md += result["extractive_summary"] + "\n\n"
        md += "## Abstractive Summary\n\n"
        md += result["abstractive_summary"] + "\n\n"
        md += "## Comparison Analysis\n\n"
        md += result["comparison"] + "\n\n"
        return md
    
    else:  # Plain text
        return f"EXTRACTIVE SUMMARY:\n{result['extractive_summary']}\n\n" + \
               f"ABSTRACTIVE SUMMARY:\n{result['abstractive_summary']}\n\n" + \
               f"COMPARISON:\n{result['comparison']}"


if __name__ == "__main__":
    app()