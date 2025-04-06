# Text Analysis Agent

## Project Overview
This project implements a comparative text analysis system that evaluates two different approaches to text summarization:
1. **Extractive Summarization**: Uses NLTK and TextRank algorithm to select key sentences from the original text
2. **Abstractive Summarization**: Employs OpenAI's GPT model to generate paraphrased summaries

The system processes text data from CSV files and generates comprehensive reports comparing these approaches based on:
- Summary lengths
- Execution times
- ROUGE metrics for summary quality
- Visualization of comparative metrics

## Tools and Technologies Used

### Core Libraries
- **NLTK**: Natural Language Toolkit for text processing and extractive summarization
  - Used for tokenization, stop words removal, and text preprocessing
  - Implements TextRank algorithm for key sentence extraction
- **OpenAI API**: For abstractive summarization using GPT-3.5
  - Provides high-quality paraphrased summaries
  - Offers consistent and coherent output

### Analysis and Processing
- **NetworkX**: Implementation of TextRank algorithm and graph-based text analysis
- **NumPy**: Efficient numerical computations and matrix operations
- **Pandas**: CSV file handling and data manipulation
- **ROUGE**: Evaluation metrics for summary quality

### Visualization and Output
- **Matplotlib**: Data visualization and metric comparisons
- **JSON**: Structured output format for analysis results
- **tqdm**: Progress tracking for batch processing

## Setup Instructions

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure OpenAI API:
   - Rename `.env` to `.env`
   - Add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Prepare your input data:
   - Use a CSV file with a text column
   - Default configuration expects a column named 'Text'

5. Run the analysis:
```bash
python main.py csv your_file.csv --text-column Text --output analysis.json --visualize
```

### Command Line Arguments
- `csv`: Input format (currently only CSV is supported)
- `your_file.csv`: Path to input CSV file
- `--text-column`: Name of the column containing text to analyze
- `--output`: Path for the output JSON file
- `--visualize`: (Optional) Generate visualization charts

## Output
The program generates:
1. **analysis.json**: Contains detailed metrics including:
   - Original text and summary lengths
   - Execution times for both methods
   - ROUGE scores comparing summary quality
   - Individual results for each processed text
   - Average metrics across all processed texts

2. **analysis_visualization.png**: Visual representation of:
   - Text length comparisons
   - Execution time comparisons
   - ROUGE scores

## Performance Insights
Based on initial analysis:
- Extractive summarization is significantly faster (~0.006s vs ~1.14s)
- Abstractive summaries tend to be longer and more detailed
- ROUGE scores indicate moderate overlap between both approaches
- Each method has its strengths:
  - Extractive: Speed and original text preservation
  - Abstractive: Coherence and paraphrasing ability
