import pandas as pd
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

def extract_first_sentence(text):
    """Extracts the first sentence from a given text."""
    if pd.isna(text):
        return ""
    sentences = nltk.sent_tokenize(str(text))
    return sentences[0] if sentences else ""

def generate_extractive_summaries(csv_path: str) -> pd.DataFrame:
    """
    Reads reviews from a CSV file and generates extractive summaries
    by taking the first sentence of the 'Text' column.

    Args:
        csv_path: Path to the CSV file containing reviews.

    Returns:
        A pandas DataFrame with original 'Id', 'Text', and the generated 'ExtractiveSummary'.
    """
    df = pd.read_csv(csv_path)
    if 'Text' not in df.columns:
        raise ValueError("CSV file must contain a 'Text' column.")
    if 'Id' not in df.columns:
         # Assuming 'Id' might not always be present, generate one if missing
         df['Id'] = range(len(df))


    # Ensure Text column is string type, handling potential float values
    df['Text'] = df['Text'].astype(str)

    df['ExtractiveSummary'] = df['Text'].apply(extract_first_sentence)

    return df[['Id', 'Text', 'ExtractiveSummary']]

if __name__ == '__main__':
    # Example usage:
    input_csv = 'First10Reviews.csv'
    summaries_df = generate_extractive_summaries(input_csv)
    print("Extractive Summaries:")
    print(summaries_df) 