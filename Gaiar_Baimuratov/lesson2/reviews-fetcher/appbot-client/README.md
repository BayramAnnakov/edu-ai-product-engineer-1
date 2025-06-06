# AppBot API Client

A Python client for interacting with the AppBot API to retrieve app review data and analytics.

## Features

The client provides access to all AppBot API endpoints:

- Authentication and token information
- App listing and management
- Review retrieval and analysis
- Sentiment analysis
- Word and phrase analysis
- Topic analysis
- Ratings analysis

## Installation

```bash
# Install from the repository
pip install -e .

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

You need an AppBot API key and password to use this client. Set them via:

1. Environment variables: `APPBOT_API_USERNAME` and `APPBOT_API_PASSWORD`
2. Direct parameters: `AppBotClient(username="YOUR_KEY", password="YOUR_PASSWORD")`

## Basic Usage

```python
from appbot import AppBotClient

# Initialize client with API credentials
client = AppBotClient()  # Uses environment variables

# Get team sources (apps)
apps = client.get_apps()
print(f"Found {len(apps)} apps")

# Get reviews for an app
app_id = apps[0]["id"]  # Use first app ID
reviews = client.get_reviews(
    app_id=app_id, 
    start="2025-01-01", 
    end="2025-04-01"
)
print(f"Found {reviews.get('total_count')} reviews")
```

## Running Examples

The package includes example scripts that demonstrate client usage:

```bash
# Run all examples
./run_examples.py

# Or use the module directly
python -m appbot.examples
```

## Running Tests

```bash
# Run all tests
./run_tests.py

# Or use unittest directly
python -m unittest discover -s tests
```

## Full Documentation

See [USAGE.md](USAGE.md) for detailed documentation of all available methods and examples.