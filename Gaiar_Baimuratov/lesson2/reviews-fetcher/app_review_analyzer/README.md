# App Review Feature Request Analyzer

A tool for extracting feature requests from app reviews and generating user interview questions.

## Overview

This project analyzes app store reviews to extract feature requests mentioned by users. It uses OpenAI's GPT-4o to process review data, extract explicit feature requests, group similar requests together, and generate relevant interview questions for user research.

## Features

- Load and process app review data from JSON files
- Chunk reviews for efficient LLM processing
- Extract explicit feature requests using GPT-4o
- Group and deduplicate similar feature requests
- Generate insightful interview questions for each feature request
- Export results in a structured JSON format

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Process Reviews

```bash
python -m src.main --reviews-path /path/to/reviews.json --output-path feature_requests.json
```

Parameters:
- `--reviews-path`: Path to the JSON file containing app reviews (required)
- `--output-path`: Path to save the output JSON file (default: feature_requests_interview_plan.json)
- `--max-tokens`: Maximum tokens per chunk for LLM processing (default: 4000)

### Example Output Format

```json
[
  {
    "topic": "Dark mode support for reduced eye strain",
    "core_questions": [
      "How important is dark mode to your experience with the app?",
      "In what contexts or times of day would you use dark mode?",
      "What concerns might you have about how dark mode would impact other features you use?"
    ],
    "max_followups": 3
  },
  {
    "topic": "Offline access to saved content",
    "core_questions": [
      "How would offline access change the way you use our app?",
      "What type of content would be most valuable to access offline?",
      "What limitations would be acceptable for an offline mode?"
    ],
    "max_followups": 3
  }
]
```

## Testing

Run the test suite:

```bash
python -m pytest
```

Run a specific test:

```bash
python -m pytest tests/test_review_processor.py::test_chunk_reviews
```

## Dependencies

- openai: GPT-4o API access
- tiktoken: Token counting for chunking
- python-dotenv: Environment variable management
- pytest: Testing framework