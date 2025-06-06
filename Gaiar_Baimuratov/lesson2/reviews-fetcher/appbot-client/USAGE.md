# AppBot Client Usage Guide

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd appbot-client
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API credentials
   ```

## Running Tests

Run the unit tests:
```bash
./run_tests.py
# or
python -m unittest discover -s tests
```

## Running Examples

```bash
./run_examples.py
```

## Using the Client in Your Own Code

```python
from appbot import AppBotClient

# Initialize with credentials
client = AppBotClient(username="YOUR_API_KEY", password="API_PASSWORD")
# Or use environment variables:
# client = AppBotClient()

# Get app listings
apps = client.get_apps()
print(f"Found {len(apps)} apps")

# Get reviews
app_id = apps[0]["id"]  # Use the first app's ID
reviews = client.get_reviews(
    app_id=app_id,
    start="2023-01-01",
    end="2023-01-31",
    country=101,  # United States
    sentiments=["positive", "neutral"],
    page=1
)
print(f"Found {reviews.get('total_count')} reviews")

# Get sentiment breakdown
sentiment = client.get_sentiment_breakdown(
    app_id=app_id,
    start="2023-01-01",
    end="2023-01-31"
)
print(sentiment)

# Get popular words
words = client.get_popular_words(
    app_id=app_id,
    start="2023-01-01",
    end="2023-01-31"
)
print(f"Found {len(words.get('results', []))} popular words")
```

## Available Methods

The client provides methods to access all endpoints of the AppBot API:

### Core Methods
- `get_token_info()` - Get information about your API token
- `get_apps()` - List team sources (apps)
- `get_detected_languages()` - List detected languages
- `get_topics()` - List topics, custom topics & tags
- `get_countries(app_id)` - List review-specific countries
- `get_ratings_countries(app_id)` - List ratings-specific countries

### Review Methods
- `get_reviews(app_id, ...)` - Get reviews for an app
- `get_review_summary_by_date(app_id, ...)` - Get review summary by date
- `get_review_summary_by_country(app_id, ...)` - Get review summary by country
- `get_review_summary_by_stars(app_id, ...)` - Get review summary by stars
- `get_review_star_overview(app_id, ...)` - Get review star overview

### Sentiment Methods
- `get_sentiment_breakdown(app_id, ...)` - Get sentiment breakdown
- `get_sentiment_timeline(app_id, ...)` - Get sentiment timeline
- `get_sentiment_grade(app_id, ...)` - Get sentiment grade

### Word and Phrase Methods
- `get_popular_words(app_id, ...)` - Get popular words
- `get_critical_words(app_id, ...)` - Get critical words
- `get_words(app_id, word_type, ...)` - Get words by type
- `get_phrases(app_id, phrase_word_count, ...)` - Get phrases

### Topic Methods
- `get_app_topics(app_id, ...)` - Get app topics
- `get_topic_reviews(app_id, topic_id, ...)` - Get reviews for a topic

### Ratings Methods
- `get_ratings_live(app_id, ...)` - Get live ratings
- `get_ratings_historical(app_id, ...)` - Get historical ratings
- `get_ratings_bulk(app_id, start, ...)` - Get bulk ratings

Refer to each method's docstring for detailed parameter information.