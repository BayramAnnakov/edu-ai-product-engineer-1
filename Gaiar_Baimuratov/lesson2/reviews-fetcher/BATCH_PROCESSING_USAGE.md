# Batch Processing Usage Guide

This guide explains how to use the batch processing system to generate interview transcripts for feature requests extracted from app reviews.

## Overview

The batch processing system consists of the following components:

1. **Feature Adapter (`feature_adapter.py`)**: Converts feature requests from analyze_all_markets.py format to UserBoard4 format
2. **Batch Interviews (`batch_interviews.py`)**: Runs UserBoard4 interviews for each feature
3. **Report Generator (`report_generator.py`)**: Creates consolidated reports from interview transcripts
4. **Process All Features (`process_all_features.py`)**: Master script that orchestrates the entire process

## Prerequisites

Ensure you have the following:

1. Python 3.7 or higher installed
2. The necessary dependencies installed:
   ```bash
   pip install rich pydantic openai python-dotenv
   ```
3. App review data in JSON format (from AppBot API)
4. Personas defined in a CSV file (default: `personas.csv`)
5. Access to OpenAI API (for UserBoard4) - set `OPENAI_API_KEY` environment variable

## Step-by-Step Usage Guide

### Option 1: End-to-End Processing

To run the entire pipeline from review data to final reports:

```bash
./process_all_features.py --review-data path/to/reviews.json --output-dir output_directory
```

This will:
1. Extract features from app reviews
2. Run interviews for each feature
3. Generate consolidated reports

### Option 2: Individual Steps

#### Step 1: Convert Features to UserBoard4 Format

If you already have features extracted:

```bash
./feature_adapter.py path/to/features.json --output interview_config.json
```

#### Step 2: Run Batch Interviews

To run interviews for all features:

```bash
./batch_interviews.py path/to/features.json --output-dir interviews_output
```

For testing with a subset of features:

```bash
./batch_interviews.py path/to/features.json --max-features 3
```

#### Step 3: Generate Consolidated Reports

To generate reports from interview transcripts:

```bash
./report_generator.py path/to/transcripts_directory
```

## Command-Line Options

### process_all_features.py

```
usage: process_all_features.py [-h] [--review-data REVIEW_DATA] [--output-dir OUTPUT_DIR] [--personas PERSONAS]
                               [--userboard-script USERBOARD_SCRIPT] [--max-followups MAX_FOLLOWUPS]
                               [--max-features MAX_FEATURES] [--skip-extraction] [--features-file FEATURES_FILE]
                               [--skip-interviews] [--transcripts-dir TRANSCRIPTS_DIR]

Process all features from review data to final reports

optional arguments:
  -h, --help            show this help message and exit
  --review-data REVIEW_DATA, -r REVIEW_DATA
                        Path to the reviews data file
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Directory to store all output
  --personas PERSONAS, -p PERSONAS
                        Path to the personas CSV file
  --userboard-script USERBOARD_SCRIPT, -u USERBOARD_SCRIPT
                        Path to the userboard4 script
  --max-followups MAX_FOLLOWUPS, -m MAX_FOLLOWUPS
                        Maximum number of follow-up questions per feature
  --max-features MAX_FEATURES, -n MAX_FEATURES
                        Maximum number of features to process (for testing)
  --skip-extraction, -s
                        Skip feature extraction (use --features-file instead)
  --features-file FEATURES_FILE, -f FEATURES_FILE
                        Path to a pre-existing features file (if skipping extraction)
  --skip-interviews, -i
                        Skip interviews (use --transcripts-dir instead)
  --transcripts-dir TRANSCRIPTS_DIR, -t TRANSCRIPTS_DIR
                        Path to a pre-existing transcripts directory (if skipping interviews)
```

### feature_adapter.py

```
usage: feature_adapter.py [-h] [--output OUTPUT] [--max-followups MAX_FOLLOWUPS] [--group-similar] input_file

Convert feature requests to UserBoard4 interview config

positional arguments:
  input_file            Path to the JSON file from analyze_all_markets.py

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Path to save the interview_config.json file (default: auto-generated)
  --max-followups MAX_FOLLOWUPS, -m MAX_FOLLOWUPS
                        Maximum number of follow-up questions per feature
  --group-similar, -g   Group similar features to avoid redundant interviews
```

### batch_interviews.py

```
usage: batch_interviews.py [-h] [--personas PERSONAS] [--output-dir OUTPUT_DIR] [--userboard-script USERBOARD_SCRIPT]
                           [--max-followups MAX_FOLLOWUPS] [--max-features MAX_FEATURES]
                           features_file

Run batch interviews for feature requests

positional arguments:
  features_file         Path to the features JSON file from analyze_all_markets.py

optional arguments:
  -h, --help            show this help message and exit
  --personas PERSONAS, -p PERSONAS
                        Path to the personas CSV file
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Directory to store results
  --userboard-script USERBOARD_SCRIPT, -u USERBOARD_SCRIPT
                        Path to the userboard4-baimuratov.py script
  --max-followups MAX_FOLLOWUPS, -m MAX_FOLLOWUPS
                        Maximum number of follow-up questions per feature
  --max-features MAX_FEATURES, -n MAX_FEATURES
                        Maximum number of features to process (for testing)
```

### report_generator.py

```
usage: report_generator.py [-h] [--output-json OUTPUT_JSON] [--output-markdown OUTPUT_MARKDOWN] transcripts_dir

Generate consolidated report from interview transcripts

positional arguments:
  transcripts_dir       Directory containing interview transcripts

optional arguments:
  -h, --help            show this help message and exit
  --output-json OUTPUT_JSON, -j OUTPUT_JSON
                        Path to save the consolidated JSON report
  --output-markdown OUTPUT_MARKDOWN, -m OUTPUT_MARKDOWN
                        Path to save the markdown report
```

## Output Directory Structure

The batch processing system creates the following directory structure:

```
output_directory/
├── features/                    # Features extracted from reviews
│   └── features_*.json          # Feature files
├── interviews/                  # Batch interview results
│   ├── configs/                 # Interview configurations
│   ├── interview_transcripts/   # Interview transcripts
│   └── summaries/               # Batch summaries
└── reports/                     # Consolidated reports
    ├── consolidated_report_*.json  # JSON report
    └── consolidated_report_*.md    # Markdown report
```

## Example Usage Workflow

1. Extract features from reviews:

```bash
python analyze_all_markets.py path/to/reviews.json
```

2. Run batch interviews for the extracted features:

```bash
./batch_interviews.py output/features_1597113_20250423_114024.json --max-features 5
```

3. Generate consolidated reports:

```bash
./report_generator.py batch_interviews_output/interview_transcripts
```

4. Or do it all in one step:

```bash
./process_all_features.py -r path/to/reviews.json --max-features 5
```

## Troubleshooting

If you encounter issues:

1. Check the logs for detailed error messages
2. Ensure OpenAI API key is correctly set
3. Verify input files exist and have the correct format
4. Try processing a smaller subset of features using `--max-features`

## Notes

- Processing large numbers of features can be time-consuming and API-intensive
- Consider using `--max-features` for initial testing
- The system creates intermediate files that can be used to resume processing if needed