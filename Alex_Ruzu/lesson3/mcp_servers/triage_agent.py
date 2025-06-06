import os
import csv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = "gpt-4o-mini"
client = OpenAI()

TRIAGE_PROMPT = (
    "You are an expert product analyst. "
    "Classify the following user review as one of: 'bug report', 'feature request', or 'other' (for positive, irrelevant, or unclear feedback). "
    "Reply with only the class label.\n"
    "Review: {review}\nClassification:"
)

input_path = os.path.join(os.path.dirname(__file__), "..", "data", "viber.csv")
output_path = os.path.join(os.path.dirname(__file__), "..", "data", "viber_classified.csv")

def classify_reviews(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["classification"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(reader):
            if i >= 10:
                break
            review = row["content"]
            prompt = TRIAGE_PROMPT.format(review=review)
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            classification = response.choices[0].message.content.strip().lower()
            row["classification"] = classification
            writer.writerow(row)
    print(f"Classification complete. Results saved to {output_path}")

def main():
    classify_reviews(input_path, output_path)

if __name__ == "__main__":
    main() 