import pandas as pd
import random
import os

def extract_sample_reviews(input_file: str, output_file: str, sample_size: int = 10, random_seed: int = 42):
    """
    Extract a sample of reviews from a large CSV file.
    
    Args:
        input_file: Path to the input CSV file containing all reviews
        output_file: Path to save the sample CSV file
        sample_size: Number of reviews to extract
        random_seed: Random seed for reproducibility
    """
    print(f"Extracting {sample_size} reviews from {input_file}...")
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist.")
        return
    
    try:
        # Check if the file is large (>100MB)
        file_size = os.path.getsize(input_file) / (1024 * 1024)  # Size in MB
        
        if file_size > 100:
            # For very large files, read in chunks and sample
            print(f"Large file detected ({file_size:.1f} MB). Reading in chunks...")
            
            # Count total rows first (skip header)
            with open(input_file, 'r') as f:
                total_rows = sum(1 for _ in f) - 1
            
            # Generate random indices to sample
            if total_rows <= sample_size:
                indices = list(range(1, total_rows + 1))  # All rows except header
            else:
                indices = sorted(random.sample(range(1, total_rows + 1), sample_size))
            
            # Read only the header and selected rows
            sampled_chunks = []
            sampled_chunks.append(pd.read_csv(input_file, nrows=0))  # Just the header
            
            for i, index in enumerate(indices):
                chunk = pd.read_csv(input_file, skiprows=range(1, index), nrows=1)
                sampled_chunks.append(chunk)
                print(f"Extracted review {i+1}/{sample_size}")
            
            sample_df = pd.concat(sampled_chunks)
        else:
            # For smaller files, read entirely and sample
            df = pd.read_csv(input_file)
            sample_df = df.sample(min(sample_size, len(df)), random_state=random_seed)
        
        # Save the sample
        sample_df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(sample_df)} reviews to {output_file}")
        
    except Exception as e:
        print(f"Error extracting reviews: {e}")

if __name__ == "__main__":
    # Extract a sample of reviews from the large Reviews.csv file
    extract_sample_reviews("Reviews.csv", "SampleReviews.csv", sample_size=20)
    
    # To use the First10Reviews.csv file that's already provided:
    print("\nTo use the existing sample file, run: python main_agent.py --input First10Reviews.csv") 