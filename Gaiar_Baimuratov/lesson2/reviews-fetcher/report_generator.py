#!/usr/bin/env python3
"""
Report generator for batch interview results.

This module generates consolidated reports from multiple interview transcripts
created by the batch_interviews.py process.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("report_generator")


def parse_transcript(transcript_path: str) -> Dict[str, Any]:
    """
    Parse an interview transcript to extract key information

    Args:
        transcript_path: Path to the transcript markdown file

    Returns:
        Dictionary with extracted information
    """
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract topic from header
        topic_match = re.search(r"# Interview Transcript: (.*?)\n", content)
        topic = topic_match.group(1) if topic_match else "Unknown Topic"

        # Extract decision (GO/NO-GO)
        decision_match = re.search(r"\*\*Decision: (.*?)\*\*", content)
        decision = decision_match.group(1) if decision_match else "UNKNOWN"

        # Extract market perspective
        perspective_match = re.search(
            r"## Market Perspective\n\n(.*?)\n\n##", content, re.DOTALL
        )
        perspective = perspective_match.group(1).strip() if perspective_match else ""

        # Extract key rationale points
        rationale_section = re.search(
            r"## Key Rationale\n\n(.*?)\n\n##", content, re.DOTALL
        )
        rationale = []
        if rationale_section:
            rationale_text = rationale_section.group(1)
            rationale = [
                point.strip().lstrip("- ")
                for point in rationale_text.split("\n")
                if point.strip()
            ]

        # Extract persona sentiments
        persona_sections = re.findall(
            r"### (.*?) - (.*?)\n\n\*\*Summary:\*\* (.*?)\n\n\*\*Key Points:\*\*\n((?:- .*?\n)*)",
            content,
        )
        personas = []
        for name, sentiment, summary, points_text in persona_sections:
            points = [
                point.strip().lstrip("- ")
                for point in points_text.split("\n")
                if point.strip()
            ]
            personas.append(
                {
                    "name": name,
                    "sentiment": sentiment,
                    "summary": summary,
                    "key_points": points,
                }
            )

        return {
            "topic": topic,
            "decision": decision,
            "market_perspective": perspective,
            "rationale": rationale,
            "personas": personas,
            "transcript_path": transcript_path,
        }

    except Exception as e:
        logger.error(f"Error parsing transcript {transcript_path}: {e}")
        return {
            "topic": "Error parsing transcript",
            "decision": "ERROR",
            "market_perspective": f"Error: {str(e)}",
            "rationale": [],
            "personas": [],
            "transcript_path": transcript_path,
            "error": str(e),
        }


def generate_consolidated_report(
    transcripts_dir: str,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a consolidated report from multiple interview transcripts

    Args:
        transcripts_dir: Directory containing interview transcripts
        output_file: Path to save the consolidated report

    Returns:
        Dictionary with consolidated report data
    """
    # Find all transcript files
    transcript_files = list(Path(transcripts_dir).glob("*.md"))
    if not transcript_files:
        logger.warning(f"No transcript files found in {transcripts_dir}")
        return {"error": f"No transcript files found in {transcripts_dir}"}

    logger.info(f"Found {len(transcript_files)} transcript files")

    # Parse each transcript
    transcript_data = []
    for file_path in transcript_files:
        logger.info(f"Parsing transcript: {file_path}")
        data = parse_transcript(str(file_path))
        transcript_data.append(data)

    # Count decisions
    go_count = sum(1 for data in transcript_data if data["decision"] == "GO")
    no_go_count = sum(1 for data in transcript_data if data["decision"] == "NO-GO")
    unknown_count = len(transcript_data) - go_count - no_go_count

    # Generate consolidated report
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_features": len(transcript_data),
        "decision_summary": {
            "GO": go_count,
            "NO-GO": no_go_count,
            "UNKNOWN": unknown_count,
        },
        "features": transcript_data,
    }

    # Generate unique persona stats
    persona_stats = {}
    for data in transcript_data:
        for persona in data["personas"]:
            name = persona["name"]
            sentiment = persona["sentiment"]
            if name not in persona_stats:
                persona_stats[name] = {
                    "POSITIVE": 0,
                    "NEUTRAL": 0,
                    "NEGATIVE": 0,
                    "UNKNOWN": 0,
                }

            persona_stats[name][
                (
                    sentiment
                    if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]
                    else "UNKNOWN"
                )
            ] += 1

    report["persona_stats"] = persona_stats

    # Save to file if specified
    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved consolidated report to {output_file}")

    return report


