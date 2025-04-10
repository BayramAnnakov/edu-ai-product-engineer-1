"""
TextRank implementation for extractive summarization of app reviews.

This module provides a TextRank-based implementation for extracting the most important
sentences from a collection of app reviews. It uses Natural Language Processing
techniques like sentence tokenization, TF-IDF vectorization, and graph-based ranking
to identify key sentences.
"""
import re
import string
from typing import List, Dict, Union, Optional

import networkx as nx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


def preprocess_text(text: str) -> str:
    """
    Clean and preprocess text for analysis.
    
    Args:
        text: Raw input text
        
    Returns:
        Preprocessed text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text, handling app review specific formatting.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Split reviews if they're concatenated
    reviews = re.split(r'\n\s*\n', text)
    
    all_sentences = []
    for review in reviews:
        # Extract sentences from each review
        sentences = sent_tokenize(review)
        all_sentences.extend(sentences)
    
    # Filter out very short sentences (likely not meaningful)
    return [s.strip() for s in all_sentences if len(s.split()) > 3]


def build_similarity_matrix(sentences: List[str]) -> Union[List[List[float]], None]:
    """
    Build similarity matrix between sentences using TF-IDF and cosine similarity.
    
    Args:
        sentences: List of sentences to compare
        
    Returns:
        2D similarity matrix or None if fewer than 2 sentences
    """
    if len(sentences) < 2:
        return None
    
    # Create TF-IDF vectorizer
    stop_words = set(stopwords.words('english'))
    vectorizer = TfidfVectorizer(stop_words=stop_words)
    
    try:
        # Get TF-IDF matrix
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        return similarity_matrix
    
    except ValueError:
        # Handle case where vectorizer fails (e.g., all words are stop words)
        return None


def textrank_summarize(
    text: str, 
    num_sentences: int = 5, 
    include_ratings: bool = True
) -> str:
    """
    Summarize text using TextRank algorithm.
    
    Args:
        text: Input text to summarize
        num_sentences: Number of sentences to extract
        include_ratings: Whether to include rating information in summary
        
    Returns:
        String containing the extractive summary
    """
    # Extract sentences
    sentences = extract_sentences(text)
    
    # If there are fewer sentences than requested, return all sentences
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
    
    # Build similarity matrix
    similarity_matrix = build_similarity_matrix(sentences)
    if similarity_matrix is None:
        return " ".join(sentences)
    
    # Create graph from similarity matrix
    graph = nx.from_numpy_array(similarity_matrix)
    
    # Run PageRank
    scores = nx.pagerank(graph, alpha=0.85)
    
    # Rank sentences by score
    ranked_sentences = sorted([(scores[i], sentence, i) for i, sentence in enumerate(sentences)], 
                              reverse=True)
    
    # Extract top sentences while preserving original order
    top_sentence_indices = sorted([i for _, _, i in ranked_sentences[:num_sentences]])
    selected_sentences = [sentences[i] for i in top_sentence_indices]
    
    # Return the summary
    summary = " ".join(selected_sentences)
    
    # Extract rating patterns if requested
    if include_ratings and "Rating:" in text:
        rating_patterns = re.findall(r'Rating: [1-5] stars', text)
        if rating_patterns:
            ratings_summary = "\n".join(set(rating_patterns))
            summary = f"{summary}\n\nRatings mentioned: {ratings_summary}"
    
    return summary


def summarize_app_reviews(reviews: List[Dict], num_sentences: int = 5) -> str:
    """
    Summarize a list of app review dictionaries.
    
    Args:
        reviews: List of review dictionaries with 'body' and 'rating' keys
        num_sentences: Number of sentences to include in summary
        
    Returns:
        Extractive summary of reviews
    """
    # Convert reviews to text
    reviews_text = "\n\n".join([
        f"Rating: {review.get('rating')} stars\n{review.get('body', '')}" 
        for review in reviews
    ])
    
    # Generate summary
    return textrank_summarize(reviews_text, num_sentences)


class TextRankSummarizer:
    """Class for TextRank-based extractive summarization."""
    
    def __init__(self, num_sentences: int = 5):
        """
        Initialize the summarizer.
        
        Args:
            num_sentences: Default number of sentences to extract
        """
        self.num_sentences = num_sentences
    
    def summarize(self, text: str, num_sentences: Optional[int] = None) -> str:
        """
        Generate extractive summary.
        
        Args:
            text: Text to summarize
            num_sentences: Number of sentences to extract (overrides default)
            
        Returns:
            Extractive summary
        """
        sentences = num_sentences or self.num_sentences
        return textrank_summarize(text, sentences)
    
    def summarize_reviews(self, reviews: List[Dict], num_sentences: Optional[int] = None) -> str:
        """
        Summarize app reviews.
        
        Args:
            reviews: List of review dictionaries
            num_sentences: Number of sentences to extract (overrides default)
            
        Returns:
            Extractive summary
        """
        sentences = num_sentences or self.num_sentences
        return summarize_app_reviews(reviews, sentences)


if __name__ == "__main__":
    # Simple test
    test_reviews = [
        {"body": "This app is great! I love the new features they added.", "rating": 5},
        {"body": "The app crashes every time I try to open it. Very frustrating.", "rating": 1},
        {"body": "Good app but it drains my battery too quickly.", "rating": 3},
        {"body": "The latest update fixed many bugs. Much better performance now.", "rating": 4},
        {"body": "Interface is confusing and not user-friendly.", "rating": 2}
    ]
    
    summarizer = TextRankSummarizer(num_sentences=3)
    summary = summarizer.summarize_reviews(test_reviews)
    
    print("EXTRACTIVE SUMMARY:")
    print(summary)