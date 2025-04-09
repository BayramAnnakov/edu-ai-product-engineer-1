import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import openai
import os
from dotenv import load_dotenv

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables
load_dotenv()

def read_text(file_path):
    """Read text from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extractive_summarize(text, num_sentences=5):
    """Generate an extractive summary using NLTK."""
    # Tokenize sentences
    sentences = sent_tokenize(text)
    
    # Tokenize words and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_frequencies = defaultdict(int)
    
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        for word in words:
            if word not in stop_words and word.isalnum():
                word_frequencies[word] += 1
    
    # Calculate sentence scores
    sentence_scores = defaultdict(int)
    for i, sentence in enumerate(sentences):
        words = word_tokenize(sentence.lower())
        for word in words:
            if word in word_frequencies:
                sentence_scores[i] += word_frequencies[word]
    
    # Get top sentences
    top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    summary_sentences = [sentences[i] for i in sorted(top_sentence_indices)]
    
    return ' '.join(summary_sentences)

def abstractive_summarize(text):
    """Generate an abstractive summary using OpenAI API."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
            {"role": "user", "content": f"Please summarize the following text in a concise and coherent way:\n\n{text}"}
        ],
        max_tokens=150,
        temperature=0.7
    )
    
    return response.choices[0].message['content'].strip() 