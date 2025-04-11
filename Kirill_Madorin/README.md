# Multi-Modal Review Summarization Agent

This project implements an agent that processes customer reviews using both deterministic extractive summarization and probabilistic abstractive summarization with LLMs, and then compares the results.

## Features

- **Extractive Summarizer**: Deterministically extracts the first sentence from each review as a summary.
- **Abstractive Summarizer**: Uses the OpenAI Agents SDK to generate concise, informative summaries using LLMs.
- **Comparison Reporter**: Analyzes and compares both summary types with similarity metrics and provides detailed insights.
- **Agent Orchestration**: Uses the OpenAI Agents SDK to manage the entire workflow.

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key in a `.env` file:

```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file with your OpenAI API key
# Replace 'your_api_key_here' with your actual API key
```

## Usage

### Basic Usage

Run the agent on the provided sample reviews:

```bash
python main_agent.py
```

This will:
1. Process the reviews in `First10Reviews.csv`
2. Generate extractive and abstractive summaries
3. Create a comparison report at `comparison_report.md`

### Custom Input/Output

Specify your own input file and output location:

```bash
python main_agent.py --input your_reviews.csv --output your_report.md
```

### Sample a Large Dataset

If you have a large CSV file of reviews, you can extract a sample:

```bash
python extract_reviews.py
```

This will create a `SampleReviews.csv` file with a random sample of reviews from `Reviews.csv`.

## Components

- **extractive_summarizer.py**: Implements first-sentence extraction
- **abstractive_summarizer.py**: Implements LLM-based summarization
- **comparison_reporter.py**: Generates comprehensive comparison reports
- **main_agent.py**: Orchestrates the entire workflow
- **extract_reviews.py**: Utility for extracting review samples

## Example Output

The comparison report includes:
- Executive summary
- Per-review comparisons with metrics
- Overall statistics
- Conclusions and follow-up questions

## Requirements

- Python 3.8+
- OpenAI API key (set in .env file)
- Dependencies in requirements.txt

## Future Enhancements

- Add sentiment analysis
- Support multi-document summarization
- Implement custom extraction algorithms
- Add visualization for summary comparisons 