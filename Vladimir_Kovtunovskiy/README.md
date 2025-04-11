# Product Review Analysis Agent

This project contains a LangGraph-based agent for analyzing product reviews. The agent can load review data, generate extractive and abstractive summaries, and compare the two summarization approaches.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY=your_api_key_here
```
Or create a `.env` file with your API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the Agent

You can run the agent using one of the following commands:

```bash
# Run the basic agent
python summary_agent.py

# Run the LangGraph workflow
python summary_langgraph_agent.py
```

The `summary_agent.py` script uses a ReAct agent to interactively analyze reviews, while the `summary_langgraph_agent.py` script uses a LangGraph workflow to perform a multi-step analysis.

### Agent Tools

The agent has the following tools:

- `load_review_data`: Load review data from a CSV file
- `extractive_summarizer`: Generate an extractive summary using NLTK
- `select_random_reviews`: Select a specified number of random reviews and combine them into a single text

### LangGraph Workflow

The LangGraph workflow consists of the following steps:

1. **Load and Select Reviews**: Loads the review data and selects a random sample
2. **Generate Extractive Summary**: Creates an extractive summary using NLTK
3. **Generate Abstractive Summary**: Creates an abstractive summary using GPT-4o-mini
4. **Compare Summaries**: Compares the extractive and abstractive summaries

## Data

The agent works with the `Reviews.csv` file, which contains product reviews with the following columns:

- Id: Review ID
- ProductId: Product ID
- UserId: User ID
- ProfileName: User profile name
- HelpfulnessNumerator: Number of users who found the review helpful
- HelpfulnessDenominator: Number of users who rated the review
- Score: Rating (1-5)
- Time: Timestamp
- Summary: Review summary
- Text: Review text

## Project Structure

```
.
├── .env                 # Environment variables
├── .gitignore          # Git ignore file
├── data_loader.py      # Functions for loading review data
├── requirements.txt    # Project dependencies
├── README.md           # Project documentation
├── Reviews.csv         # Review data (not tracked in git)
├── summary_agent.py    # ReAct agent implementation
├── summary_langgraph_agent.py  # LangGraph workflow implementation
└── summary_workflow.py # Workflow components and utilities
```

## Summarization Approaches

### Extractive Summarization

The extractive summarization approach selects the most important sentences from the original text based on word frequency. This approach:

1. Tokenizes the text into sentences
2. Removes stopwords and punctuation
3. Calculates word frequencies
4. Scores sentences based on the frequencies of their words
5. Selects the top sentences to form the summary

### Abstractive Summarization

The abstractive summarization approach uses GPT-4o-mini to generate a new summary that captures the key points, sentiment, and insights from the reviews in a natural, flowing narrative. This approach:

1. Takes the selected reviews as input
2. Uses a prompt template to guide the LLM
3. Generates a concise, coherent summary
4. Captures the main themes and overall sentiment

## License

MIT 