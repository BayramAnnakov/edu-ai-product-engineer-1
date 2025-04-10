# Data Collection with AppBot Client

This guide explains how to use the `pull_data.py` script to collect and save data from the AppBot API.

## Setup

1. Make sure you've installed the package:
   ```bash
   pip install -e .
   ```

2. Set up your environment variables in `.env`:
   ```
   APPBOT_API_USERNAME=YOUR_API_USERNAME
   APPBOT_API_PASSWORD=YOUR_API_PASSWORD
   APPBOT_APP_ID=YOUR_APP_ID  # Optional, can be specified via command line
   ```

## Basic Usage

The `pull_data.py` script provides several options for pulling data:

```bash
# List available apps
./pull_data.py --list-apps

# Pull all data types for a specific app (last 30 days)
./pull_data.py --app-id 12345

# Pull only reviews for a specific app
./pull_data.py --app-id 12345 --reviews

# Pull data for a custom date range
./pull_data.py --app-id 12345 --start-date 2025-01-01 --end-date 2025-04-01

# Pull reviews for the last 90 days
./pull_data.py --app-id 12345 --reviews --days 90

# Save reviews in CSV format
./pull_data.py --app-id 12345 --reviews --output-format csv
```

## Command Line Options

- `--list-apps`: List all available apps and their IDs
- `--app-id ID`: Specify the app ID to pull data for (alternative to setting APPBOT_APP_ID in .env)
- `--days N`: Number of days to pull data for (default: 30)
- `--start-date YYYY-MM-DD`: Start date for data (overrides --days)
- `--end-date YYYY-MM-DD`: End date for data
- `--reviews`: Pull reviews data
- `--sentiment`: Pull sentiment data
- `--words`: Pull popular words data
- `--output-format {json,csv}`: Output format for reviews (default: json)

If none of `--reviews`, `--sentiment`, or `--words` are specified, all data types will be pulled.

## Output Files

All data is saved in the `results/` directory with the following naming pattern:

- Reviews: `reviews_APP_ID_TIMESTAMP.json` or `reviews_APP_ID_TIMESTAMP.csv`
- Sentiment breakdown: `sentiment_breakdown_APP_ID_TIMESTAMP.json`
- Sentiment timeline: `sentiment_timeline_APP_ID_TIMESTAMP.json`
- Popular words: `popular_words_APP_ID_TIMESTAMP.json`
- Critical words: `critical_words_APP_ID_TIMESTAMP.json`
- App list: `apps_list_TIMESTAMP.json`

## Examples

### Get all available apps
```bash
./pull_data.py --list-apps
```

### Get reviews for the last 30 days
```bash
./pull_data.py --app-id 12345 --reviews
```

### Get sentiment data for January 2025
```bash
./pull_data.py --app-id 12345 --sentiment --start-date 2025-01-01 --end-date 2025-01-31
```

### Get popular words for the last 90 days
```bash
./pull_data.py --app-id 12345 --words --days 90
```

### Get all data for a specific period
```bash
./pull_data.py --app-id 12345 --start-date 2025-03-01 --end-date 2025-04-01
```