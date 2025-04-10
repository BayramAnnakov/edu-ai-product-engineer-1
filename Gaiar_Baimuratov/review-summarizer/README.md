# App Review Summarization Agent

A Python application that uses AI to summarize and analyze app reviews from the AppBot API. The system combines a deterministic extractive summarizer (NLP-based TextRank) with a probabilistic abstractive summarizer (LLM-based), and uses a third agent to compare their outputs.

## Overview

This tool helps mobile app developers and product managers quickly understand user feedback by:

1. Fetching app reviews from the AppBot API
2. Generating an extractive summary using TextRank algorithm (pulls key sentences from reviews)
3. Creating an abstractive summary using OpenAI's GPT-4o (rewrites content in a coherent way)
4. Comparing both summaries with OpenAI's o1 model to evaluate their strengths and weaknesses

The system uses CrewAI to orchestrate specialized AI agents that work together to produce high-quality summaries of user feedback.

## Features

- **AppBot API Integration**: Fetches app reviews with filtering by date range and star rating
- **Extractive Summarization**: Uses TextRank algorithm to identify key sentences from reviews
- **Abstractive Summarization**: Uses OpenAI's GPT-4o to generate cohesive summaries
- **Summary Comparison**: Evaluates both summary types using OpenAI's o1 model
- **Multiple Output Formats**: Supports text, JSON, and markdown output
- **CLI Interface**: User-friendly command-line interface with comprehensive options

## Requirements

- Python 3.10 or higher
- AppBot API credentials (username and password)
- OpenAI API key with access to GPT-4o and o1 models
- Required Python packages (see Installation section)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/app-review-summarizer.git
   cd app-review-summarizer
   ```

2. Create and activate a Python 3.10 virtual environment:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the AppBot client:
   ```bash
   pip install -e ./appbot-client
   ```

5. Create a `.env` file with your API credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Configuration

Create a `.env` file with the following variables:

```
APPBOT_API_USERNAME=your_appbot_username
APPBOT_API_PASSWORD=your_appbot_password
APPBOT_APP_ID=optional_default_app_id
OPENAI_API_KEY=your_openai_api_key
```

Optional configuration variables:
```
REVIEW_DAYS=30
REVIEW_LIMIT=500
MIN_RATING=1
MAX_RATING=5
EXTRACTIVE_SENTENCES=5
VERBOSE=False
OUTPUT_FORMAT=text
```

## Usage

### Command Line Interface

The tool provides a user-friendly CLI with the following commands:

#### List Available Apps

```bash
python review_summarizer_cli.py list-apps
```

This command will display all apps accessible with your AppBot API credentials.

#### Generate App Review Summaries

```bash
python review_summarizer_cli.py summarize --app-id APP_ID [OPTIONS]
```

Options:
- `--app-id`, `-a`: AppBot application ID
- `--days`, `-d`: Number of days of reviews to analyze (default: 90)
- `--limit`, `-l`: Maximum number of reviews to process (default: 500)
- `--min-rating`, `-m`: Minimum rating to include (1-5, default: 1)
- `--max-rating`, `-M`: Maximum rating to include (1-5, default: 5)
- `--format`, `-f`: Output format (text, json, markdown; default: text)
- `--output`, `-o`: Output file path
- `--verbose`, `-v`: Enable verbose output

Example:

```bash
# Analyze the last 30 days of reviews for app ID 1234567, save as markdown
python review_summarizer_cli.py summarize --app-id 1234567 --days 30 --format markdown --output summary.md
```

### Programmatic Usage

You can also use the modules directly in your code:

```python
from appbot import AppBotClient
from text_rank import TextRankSummarizer
from crew_setup import run_crew

# Initialize AppBot client
client = AppBotClient()

# Fetch reviews
app_id = "1234567"
reviews = []
reviews_data = client.get_reviews(app_id=app_id, start="2025-01-01", end="2025-04-10")
reviews.extend(reviews_data.get("results", []))