def generate_markdown_report(report_data: Dict[str, Any], output_file: str) -> None:
    """
    Generate a markdown report from consolidated report data

    Args:
        report_data: Consolidated report data
        output_file: Path to save the markdown report
    """
    timestamp = report_data["timestamp"]
    total_features = report_data["total_features"]
    decision_summary = report_data["decision_summary"]
    features = report_data["features"]
    persona_stats = report_data["persona_stats"]

    # Start building the markdown
    markdown = "# Feature Interview Analysis Report\n\n"
    markdown += f"**Generated:** {timestamp}\n\n"
    markdown += "## Executive Summary\n\n"
    markdown += f"Total features analyzed: **{total_features}**\n\n"
    markdown += "### Decision Summary\n\n"
    markdown += f"- GO: {decision_summary['GO']} ({decision_summary['GO']/total_features*100:.1f}%)\n"
    markdown += f"- NO-GO: {decision_summary['NO-GO']} ({decision_summary['NO-GO']/total_features*100:.1f}%)\n"
    if decision_summary["UNKNOWN"] > 0:
        markdown += f"- UNKNOWN: {decision_summary['UNKNOWN']} ({decision_summary['UNKNOWN']/total_features*100:.1f}%)\n"

    markdown += "\n## Persona Sentiment Analysis\n\n"

    # Add persona stats table
    markdown += "| Persona | Positive | Neutral | Negative | Total |\n"
    markdown += "|---------|----------|---------|----------|-------|\n"

    for name, stats in persona_stats.items():
        total = (
            stats["POSITIVE"] + stats["NEUTRAL"] + stats["NEGATIVE"] + stats["UNKNOWN"]
        )
        markdown += f"| {name} | {stats['POSITIVE']} | {stats['NEUTRAL']} | {stats['NEGATIVE']} | {total} |\n"

    # Add feature summary table
    markdown += "\n## Feature Decision Summary\n\n"
    markdown += "| Feature | Decision | Market Perspective |\n"
    markdown += "|---------|----------|-------------------|\n"

    for feature in sorted(
        features, key=lambda x: (0 if x["decision"] == "GO" else 1, x["topic"])
    ):
        # Truncate market perspective if too long
        perspective = (
            feature["market_perspective"][:150] + "..."
            if len(feature["market_perspective"]) > 150
            else feature["market_perspective"]
        )
        markdown += (
            f"| {feature['topic']} | **{feature['decision']}** | {perspective} |\n"
        )

    # Add detailed feature sections
    markdown += "\n## Feature Details\n\n"

    for feature in features:
        markdown += f"### {feature['topic']}\n\n"
        markdown += f"**Decision: {feature['decision']}**\n\n"
        markdown += f"**Market Perspective:**\n{feature['market_perspective']}\n\n"

        markdown += "**Key Rationale:**\n"
        for point in feature["rationale"]:
            markdown += f"- {point}\n"

        markdown += "\n**Persona Feedback:**\n\n"
        for persona in feature["personas"]:
            markdown += f"- **{persona['name']} ({persona['sentiment']})**: {persona['summary']}\n"

        markdown += (
            f"\n[Full Transcript]({os.path.basename(feature['transcript_path'])})\n\n"
        )
        markdown += "---\n\n"

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"Saved markdown report to {output_file}")


def main():
    """Main entry point for the report generator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate consolidated report from interview transcripts"
    )
    parser.add_argument(
        "transcripts_dir", help="Directory containing interview transcripts"
    )
    parser.add_argument(
        "--output-json",
        "-j",
        help="Path to save the consolidated JSON report",
        default=None,
    )
    parser.add_argument(
        "--output-markdown", "-m", help="Path to save the markdown report", default=None
    )

    args = parser.parse_args()

    # Generate default filenames if not provided
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output_json is None:
        args.output_json = f"consolidated_report_{timestamp}.json"
    if args.output_markdown is None:
        args.output_markdown = f"consolidated_report_{timestamp}.md"

    # Generate the reports
    report_data = generate_consolidated_report(args.transcripts_dir, args.output_json)
    generate_markdown_report(report_data, args.output_markdown)

    print("\nReport Generation Complete:")
    print(f"- JSON report: {args.output_json}")
    print(f"- Markdown report: {args.output_markdown}")
    print(f"- Total features: {report_data['total_features']}")
    print(f"- GO decisions: {report_data['decision_summary']['GO']}")
    print(f"- NO-GO decisions: {report_data['decision_summary']['NO-GO']}")


if __name__ == "__main__":
    main()
