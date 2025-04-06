import argparse
import json
import time
from pathlib import Path
import pandas as pd
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
from rouge import Rouge
import networkx as nx
from openai import OpenAI
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
from tqdm import tqdm

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class TextAnalysisAgent:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.rouge = Rouge()
        
    def read_csv(self, file_path, text_column):
        """Read and preprocess the CSV file."""
        df = pd.read_csv(file_path)
        return df[text_column].tolist()

    def extractive_summarize(self, text):
        """Implement extractive summarization using TextRank algorithm."""
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return text
        
        # Generate similarity matrix
        similarity_matrix = self._generate_similarity_matrix(sentences)
        
        try:
            # Calculate scores using PageRank algorithm with adjusted parameters
            nx_graph = nx.from_numpy_array(similarity_matrix)
            scores = nx.pagerank(nx_graph, max_iter=200, tol=1e-6)
            
            # Get top sentences (up to 3 or 30% of total sentences, whichever is smaller)
            max_sentences = min(3, max(1, len(sentences) // 3))
            ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
            summary = " ".join([s for _, s in ranked_sentences[:max_sentences]])
            
            return summary
        except (nx.PowerIterationFailedConvergence, ValueError):
            # Fallback: return first few sentences if PageRank fails
            return " ".join(sentences[:3])

    def _generate_similarity_matrix(self, sentences):
        """Generate similarity matrix for sentences."""
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        stop_words = set(stopwords.words('english'))

        for idx1 in range(len(sentences)):
            for idx2 in range(len(sentences)):
                if idx1 != idx2:
                    similarity_matrix[idx1][idx2] = self._sentence_similarity(
                        sentences[idx1], sentences[idx2], stop_words)
        
        # Normalize the matrix to ensure convergence
        row_sums = similarity_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        similarity_matrix = similarity_matrix / row_sums[:, np.newaxis]
        
        return similarity_matrix

    def _sentence_similarity(self, sent1, sent2, stop_words):
        """Calculate similarity between two sentences."""
        words1 = [word.lower() for word in word_tokenize(sent1) if word.isalnum()]
        words2 = [word.lower() for word in word_tokenize(sent2) if word.isalnum()]
        
        words1 = [w for w in words1 if w not in stop_words]
        words2 = [w for w in words2 if w not in stop_words]
        
        if not words1 or not words2:
            return 0.0
        
        all_words = list(set(words1 + words2))
        
        vector1 = [1 if w in words1 else 0 for w in all_words]
        vector2 = [1 if w in words2 else 0 for w in all_words]
        
        # Calculate cosine similarity with error handling
        try:
            dot_product = np.dot(vector1, vector2)
            norm1 = np.sqrt(np.dot(vector1, vector1))
            norm2 = np.sqrt(np.dot(vector2, vector2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except:
            return 0.0

    def abstractive_summarize(self, text):
        """Implement abstractive summarization using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a text summarization assistant. Provide a very concise summary in 1-2 sentences."},
                    {"role": "user", "content": text}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in abstractive summarization: {e}")
            return text[:200] + "..."  # Fallback to truncation

    def analyze_batch(self, texts, batch_size=5):
        """Analyze a batch of texts at once."""
        all_results = []
        
        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            # First do all extractive summaries (fast)
            extractive_summaries = []
            for text in batch:
                start_time = time.time()
                summary = self.extractive_summarize(text)
                extractive_time = time.time() - start_time
                extractive_summaries.append((summary, extractive_time))
            
            # Then do all abstractive summaries (slow but can be parallelized in future)
            abstractive_summaries = []
            for text in batch:
                start_time = time.time()
                summary = self.abstractive_summarize(text)
                abstractive_time = time.time() - start_time
                abstractive_summaries.append((summary, abstractive_time))
            
            # Combine results
            for j in range(len(batch)):
                text = batch[j]
                extractive_summary, extractive_time = extractive_summaries[j]
                abstractive_summary, abstractive_time = abstractive_summaries[j]
                
                try:
                    rouge_scores = self.rouge.get_scores(abstractive_summary, extractive_summary)[0]
                except:
                    rouge_scores = {
                        "rouge-1": {"f": 0.0},
                        "rouge-2": {"f": 0.0},
                        "rouge-l": {"f": 0.0}
                    }
                
                result = {
                    "original_text_length": len(text),
                    "extractive_summary_length": len(extractive_summary),
                    "abstractive_summary_length": len(abstractive_summary),
                    "execution_time_extractive": extractive_time,
                    "execution_time_abstractive": abstractive_time,
                    "rouge_score": {
                        "rouge-1": rouge_scores["rouge-1"]["f"],
                        "rouge-2": rouge_scores["rouge-2"]["f"],
                        "rouge-l": rouge_scores["rouge-l"]["f"]
                    },
                    "summaries": {
                        "extractive": extractive_summary,
                        "abstractive": abstractive_summary
                    }
                }
                batch_results.append(result)
            
            all_results.extend(batch_results)
        
        return all_results

    def analyze_text(self, text):
        """Analyze text using both summarization methods and generate report."""
        # Extractive summarization
        start_time = time.time()
        extractive_summary = self.extractive_summarize(text)
        extractive_time = time.time() - start_time

        # Abstractive summarization
        start_time = time.time()
        abstractive_summary = self.abstractive_summarize(text)
        abstractive_time = time.time() - start_time

        # Calculate ROUGE scores
        try:
            rouge_scores = self.rouge.get_scores(abstractive_summary, extractive_summary)[0]
        except:
            rouge_scores = {
                "rouge-1": {"f": 0.0},
                "rouge-2": {"f": 0.0},
                "rouge-l": {"f": 0.0}
            }

        return {
            "original_text_length": len(text),
            "extractive_summary_length": len(extractive_summary),
            "abstractive_summary_length": len(abstractive_summary),
            "execution_time_extractive": extractive_time,
            "execution_time_abstractive": abstractive_time,
            "rouge_score": {
                "rouge-1": rouge_scores["rouge-1"]["f"],
                "rouge-2": rouge_scores["rouge-2"]["f"],
                "rouge-l": rouge_scores["rouge-l"]["f"]
            },
            "summaries": {
                "extractive": extractive_summary,
                "abstractive": abstractive_summary
            }
        }

    def visualize_results(self, results):
        """Create visualizations for the analysis results."""
        plt.figure(figsize=(15, 5))

        # Plot 1: Summary lengths comparison
        plt.subplot(1, 3, 1)
        lengths = [
            results['original_text_length'],
            results['extractive_summary_length'],
            results['abstractive_summary_length']
        ]
        plt.bar(['Original', 'Extractive', 'Abstractive'], lengths)
        plt.title('Text Length Comparison')
        plt.ylabel('Number of characters')
        plt.xticks(rotation=45)

        # Plot 2: Execution times
        plt.subplot(1, 3, 2)
        times = [
            results['execution_time_extractive'],
            results['execution_time_abstractive']
        ]
        plt.bar(['Extractive', 'Abstractive'], times)
        plt.title('Execution Time Comparison')
        plt.ylabel('Seconds')
        plt.xticks(rotation=45)

        # Plot 3: ROUGE scores
        plt.subplot(1, 3, 3)
        scores = [
            results['rouge_score']['rouge-1'],
            results['rouge_score']['rouge-2'],
            results['rouge_score']['rouge-l']
        ]
        plt.bar(['ROUGE-1', 'ROUGE-2', 'ROUGE-L'], scores)
        plt.title('ROUGE Scores')
        plt.ylabel('Score')
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig('analysis_visualization.png')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description='Text Analysis Agent')
    parser.add_argument('format', choices=['csv'], help='Input format')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('--text-column', required=True, help='Column name containing text')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')

    args = parser.parse_args()

    agent = TextAnalysisAgent()
    texts = agent.read_csv(args.input, args.text_column)

    # Process texts in batches
    with tqdm(total=min(10, len(texts)), desc="Analyzing texts") as pbar:
        all_results = agent.analyze_batch(texts[:10], batch_size=args.batch_size)  # Process first 10 reviews
        pbar.update(len(all_results))

    # Calculate average metrics
    avg_results = {
        "average_metrics": {
            "avg_original_length": sum(r["original_text_length"] for r in all_results) / len(all_results),
            "avg_extractive_length": sum(r["extractive_summary_length"] for r in all_results) / len(all_results),
            "avg_abstractive_length": sum(r["abstractive_summary_length"] for r in all_results) / len(all_results),
            "avg_extractive_time": sum(r["execution_time_extractive"] for r in all_results) / len(all_results),
            "avg_abstractive_time": sum(r["execution_time_abstractive"] for r in all_results) / len(all_results),
            "avg_rouge_1": sum(r["rouge_score"]["rouge-1"] for r in all_results) / len(all_results),
            "avg_rouge_2": sum(r["rouge_score"]["rouge-2"] for r in all_results) / len(all_results),
            "avg_rouge_l": sum(r["rouge_score"]["rouge-l"] for r in all_results) / len(all_results)
        },
        "individual_results": all_results
    }

    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(avg_results, f, indent=2)

    if args.visualize:
        agent.visualize_results(all_results[0])  # Visualize first result as example

if __name__ == "__main__":
    main()