# Process with CrewAI
results = run_crew(reviews, verbose=True)

# Access results
extractive_summary = results["extractive_summary"]
abstractive_summary = results["abstractive_summary"]
comparison = results["comparison"]
```

## Project Structure

```
.
├── .env.example             # Example environment variables
├── CLAUDE.md                # Instructions for Claude Code
├── PRD.md                   # Product Requirements Document
├── README.md                # This file
├── app_review_summarizer.py # Main application logic
├── appbot-client/           # AppBot API client package
├── config_manager.py        # Configuration management
├── crew_setup.py            # CrewAI agent configuration
├── implementation_plan.md   # Project implementation details
├── requirements.txt         # Python dependencies
├── review_summarizer_cli.py # Command-line interface
└── text_rank.py             # TextRank implementation for extractive summarization
```

## How It Works

1. **AppBot Client**: Fetches app reviews from the AppBot API using your credentials
2. **TextRank Algorithm**: Processes review text to identify key sentences by building a graph representation and ranking sentences by importance
3. **CrewAI Orchestration**:
   - **Extractive Summarizer Agent**: Uses TextRank to extract important sentences from reviews
   - **Abstractive Summarizer Agent**: Uses GPT-4o to generate a cohesive summary
   - **Comparison Agent**: Uses o1 to compare the two summaries and evaluate them

4. **Output Generation**: Formats the results as text, JSON, or markdown

## Example Output

### Extractive Summary
```
The app crashes every time I try to open it. Very frustrating. Good app but it drains my battery too quickly. Interface is confusing and not user-friendly. The latest update fixed many bugs. Much better performance now.

Ratings mentioned: Rating: 1 stars
Rating: 2 stars
Rating: 3 stars
Rating: 4 stars
```

### Abstractive Summary
```
User feedback on this app is mixed. While some users appreciate the latest update that has fixed bugs and improved performance, many still report significant issues. The main complaints include frequent app crashes on startup, excessive battery drain, and a confusing, non-user-friendly interface. Despite these problems, some users still consider it a "good app" overall, suggesting the core functionality is valuable when it works properly.
```

### Comparison
```
Comparison of Summaries:

1. Completeness:
   * Extractive Summary directly quotes five distinct issues from reviews: app crashes, frustration, battery drain, confusing interface, and the positive note about bug fixes.
   * Abstractive Summary covers the same core issues but adds interpretation by grouping feedback as "mixed" and noting that users still value the core functionality despite problems.

2. Accuracy:
   * Extractive Summary is inherently accurate as it uses verbatim sentences from reviews, including the exact ratings.
   * Abstractive Summary accurately represents the overall sentiment but makes inferences (like "suggesting the core functionality is valuable") that aren't explicitly stated in the original quotes.

3. Readability:
   * Extractive Summary reads as disconnected statements with abrupt transitions.
   * Abstractive Summary flows more naturally as a cohesive paragraph with proper transitions between ideas.

4. Usefulness:
   * Extractive Summary provides direct voice-of-customer feedback that developers can quote directly.
   * Abstractive Summary offers better context and interpretation of the feedback's significance.

Recommendation: The Abstractive Summary is more effective overall for understanding the general user sentiment and key issues, but the Extractive Summary provides valuable direct quotes that maintain the authentic user voice. For developers, a combination of both would be optimal - using the Abstractive Summary for a quick understanding and the Extractive Summary for specific user language.
```

## Development

### Running Tests

```bash
python -m pytest
```

### Code Formatting

```bash
black .
isort .
```

### Linting

```bash
flake8
```

## Future Extensions

This project is designed to be extensible for multi-modal inputs (e.g., screenshots or audio in reviews). The architecture accommodates adding agents/tools for image or audio processing without significant rework.

## License

[MIT License](LICENSE)

## Acknowledgments

- CrewAI for the multi-agent orchestration framework
- OpenAI for GPT-4o and o1 models
- AppBot for review data access