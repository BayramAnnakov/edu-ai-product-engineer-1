#!/usr/bin/env python3
"""
Script to clean up the all_markets_data and all_markets_analysis directories.
"""

import argparse
import os
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clean up all_markets_data and all_markets_analysis directories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--keep-latest",
        action="store_true",
        help="Keep the latest file in each directory",
    )
    return parser.parse_args()


def get_file_info(directory):
    """Get information about files in a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[yellow]Directory {directory} does not exist[/yellow]")
        return []

    files = list(dir_path.glob("*.json"))
    return files


def cleanup_directory(directory, dry_run=False, keep_latest=False):
    """Clean up files in a directory."""
    files = get_file_info(directory)
    if not files:
        return 0

    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Keep the latest file if requested
    if keep_latest and files:
        files = files[1:]

    with Progress() as progress:
        task = progress.add_task(f"[green]Processing {directory}...", total=len(files))
        for file in files:
            size_mb = file.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            if dry_run:
                console.print(
                    f"Would delete: {file.name} ({size_mb:.2f} MB, modified: {mod_time})"
                )
            else:
                console.print(
                    f"Deleting: {file.name} ({size_mb:.2f} MB, modified: {mod_time})"
                )
                os.remove(file)

            progress.update(task, advance=1)

    return len(files)


def main():
    args = parse_args()

    console.print(
        Panel.fit(
            "[bold blue]App Review Data Cleanup Utility[/bold blue]\n\n"
            f"[{'DRY RUN' if args.dry_run else 'DELETE'} MODE] "
            f"[{'Keeping latest file in each directory' if args.keep_latest else 'Removing all files'}]",
            title="Cleanup Utility",
            subtitle="reviews-fetcher",
        )
    )

    directories = ["all_markets_data", "all_markets_analysis"]

    total_files = 0
    for directory in directories:
        base_dir = Path(__file__).parent
        full_dir = base_dir / directory
        count = cleanup_directory(full_dir, args.dry_run, args.keep_latest)
        total_files += count

    if args.dry_run:
        console.print(
            f"\n[bold yellow]Would have deleted {total_files} files[/bold yellow]"
        )
    else:
        console.print(
            f"\n[bold green]Successfully deleted {total_files} files[/bold green]"
        )


if __name__ == "__main__":
    main()
