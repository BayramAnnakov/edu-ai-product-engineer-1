# Text Summarization Project

A Python-based text summarization tool that provides both extractive and abstractive summarization capabilities. This project demonstrates two different approaches to text summarization using NLTK for extractive summarization and OpenAI's GPT-3.5 for abstractive summarization.

## Features

- **Extractive Summarization**: Uses NLTK to identify and extract the most important sentences from the original text
- **Abstractive Summarization**: Leverages OpenAI's GPT-3.5 to generate new, concise summaries
- **Comparison Analysis**: Provides detailed comparison between both summarization approaches
- **Detailed Reports**: Generates comprehensive reports including length analysis, content coverage, and recommendations

## Prerequisites

- Python 3.6 or higher
- OpenAI API key
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Place your text file (e.g., `article_new.txt`) in the project directory
2. Run the summarization script:
```bash
python summarization_demo.py
```

3. The results will be saved in `summarization_results.txt`, containing:
   - Original article length
   - Extractive summary
   - Abstractive summary
   - Detailed comparison report

## Project Structure

```
.
├── README.md
├── requirements.txt
├── summarization_demo.py
├── article_new.txt
└── summarization_results.txt
```

## Dependencies

- nltk==3.8.1
- openai>=1.0.0
- python-dotenv==1.0.1

## How It Works

### Extractive Summarization
- Uses NLTK's sentence tokenization
- Implements word frequency analysis
- Removes stopwords and punctuation
- Selects most important sentences based on word frequency

### Abstractive Summarization
- Uses OpenAI's GPT-3.5 model
- Generates new, concise summaries
- Maintains semantic meaning while being more concise

### Comparison Report
- Analyzes compression ratios
- Compares content coverage
- Provides recommendations for each approach
- Calculates similarity between summaries

## Output Example

The program generates a detailed report including:
- Original text length
- Extractive summary with length
- Abstractive summary with length
- Comprehensive comparison analysis
- Usage recommendations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NLTK for natural language processing capabilities
- OpenAI for their GPT-3.5 API
- The Python community for their excellent tools and libraries 