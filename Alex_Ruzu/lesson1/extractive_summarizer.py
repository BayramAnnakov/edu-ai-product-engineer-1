import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from string import punctuation
from heapq import nlargest
from collections import defaultdict

# Download required NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

def extractive_summarize(text, num_sentences=5):
    """
    Generate an extractive summary using NLTK.
    This approach selects the most important sentences based on word frequency.
    """
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # Tokenize words and remove stopwords
    stop_words = set(stopwords.words('english') + list(punctuation))
    word_freq = defaultdict(int)
    
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        for word in words:
            if word not in stop_words:
                word_freq[word] += 1
    
    # Calculate sentence scores based on word frequencies
    sentence_scores = defaultdict(int)
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        for word in words:
            if word in word_freq:
                sentence_scores[sentence] += word_freq[word]
    
    # Get the top sentences
    summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    
    # Join sentences to create summary
    summary = ' '.join(summary_sentences)
    return summary

if __name__ == "__main__":
    # Example usage
    text = """
    There's a lot of chatter in the media that software developers will soon lose their jobs to AI. 
    I don't buy it. It is not the end of programming. It is the end of programming as we know it today. 
    That is not new. The first programmers connected physical circuits to perform each calculation. 
    They were succeeded by programmers writing machine instructions as binary code to be input one bit at a time 
    by flipping switches on the front of a computer. Assembly language programming then put an end to that. 
    It lets a programmer use a human-like language to tell the computer to move data to locations in memory 
    and perform calculations on it. Then, development of even higher-level compiled languages like Fortran, 
    COBOL, and their successors C, C++, and Java meant that most programmers no longer wrote assembly code. 
    Instead, they could express their wishes to the computer using higher level abstractions.
    """
    
    summary = extractive_summarize(text, num_sentences=3)
    print("Extractive Summary:")
    print(summary) 