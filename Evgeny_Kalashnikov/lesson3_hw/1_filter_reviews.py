import pandas as pd
import os
from openai import OpenAI
from datetime import datetime
from langdetect import detect, DetectorFactory
import json

# Ensure consistent language detection results
DetectorFactory.seed = 0

# --- Configuration ---
INPUT_CSV_PATH = 'Evgeny_Kalashnikov/NETFLIX_REVIEWS.csv'
OUTPUT_DIR = '.' # Current directory (Evgeny_Kalashnikov/lesson3_hw)
REVIEW_TEXT_COLUMN = "review_text"
OTHER_REVIEW_COLUMNS = ["review_rating", "review_likes"]
TIMESTAMP_COLUMN = "review_timestamp"
LIKES_COLUMN = "review_likes"
MODEL_NAME = "o4-mini-2025-04-16"
CATEGORIES = ['bug report', 'feature requests', 'other']
CLASSIFICATION_COLUMN_NAME = "classification_type"
REASONING_COLUMN_NAME = "classification_reasoning"
MAX_PER_CATEGORY = 20
MIN_TOTAL_PER_CATEGORY = 10
ALLOWED_LANGUAGES = ['en', 'ru']

# --- OpenAI Client ---
# Ensure your OPENAI_API_KEY is set as an environment variable
client = OpenAI()

def detect_language(text: str) -> str | None:
    """Detects the language of the input text."""
    if not isinstance(text, str):
        return None
    try:
        return detect(text)
    except:
        return None

def classify_review(review_text: str) -> tuple[str, str | None]:
    """Classifies a single review and provides reasoning using the OpenAI model.
       Returns a tuple of (classification, reasoning). Reasoning is None if JSON parsing fails.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": f"Classify the following review into one of these categories: {', '.join(CATEGORIES)}. For 'feature requests', explain the feature requested. For 'bug report', explain the bug reported. For 'other', provide a brief overview of the review. Respond with a JSON object with two keys: 'category' (one of the specified categories) and 'reasoning' (a string explaining your classification, detailing the feature/bug if applicable, or a brief overview)."},
                {"role": "user", "content": review_text}
            ]
        )
        content = response.choices[0].message.content.strip()
        
        # Attempt to parse JSON response
        try:
            json_response = json.loads(content)
            classification = json_response.get('category', '').strip().lower()
            reasoning = json_response.get('reasoning', '').strip()
            # Basic validation of category
            if classification not in CATEGORIES:
                 print(f"Warning: Unexpected classification '{classification}' for review: {review_text[:50]}...")
                 # If classification is unexpected, default to 'other' but keep the reasoning
                 return 'other', reasoning if reasoning != "" else f"Unexpected classification: {classification}"

            return classification, reasoning

        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON response for review: {review_text[:50]}...")
            print(f"Raw response: {content}")
            return None, None # Indicate parsing failure
            

    except Exception as e:
        print(f"Error classifying review: {e}")
        return 'other', f"Error during classification: {e}" # Default to other and provide error as reasoning on error

def main():
    """Main function to read, classify, and save reviews."""
    try:
        # Read the CSV file
        df = pd.read_csv(INPUT_CSV_PATH)

        # Ensure LIKES_COLUMN is numeric and sort by likes (highest first)
        df[LIKES_COLUMN] = pd.to_numeric(df[LIKES_COLUMN], errors='coerce')
        # Sort by likes (descending), falling back to timestamp if likes are NaN
        df[TIMESTAMP_COLUMN] = pd.to_datetime(df[TIMESTAMP_COLUMN], errors='coerce') # Ensure timestamp is datetime for fallback sort
        df = df.sort_values(by=[LIKES_COLUMN, TIMESTAMP_COLUMN], ascending=[False, False])
        # Drop rows with invalid review text or likes (timestamp can be used for fallback sort)
        df = df.dropna(subset=[REVIEW_TEXT_COLUMN, LIKES_COLUMN])

        collected_data = []
        collected_counts = {category: 0 for category in CATEGORIES}

        print("Starting review analysis...")

        # Iterate through reviews
        for index, row in df.iterrows():
            # Check if minimum requirements are met for all categories
            if all(count >= MIN_TOTAL_PER_CATEGORY for count in collected_counts.values()):
                print("Minimum reviews collected for all categories. Stopping.")
                break

            review_text = str(row[REVIEW_TEXT_COLUMN]) # Ensure review text is string

            # Detect language
            lang = detect_language(review_text)

            # Process only allowed languages
            if lang not in ALLOWED_LANGUAGES:
                continue # Skip this review if not in allowed languages

            # Classify the review and get reasoning
            classification, reasoning = classify_review(review_text)

            # Skip if JSON parsing failed during classification
            if classification is None or reasoning is None:
                print(f"Skipping review due to classification parsing error: {review_text[:50]}...")
                continue

            # Add to collection if not exceeding max per category
            if collected_counts[classification] < MAX_PER_CATEGORY:
                # Create a dictionary from the original row and add the classification and reasoning
                row_data = row.to_dict()
                row_data[CLASSIFICATION_COLUMN_NAME] = classification
                row_data[REASONING_COLUMN_NAME] = reasoning
                collected_data.append(row_data)
                collected_counts[classification] += 1
                print(f"Collected '{classification}' review count: {collected_counts[classification]} (Language: {lang})")


        print("Analysis complete. Creating output file.")

        # Create results DataFrame from collected data
        results_df = pd.DataFrame(collected_data)

        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_classified.csv")

        # Save to CSV
        results_df.to_csv(output_filename, index=False)

        print(f"Results saved to {output_filename}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
    except ImportError:
         print("Error: 'langdetect' library not found. Please install it using 'pip install langdetect'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 