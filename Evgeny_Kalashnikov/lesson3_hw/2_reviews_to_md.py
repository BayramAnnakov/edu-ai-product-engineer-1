import pandas as pd
import os

# --- Configuration ---
INPUT_CSV = "1_filter_reviews.csv"
OUTPUT_MD = "Evgeny_Kalashnikov/lesson3_hw/netflix.md"
FIELDS = ["author_name", "review_timestamp", "review_text", "classification_type", "classification_reasoning"]
MAX_TOTAL = 15
MAX_PER_TYPE = 7

CAPTION = "# Netflix Reviews Analysis\n"
EXPLANATION = (
    "This document presents a selection of 15 Netflix reviews, automatically classified into three categories: "
    "bug report, feature requests, and other. Each review includes the author, timestamp, text, classification, and the reasoning behind the classification. "
    "No more than 7 reviews of each type are included."
)


def main():
    # Read the CSV
    df = pd.read_csv(INPUT_CSV)

    # Prepare counters and selection
    selected = []
    type_counts = {t: 0 for t in df["classification_type"].unique()}

    for _, row in df.iterrows():
        t = row["classification_type"]
        if type_counts.get(t, 0) < MAX_PER_TYPE and len(selected) < MAX_TOTAL:
            selected.append(row)
            type_counts[t] = type_counts.get(t, 0) + 1
        if len(selected) >= MAX_TOTAL:
            break

    # Write to markdown
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(CAPTION + "\n")
        f.write(EXPLANATION + "\n\n")
        for i, row in enumerate(selected, 1):
            f.write(f"### Review {i}\n")
            for field in FIELDS:
                value = row.get(field, "")
                f.write(f"**{field.replace('_', ' ').title()}:** {value}\n\n")
            f.write("---\n\n")

    print(f"Markdown file saved to {OUTPUT_MD}")

if __name__ == "__main__":
    main() 