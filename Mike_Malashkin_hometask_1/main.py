import os
from processor import process_reviews, analyze_results
import json
from datetime import datetime

def main():
    """Main entry point for the project."""
    print("Starting the summarization project...")
    
    # Step 1: Process reviews from Reviews.csv
    print("\nStep 1: Processing reviews...")
    output_file = process_reviews()
    
    if not output_file:
        print("Failed to process reviews. Exiting...")
        return
    
    # Step 2: Load the processed results
    print("\nStep 2: Analyzing results...")
    with open(output_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Step 3: Analyze the results
    analysis = analyze_results(results)
    
    # Step 4: Save the analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_file = f"summarization_comparison_{timestamp}.json"
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=4)
    
    print(f"\nAnalysis saved to {analysis_file}")
    print("\nProject completed successfully!")

if __name__ == "__main__":
    main() 