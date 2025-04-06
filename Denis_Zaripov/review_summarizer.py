import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from crewai import Agent, Task, Crew, Process
import pandas as pd
import numpy as np
from langchain_openai import ChatOpenAI
import time
from collections import Counter

# Disable telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"

class ReviewSummarizer:
    def __init__(self):
        # Load reviews from local CSV file
        self.reviews_df = pd.read_csv('Reviews.csv')
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize OpenAI model with lower temperature for more concise outputs
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0.3,  # Lower temperature for more focused outputs
            max_tokens=150    # Limit token usage
        )
        
    def extractive_summarization(self, text):
        """
        Extractive summarization using VADER sentiment analysis
        """
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
        compound_score = sentiment_scores['compound']
        
        # Classify based on compound score
        if compound_score >= 0.05:
            sentiment = "positive"
        elif compound_score <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            'sentiment': sentiment,
            'compound_score': compound_score,
            'scores': sentiment_scores
        }
    
    def abstractive_summarization(self, text):
        """
        Abstractive summarization using CrewAI and OpenAI GPT-4-mini with minimal token usage
        """
        # Create a single agent for both summarization and sentiment analysis
        review_agent = Agent(
            role='Review Analyzer',
            goal='Create concise summaries and analyze sentiment of customer reviews',
            backstory='Expert in natural language processing and sentiment analysis',
            verbose=True,
            llm=self.llm
        )
        
        # Create a single task that combines summarization and sentiment analysis
        combined_task = Task(
            description=f"Review: {text}\n\nProvide a brief summary (max 2 sentences) and classify sentiment as positive, negative, or neutral.",
            agent=review_agent,
            expected_output="A very concise summary and sentiment classification (positive/negative/neutral)."
        )
        
        # Create and run the crew with a single agent and task
        crew = Crew(
            agents=[review_agent],
            tasks=[combined_task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return result
    
    def process_all_reviews(self, num_samples=None):
        """
        Process all reviews with extractive first, then abstractive
        """
        # If num_samples is provided, take a random sample
        if num_samples:
            reviews_df = self.reviews_df.sample(n=min(num_samples, len(self.reviews_df)))
        else:
            reviews_df = self.reviews_df
            
        # Process all reviews with extractive first
        print("Processing all reviews with extractive algorithm...")
        extractive_results = []
        processed_count = 0
        for _, row in reviews_df.iterrows():
            review_text = row['Text']
            extractive_result = self.extractive_summarization(review_text)
            extractive_results.append({
                'text': review_text,
                'result': extractive_result
            })
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"Processed {processed_count} reviews with extractive algorithm")
        
        # Process all reviews with abstractive
        print("\nProcessing all reviews with abstractive algorithm...")
        abstractive_results = []
        processed_count = 0
        for _, row in reviews_df.iterrows():
            review_text = row['Text']
            abstractive_result = self.abstractive_summarization(review_text)            
            abstractive_results.append({
                'text': review_text,
                'result': abstractive_result
            })
            processed_count += 1
            if processed_count % 5 == 0:
                print(f"Processed {processed_count} reviews with abstractive algorithm")
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Compare results
        print("\nComparing results...")
        comparison_results = []
        for i in range(len(extractive_results)):
            comparison = {
                'text': extractive_results[i]['text'],
                'extractive': extractive_results[i]['result'],
                'abstractive': abstractive_results[i]['result']
            }
            comparison_results.append(comparison)
        
        return comparison_results
    
    def analyze_results(self, results):
        """
        Analyze and compare the results of both algorithms
        """
        # Extract sentiments from both approaches
        extractive_sentiments = [r['extractive']['sentiment'] for r in results]
        
        # Count sentiments for extractive approach
        extractive_counts = Counter(extractive_sentiments)
        
        # Extract compound scores for extractive approach
        compound_scores = [r['extractive']['compound_score'] for r in results]
        
        # Calculate average compound score
        avg_compound_score = sum(compound_scores) / len(compound_scores) if compound_scores else 0
        
        # Analyze abstractive results
        # Since abstractive results are CrewOutput objects, we need to convert them to strings
        abstractive_sentiments = []
        for result in results:
            # Convert CrewOutput to string
            abstractive_text = str(result['abstractive'])
            # Simple keyword-based extraction from abstractive results
            if 'positive' in abstractive_text.lower():
                abstractive_sentiments.append('positive')
            elif 'negative' in abstractive_text.lower():
                abstractive_sentiments.append('negative')
            else:
                abstractive_sentiments.append('neutral')
        
        # Count sentiments for abstractive approach
        abstractive_counts = Counter(abstractive_sentiments)
        
        # Calculate agreement between approaches
        agreement_count = sum(1 for i in range(len(results)) 
                             if extractive_sentiments[i] == abstractive_sentiments[i])
        agreement_percentage = (agreement_count / len(results)) * 100 if results else 0
        
        # Prepare comparison summary
        comparison_summary = {
            'total_reviews': len(results),
            'extractive_sentiment_distribution': dict(extractive_counts),
            'abstractive_sentiment_distribution': dict(abstractive_counts),
            'average_compound_score': avg_compound_score,
            'agreement_percentage': agreement_percentage,
            'sample_results': results[:5]  # Include first 5 results as samples
        }
        
        return comparison_summary

def main():
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it using: export OPENAI_API_KEY='your-api-key'")
        return
        
    summarizer = ReviewSummarizer()
    
    # Process all reviews
    num_samples = 50  # Set to None to process all reviews
    results = summarizer.process_all_reviews(num_samples=num_samples)
    
    # Analyze and compare results
    comparison_summary = summarizer.analyze_results(results)
    
    # Print detailed comparison
    print("\n=== COMPREHENSIVE COMPARISON ===")
    print(f"Total reviews processed: {comparison_summary['total_reviews']}")
    
    print("\nExtractive Sentiment Distribution:")
    for sentiment, count in comparison_summary['extractive_sentiment_distribution'].items():
        percentage = (count / comparison_summary['total_reviews']) * 100
        print(f"  {sentiment}: {count} ({percentage:.1f}%)")
    
    print("\nAbstractive Sentiment Distribution:")
    for sentiment, count in comparison_summary['abstractive_sentiment_distribution'].items():
        percentage = (count / comparison_summary['total_reviews']) * 100
        print(f"  {sentiment}: {count} ({percentage:.1f}%)")
    
    print(f"\nAverage Compound Score (Extractive): {comparison_summary['average_compound_score']:.3f}")
    print(f"Agreement between approaches: {comparison_summary['agreement_percentage']:.1f}%")
    
    print("\n=== SAMPLE RESULTS ===")
    for i, result in enumerate(comparison_summary['sample_results']):
        print(f"\nReview {i+1}:")
        print(f"Original text: {result['text'][:200]}...")
        print("\nExtractive Analysis:")
        print(f"Sentiment: {result['extractive']['sentiment']}")
        print(f"Compound Score: {result['extractive']['compound_score']}")
        print("\nAbstractive Analysis:")
        print(str(result['abstractive']))  # Convert CrewOutput to string for printing
        print("-" * 80)

if __name__ == "__main__":
    main() 