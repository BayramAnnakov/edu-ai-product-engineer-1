import matplotlib.pyplot as plt
import numpy as np
from typing import Dict
from utils import get_metrics, print_metrics

def analyze_summaries(original_text: str, 
                     extractive_summary: str, 
                     abstractive_summary: str,
                     extractive_time: float,
                     abstractive_time: float,
                     output_file: str = 'summary_comparison.png') -> str:
    """Perform comprehensive analysis of summaries including metrics and visualization."""
    try:
        # Basic validation
        if not extractive_summary or not abstractive_summary:
            raise ValueError("Summaries cannot be empty")
            
        # Calculate metrics
        original_metrics = get_metrics(original_text)
        extractive_metrics = get_metrics(extractive_summary)
        abstractive_metrics = get_metrics(abstractive_summary)
        
        # Simple debug print
        print("\nSummary Lengths:")
        print(f"Extractive: {len(extractive_summary)} chars, Metrics: {extractive_metrics}")
        print(f"Abstractive: {len(abstractive_summary)} chars, Metrics: {abstractive_metrics}")
        
        # Print metrics and generate visualization
        print_metrics(original_metrics, extractive_metrics, abstractive_metrics, 
                     extractive_time, abstractive_time)
        return generate_visualization(extractive_metrics, abstractive_metrics, output_file)
        
    except Exception as e:
        print(f"Error in analyze_summaries: {e}")
        import traceback
        traceback.print_exc()
        return "Error analyzing summaries."

def generate_visualization(extractive_metrics: Dict[str, float], 
                         abstractive_metrics: Dict[str, float],
                         output_file: str = 'summary_comparison.png') -> str:
    """Generate a visualization comparing the summaries."""
    try:
        # Verify input types and print debug info
        print("\n=== Visualization Input Debug ===")
        print("Extractive Metrics:", extractive_metrics)
        print("Abstractive Metrics:", abstractive_metrics)
        
        if not isinstance(extractive_metrics, dict) or not isinstance(abstractive_metrics, dict):
            raise ValueError("Metrics must be dictionaries")
            
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Define consistent colors and width
        extractive_color = '#1f77b4'  # blue
        abstractive_color = '#ff7f0e'  # orange
        width = 0.35
        
        # Plot 1: Character and Word Counts
        metrics1 = ['characters', 'words']
        x1 = range(len(metrics1))
        
        # Get values, ensuring they're positive numbers
        extractive_values1 = [max(0, extractive_metrics.get(m, 0)) for m in metrics1]
        abstractive_values1 = [max(0, abstractive_metrics.get(m, 0)) for m in metrics1]
        
        # Create bars
        bars1 = ax1.bar([i - width/2 for i in x1], 
                       extractive_values1, 
                       width, 
                       label='Extractive', 
                       color=extractive_color)
        bars2 = ax1.bar([i + width/2 for i in x1], 
                       abstractive_values1, 
                       width, 
                       label='Abstractive', 
                       color=abstractive_color)
        
        # Add value labels
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}',
                        ha='center', va='bottom')
        
        autolabel(bars1)
        autolabel(bars2)
        
        # Customize first plot
        ax1.set_ylabel('Count')
        ax1.set_title('Character and Word Counts')
        ax1.set_xticks(x1)
        ax1.set_xticklabels(['Characters', 'Words'])
        ax1.legend()
        
        # Ensure y-axis starts at 0 and has some padding at the top
        ax1.set_ylim(bottom=0, top=max(max(extractive_values1), max(abstractive_values1)) * 1.15)
        
        # Plot 2: Sentence Metrics
        metrics2 = ['sentences', 'avg_words_per_sentence']
        x2 = range(len(metrics2))
        
        # Get values, ensuring they're positive numbers
        extractive_values2 = [max(0, extractive_metrics.get(m, 0)) for m in metrics2]
        abstractive_values2 = [max(0, abstractive_metrics.get(m, 0)) for m in metrics2]
        
        # Create bars
        bars3 = ax2.bar([i - width/2 for i in x2],
                       extractive_values2,
                       width, 
                       label='Extractive', 
                       color=extractive_color)
        bars4 = ax2.bar([i + width/2 for i in x2],
                       abstractive_values2,
                       width, 
                       label='Abstractive', 
                       color=abstractive_color)
        
        # Add value labels with appropriate formatting
        def autolabel_float(bars):
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom')
        
        autolabel_float(bars3)
        autolabel_float(bars4)
        
        # Customize second plot
        ax2.set_ylabel('Count / Average')
        ax2.set_title('Sentence Metrics')
        ax2.set_xticks(x2)
        ax2.set_xticklabels(['Number of\nSentences', 'Avg Words per\nSentence'])
        ax2.legend()
        
        # Ensure y-axis starts at 0 and has some padding at the top
        ax2.set_ylim(bottom=0, top=max(max(extractive_values2), max(abstractive_values2)) * 1.15)
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
        
    except Exception as e:
        print(f"Error generating visualization: {e}")
        import traceback
        traceback.print_exc()
        return "Error generating visualization." 