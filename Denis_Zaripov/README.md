# Review Summarization Comparison

This project implements and compares two different approaches to review summarization:
1. Extractive Summarization using VADER sentiment analysis
2. Abstractive Summarization using CrewAI and LLM

## Features

- Extractive summarization using VADER sentiment analysis
- Abstractive summarization using CrewAI framework
- Comparison of both approaches
- Processing of Amazon product reviews dataset

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python review_summarizer.py
```

## Comparison of Approaches

### Extractive Summarization (VADER)
- Uses a lexicon-based approach
- Assigns sentiment scores to words
- Considers word modifiers and context
- Fast and rule-based
- Good for quick sentiment analysis
- Less flexible but more consistent

### Abstractive Summarization (CrewAI)
- Uses LLM-based approach
- Creates new, concise summaries
- More natural language generation
- Better at capturing context and nuance
- More computationally intensive
- More flexible but may be less consistent

## Dataset

The project uses the "arhamrumi/amazon-product-reviews" dataset from Hugging Face.

## Requirements

See requirements.txt for full list of dependencies. 

---

## Example OUTPUTS


Comparing results...

=== COMPREHENSIVE COMPARISON ===
Total reviews processed: 50

Extractive Sentiment Distribution:
  positive: 45 (90.0%)
  negative: 5 (10.0%)

Abstractive Sentiment Distribution:
  positive: 37 (74.0%)
  negative: 12 (24.0%)
  neutral: 1 (2.0%)

Average Compound Score (Extractive): 0.695
Agreement between approaches: 84.0%

=== SAMPLE RESULTS ===

Review 1:
Original text: This has easily become our favorite flavored coffee! From the moment it begins brewing, sharing a whiff of the tropics to the last sip in the cup it delights the senses! I usually save flavored coffee...

Extractive Analysis:
Sentiment: positive
Compound Score: 0.8743

Abstractive Analysis:
This review expresses that the flavored coffee has become a favorite, providing a delightful sensory experience from brewing to sipping. The sentiment is classified as positive.
--------------------------------------------------------------------------------

Review 2:
Original text: LOVE this product.  I put a tablespoon of it into my smoothies every morning....

Extractive Analysis:
Sentiment: positive
Compound Score: 0.7125

Abstractive Analysis:
The customer expresses strong enthusiasm for the product, highlighting that they incorporate it into their daily smoothies. Sentiment classification: Positive.
--------------------------------------------------------------------------------

Review 3:
Original text: It was OK, but nothing to rave about.  I generally eat a lot of chocolate and candy, but the thought of eating more than one little bar of this stuff every couple of days is not at all appealing to me...

Extractive Analysis:
Sentiment: negative
Compound Score: -0.4782

Abstractive Analysis:
The reviewer finds the product to be mediocre and not worth purchasing in bulk, suggesting that others should spend their money on better options. Sentiment classification: negative.
--------------------------------------------------------------------------------

Review 4:
Original text: Baby was just ok with this one, slow to eat it and didn't finish.  I thought it was great though......

Extractive Analysis:
Sentiment: positive
Compound Score: 0.743

Abstractive Analysis:
The review indicates that the baby was not very enthusiastic about the product, eating slowly and not finishing it, while the reviewer personally thought it was great. Sentiment classification: neutral.
--------------------------------------------------------------------------------

Review 5:
Original text: This is definitely a great product since all the ingredients are quality stuff. However, like some reviewers have stated or I read from the label about how some dogs can't take the 95% meat contend. M...

Extractive Analysis:
Sentiment: positive
Compound Score: 0.87

Abstractive Analysis:
This review highlights that the product is of high quality and is loved by the dog, but it also notes that some dogs may experience digestive issues due to the high meat content. The reviewer recommends using a small amount mixed with dry food to avoid problems. Sentiment classification: positive.