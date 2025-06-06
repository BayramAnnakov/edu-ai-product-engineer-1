"""
UI utilities for rich terminal output and progress tracking.
"""

import time
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)
from rich.table import Table
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text

# Initialize console
console = Console()

# Styling constants
HEADER_STYLE = "bold cyan on dark_blue"
SUCCESS_STYLE = "bold green"
ERROR_STYLE = "bold white on red"
WARNING_STYLE = "bold yellow"
INFO_STYLE = "blue"
HIGHLIGHT_STYLE = "bold magenta"


def display_header(title: str) -> None:
    """Display a styled header."""
    console.print("\n")
    console.print(
        Panel(
            Text(title.upper(), style="bold white", justify="center"),
            style=HEADER_STYLE,
            expand=True,
        )
    )


def display_section(title: str) -> None:
    """Display a section header."""
    console.print(f"\n[{HIGHLIGHT_STYLE}]{title}[/{HIGHLIGHT_STYLE}]")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[{SUCCESS_STYLE}]✓ {message}[/{SUCCESS_STYLE}]")


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[{ERROR_STYLE}]ERROR: {message}[/{ERROR_STYLE}]")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[{WARNING_STYLE}]⚠ {message}[/{WARNING_STYLE}]")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[{INFO_STYLE}]ℹ {message}[/{INFO_STYLE}]")


def create_progress() -> Progress:
    """Create a rich progress bar."""
    # Prevent multiple live displays by using the already created console
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,  # Use the same console instance
    )


def display_stats_table(title: str, data: List[Dict[str, Any]]) -> None:
    """Display a table of statistics."""
    if not data:
        display_warning(f"No data available for {title}")
        return

    if not isinstance(data[0], dict):
        display_warning(f"Invalid data format for table {title}")
        return

    # Create table with columns from the keys of the first item
    table = Table(title=title, show_header=True, header_style="bold blue")
    columns = list(data[0].keys())

    for column in columns:
        table.add_column(column)

    # Add rows
    for item in data:
        table.add_row(*[str(item[col]) for col in columns])

    console.print(table)


def display_json_pretty(data: Any, title: Optional[str] = None) -> None:
    """Display JSON data in a pretty format."""
    if title:
        display_section(title)

    console.print(Pretty(data, expand_all=False))


def display_code(code: str, language: str = "python") -> None:
    """Display code with syntax highlighting."""
    console.print(Syntax(code, language, theme="monokai"))


def display_markdown(markdown_text: str) -> None:
    """Display markdown formatted text."""
    console.print(Markdown(markdown_text))


def display_summary(title: str, summary_text: str) -> None:
    """Display a summary panel."""
    console.print("\n")
    console.print(
        Panel(
            Text(summary_text, style="white"),
            title=title,
            title_align="center",
            border_style=HIGHLIGHT_STYLE,
            expand=True,
        )
    )


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def generate_llm_summary(data: Dict[str, Any], openai_client) -> str:
    """Generate a summary of analysis results using GPT-4o."""
    # Prepare a simplified version of the data
    try:
        summary_prompt = f"""
        I have analyzed app reviews and extracted the following information:
        
        App ID: {data.get('app_id', 'unknown')}
        Date Range: {data.get('start_date', 'unknown')} to {data.get('end_date', 'unknown')}
        Total Reviews: {data.get('total_count', 0)}
        
        Countries: {', '.join(list(data.get('country_stats', {}).keys())[:5])} 
        {f'and {len(data.get("country_stats", {})) - 5} more' if len(data.get('country_stats', {})) > 5 else ''}
        
        Feature Requests: {data.get('feature_count', 0)} unique features extracted from {data.get('raw_feature_count', 0)} mentions
        
        Top Features:
        {chr(10).join([f"- {feature}" for feature in data.get('top_features', [])[:5]])}
        
        Please provide a 3-4 sentence executive summary of these review analysis results.
        Keep it concise but informative, focusing on the most important insights.
        """

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst summarizing app review analysis results.",
                },
                {"role": "user", "content": summary_prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Failed to generate summary: {str(e)}"


class TimedOperation:
    """Context manager for timing operations."""

    def __init__(self, description: str, console: Optional[Console] = None):
        self.description = description
        self.console = console or globals()["console"]

    def __enter__(self):
        self.start = time.time()
        self.console.print(f"[bold blue]Starting: {self.description}...[/bold blue]")
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        self.console.print(
            f"[bold green]Completed: {self.description} in {format_duration(elapsed)}[/bold green]"
        )
