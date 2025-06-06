# Product Review Analysis System

## Overview
This project is an AI-powered system for analyzing product reviews using OpenAI's GPT models. It processes customer reviews to generate actionable insights, including feature suggestions and user personas, and simulates user research sessions.

## Features
- Loads and validates product reviews from CSV files
- Identifies key user pain points and generates feature suggestions
- Creates detailed user personas based on review analysis
- Simulates interactive user research sessions
- Generates comprehensive summaries with insights and recommendations

## Project Structure
```
├── data/               # Data storage directory
├── output/            # Output files directory
├── src/               # Source code
│   ├── __init__.py
│   ├── agent_persona_creator.py   # Persona generation logic
│   ├── data_loader.py            # CSV loading and validation
│   ├── llm_client.py            # OpenAI API interaction
│   ├── logger_config.py         # Logging configuration
│   ├── main.py                 # Main application entry
│   ├── product_manager_agent.py # Product analysis logic
│   └── reviews_preparer.py     # Review data preparation
├── tests/             # Test files
├── README.md          # Project documentation
├── requirements.txt   # Project dependencies
└── Reviews.csv       # Sample review data
```

## Requirements
- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a .env file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage
Run the analysis with:
```bash
python -m src.main --csv-path path/to/your/reviews.csv
```

The system will:
1. Load and validate the review data
2. Generate feature suggestions based on user pain points
3. Create user personas from the reviews
4. Simulate a user research session
5. Save the results to the output directory

## Output
The system generates:
- Console logs with detailed analysis progress
- A summary.txt file in the output directory containing:
  - Key feature suggestions
  - User personas
  - User research session insights
  - Recommendations for improvement

## Logging
Logs are saved to:
- Console output for immediate feedback
- Daily log files in the output directory (format: app_YYYYMMDD.log)