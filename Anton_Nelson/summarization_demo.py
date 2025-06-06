import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from string import punctuation
from heapq import nlargest
from collections import defaultdict
import openai
import os
from dotenv import load_dotenv
import sys
from difflib import SequenceMatcher

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables for OpenAI API
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def read_article(file_path):
    """Read the article from a file."""
    print(f"Current working directory: {os.getcwd()}")
    print(f"Attempting to read file: {file_path}")
    print(f"Absolute file path: {os.path.abspath(file_path)}")
    print(f"File exists: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        print(f"File size: {os.path.getsize(file_path)} bytes")
        
        try:
            # Try with UTF-8 encoding first
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"Content length: {len(content)} characters")
                print(f"First 100 characters: {content[:100]}")
                return content
        except UnicodeDecodeError:
            print("UTF-8 encoding failed, trying with latin-1 encoding")
            try:
                # Try with latin-1 encoding as fallback
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                    print(f"Content length: {len(content)} characters")
                    print(f"First 100 characters: {content[:100]}")
                    return content
            except Exception as e:
                print(f"Error reading file with latin-1 encoding: {str(e)}")
                return ""
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return ""
    else:
        print(f"File not found: {file_path}")
        return ""

def extractive_summarize(text, num_sentences=5):
    """
    Perform extractive summarization using NLTK.
    This method selects the most important sentences based on word frequency.
    """
    if not text:
        print("Warning: Empty text provided to extractive_summarize")
        return "No text to summarize."
        
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    print(f"Number of sentences found: {len(sentences)}")
    
    if len(sentences) == 0:
        return "No sentences found in the text."
    
    # Tokenize words and remove stopwords
    stop_words = set(stopwords.words('english') + list(punctuation))
    word_freq = defaultdict(int)
    
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word not in stop_words:
                word_freq[word] += 1
    
    # Calculate sentence scores based on word frequencies
    sentence_scores = defaultdict(int)
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                sentence_scores[sentence] += word_freq[word]
    
    # Get the top sentences
    num_sentences = min(num_sentences, len(sentences))
    summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    
    # Join sentences to create summary
    return ' '.join(summary_sentences)

def abstractive_summarize(text):
    """
    Perform abstractive summarization using OpenAI's GPT model.
    This method generates a new summary that may contain information not explicitly stated in the original text.
    """
    if not text:
        print("Warning: Empty text provided to abstractive_summarize")
        return "No text to summarize."
        
    try:
        # Updated API call syntax for OpenAI v1.0.0+
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, informative summaries."},
                {"role": "user", "content": f"Please provide a concise summary of the following article:\n\n{text}"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        # Updated response handling for new API
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in abstractive summarization: {str(e)}")
        return f"Error in abstractive summarization: {str(e)}"

def generate_comparison_report(original_text, extractive_summary, abstractive_summary):
    """
    Generate a detailed comparison report between the two summarization approaches.
    """
    # Calculate compression ratio
    original_length = len(original_text.split())
    extractive_length = len(extractive_summary.split())
    abstractive_length = len(abstractive_summary.split())
    
    extractive_ratio = (original_length - extractive_length) / original_length * 100
    abstractive_ratio = (original_length - abstractive_length) / original_length * 100
    
    # Calculate similarity between summaries
    similarity = SequenceMatcher(None, extractive_summary, abstractive_summary).ratio() * 100
    
    # Analyze content coverage
    extractive_sentences = set(sent_tokenize(extractive_summary))
    original_sentences = set(sent_tokenize(original_text))
    extractive_coverage = len(extractive_sentences) / len(original_sentences) * 100
    
    # Generate report
    report = f"""
=== COMPARISON REPORT ===

1. LENGTH ANALYSIS:
   - Original text: {original_length} words
   - Extractive summary: {extractive_length} words (compression: {extractive_ratio:.1f}%)
   - Abstractive summary: {abstractive_length} words (compression: {abstractive_ratio:.1f}%)

2. CONTENT ANALYSIS:
   - Extractive summary coverage: {extractive_coverage:.1f}% of original sentences
   - Similarity between summaries: {similarity:.1f}%

3. APPROACH CHARACTERISTICS:
   Extractive Summary:
   - Uses exact sentences from the original text
   - Preserves original wording and structure
   - More detailed but potentially less concise
   - Better for technical content preservation
   
   Abstractive Summary:
   - Generates new sentences and phrasing
   - More concise and natural language
   - Better at capturing main ideas and themes
   - May include inferred information

4. RECOMMENDATIONS:
   - Use extractive summarization when:
     * Preserving exact wording is important
     * Technical accuracy is crucial
     * Original sentence structure should be maintained
   
   - Use abstractive summarization when:
     * Conciseness is a priority
     * Natural language flow is important
     * Main ideas need to be synthesized
     * General audience understanding is the goal
"""
    return report

def main():
    # Read the article - using the new article file
    article_text = read_article('article_new.txt')
    
    if not article_text:
        print("Error: Could not read article text. Exiting.")
        sys.exit(1)
    
    print(f"Article text length: {len(article_text)} characters")
    print(f"Article word count: {len(article_text.split())} words")
    
    # Create output file
    with open('summarization_results.txt', 'w', encoding='utf-8') as output_file:
        # Write original article length
        output_file.write(f"Original Article Length: {len(article_text.split())} words\n\n")
        
        # Perform extractive summarization
        output_file.write("=== Extractive Summary (NLTK) ===\n")
        extractive_summary = extractive_summarize(article_text)
        output_file.write(extractive_summary + "\n")
        output_file.write(f"\nExtractive Summary Length: {len(extractive_summary.split())} words\n\n")
        
        # Perform abstractive summarization
        output_file.write("=== Abstractive Summary (OpenAI) ===\n")
        abstractive_summary = abstractive_summarize(article_text)
        output_file.write(abstractive_summary + "\n")
        output_file.write(f"\nAbstractive Summary Length: {len(abstractive_summary.split())} words\n")
        
        # Generate and write comparison report
        output_file.write("\n=== COMPARISON REPORT ===\n")
        comparison_report = generate_comparison_report(article_text, extractive_summary, abstractive_summary)
        output_file.write(comparison_report)
    
    print("Summarization completed. Results saved to 'summarization_results.txt'")

if __name__ == "__main__":
    main() 