from typing import Dict
from nltk.tokenize import sent_tokenize, word_tokenize
import pandas as pd

def get_article_text(file_path: str) -> str:
    """Read text from a file and return it as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""


def get_reviews_from_csv(csv_path: str, num_rows: int = 5) -> str:
    """Read reviews from a CSV file and return them as a formatted string.
    
    Args:
        csv_path: Path to the CSV file.
        num_rows: Number of rows to read (default: 5).
        
    Returns:
        A formatted string of reviews or an error message.
    """
    try:
        # Try to read the CSV with only num_rows
        df = pd.read_csv(csv_path, nrows=num_rows)
        if df.empty:
            return "No reviews found in the CSV file."

        # Check if "Text" column exists, otherwise find the first text-based column
        if "Text" in df.columns:
            review_column = "Text"
        else:
            # Select first non-numeric column as a fallback
            text_columns = df.select_dtypes(include=['object', 'string']).columns
            if not text_columns.any():
                return "No text columns found in the CSV file."
            review_column = text_columns[0]  # Pick the first available text column

        # Convert column to string and drop NaN values
        reviews = df[review_column].dropna().astype(str).tolist()

        # Remove empty or whitespace-only reviews
        valid_reviews = [review.strip() for review in reviews if review.strip()]

        if not valid_reviews:
            return "No valid reviews found in the CSV file."

        # Format the reviews with numbering
        combined_text = "\n\n".join([f"REVIEW {i+1}:\n{review}" for i, review in enumerate(valid_reviews)])

        return combined_text
    except Exception as e:
        return f"Error reading CSV file: {e}"


def get_metrics(text: str) -> Dict[str, float]:
    """Calculate text metrics."""
    try:
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        return {
            'characters': float(len(text)),
            'words': float(len(words)),
            'sentences': float(len(sentences)),
            'avg_words_per_sentence': float(len(words) / len(sentences)) if sentences else 0.0
        }
    except Exception as e:
        print(f"Error in get_metrics: {e}")
        return {
            'characters': 0.0,
            'words': 0.0,
            'sentences': 0.0,
            'avg_words_per_sentence': 0.0
        }

def print_metrics(original_metrics: Dict[str, float], 
                 extractive_metrics: Dict[str, float], 
                 abstractive_metrics: Dict[str, float],
                 extractive_time: float,
                 abstractive_time: float) -> None:
    """Print detailed metrics for both summarization methods."""
    print("\n=== Text Analysis Metrics ===")
    print(f"Original Text Metrics:")
    print(f"Characters: {original_metrics['characters']}")
    print(f"Words: {original_metrics['words']}")
    print(f"Sentences: {original_metrics['sentences']}")
    print(f"Average words per sentence: {original_metrics['avg_words_per_sentence']:.2f}")
    
    print("\n=== Time Comparison ===")
    print(f"Extractive processing time: {extractive_time:.2f} seconds")
    print(f"Abstractive processing time: {abstractive_time:.2f} seconds")
    
    print("\n=== Length Comparison ===")
    print(f"Extractive Summary:")
    print(f"- Characters: {extractive_metrics['characters']} ({extractive_metrics['characters']/original_metrics['characters']*100:.1f}% of original)")
    print(f"- Words: {extractive_metrics['words']} ({extractive_metrics['words']/original_metrics['words']*100:.1f}% of original)")
    print(f"- Sentences: {extractive_metrics['sentences']} ({extractive_metrics['sentences']/original_metrics['sentences']*100:.1f}% of original)")
    
    print(f"\nAbstractive Summary:")
    print(f"- Characters: {abstractive_metrics['characters']} ({abstractive_metrics['characters']/original_metrics['characters']*100:.1f}% of original)")
    print(f"- Words: {abstractive_metrics['words']} ({abstractive_metrics['words']/original_metrics['words']*100:.1f}% of original)")
    print(f"- Sentences: {abstractive_metrics['sentences']} ({abstractive_metrics['sentences']/original_metrics['sentences']*100:.1f}% of original)")