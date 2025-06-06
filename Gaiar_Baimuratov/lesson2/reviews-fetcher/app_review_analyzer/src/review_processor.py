"""
Review processing functionality for app review analysis.

This module provides functions to process app reviews, including:
- Chunking reviews into manageable pieces for LLM processing
- Extracting feature requests from reviews using GPT-4o
- Grouping and refining extracted features
- Generating interview questions for feature topics
"""

import json
from typing import List
import os
from dotenv import load_dotenv

import tiktoken
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def load_reviews(file_path: str) -> List[str]:
    """
    Load reviews from a JSON file.

    Args:
        file_path: Path to the JSON file containing reviews.

    Returns:
        List of review text strings.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract just the review text
    reviews = []
    for review in data.get("results", []):
        if review.get("body"):  # Make sure there's actual review text
            reviews.append(review["body"])

    return reviews


def chunk_reviews(reviews: List[str], max_tokens: int = 8192) -> List[List[str]]:
    """
    Chunk reviews to ensure they fit within token limits.

    Args:
        reviews: List of review text strings.
        max_tokens: Maximum number of tokens per chunk. Default is 8192 for GPT-4o.

    Returns:
        List of lists, where each inner list is a chunk of reviews.
    """
    # Get the encoding for GPT-4o
    encoding = tiktoken.encoding_for_model("gpt-4o")

    chunks = []
    current_chunk = []
    current_token_count = 0

    # Reserve tokens for prompt overhead (system message, instructions, etc.)
    prompt_overhead = 500  # Adjust based on actual prompt size
    effective_max_tokens = max_tokens - prompt_overhead

    for review in reviews:
        # Count tokens for this review
        review_tokens = len(encoding.encode(review))

        # Check if adding this review would exceed the token limit
        if current_token_count + review_tokens > effective_max_tokens and current_chunk:
            # Save the current chunk and start a new one
            chunks.append(current_chunk)
            current_chunk = []
            current_token_count = 0

        # Handle reviews that are too large on their own
        if review_tokens > effective_max_tokens:
            # In a real implementation, we'd need to split the review itself
            # For now, we'll just truncate
            truncated_review = review[
                : int(len(review) * (effective_max_tokens / review_tokens))
            ]
            # Put the truncated review in its own chunk
            chunks.append([truncated_review])
            # Continue with an empty chunk
            current_chunk = []
            current_token_count = 0
        else:
            # Add the review to the current chunk
            current_chunk.append(review)
            current_token_count += review_tokens

    # Add the final chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def extract_features_from_chunk(chunk: List[str], client=None) -> List[str]:
    """
    Extract feature requests from a chunk of reviews using GPT-4o.

    Args:
        chunk: List of review text strings.
        client: OpenAI client instance. If None, use the global instance.

    Returns:
        List of extracted feature request strings.
    """
    # Use provided client or global client
    api_client = client or openai_client

    if not api_client:
        raise ValueError("No OpenAI client available. Please provide API key.")

    # Format the reviews into a single string for the prompt
    reviews_text = "\n\n---\n\n".join(chunk)

    # Create the prompt for feature extraction
    response = api_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at analyzing app reviews and extracting specific feature requests.",
            },
            {
                "role": "user",
                "content": f"""
                I'm going to provide you with app reviews. Your task is to carefully analyze these reviews 
                and extract ONLY explicit feature requests mentioned by users. 
                
                Guidelines:
                - Focus on specific feature requests or improvements users want to see
                - Ignore general complaints, praise, or feedback unless they contain a feature request
                - Be precise - extract the exact feature request as described by the user
                - Each feature request should be a single sentence or phrase
                - Return only a list of the identified feature requests, one per line
                
                Here are the reviews to analyze:
                
                {reviews_text}
                """,
            },
        ],
        temperature=0.1,  # Low temperature for consistency
    )

    # Extract the feature requests from the response
    feature_text = response.choices[0].message.content.strip()

    # Parse the response into a list of feature requests
    # The model should return one feature per line
    features = [line.strip() for line in feature_text.split("\n") if line.strip()]

    return features


def group_and_refine_features(
    raw_feature_requests: List[str], client=None
) -> List[str]:
    """
    Group similar feature requests and refine them into unique topics.

    Args:
        raw_feature_requests: List of extracted feature request strings.
        client: OpenAI client instance. If None, use the global instance.

    Returns:
        List of refined, unique feature topic strings.
    """
    # Use provided client or global client
    api_client = client or openai_client

    if not api_client:
        raise ValueError("No OpenAI client available. Please provide API key.")

    # Format the feature requests into a single string for the prompt
    features_text = "\n".join([f"- {feature}" for feature in raw_feature_requests])

    # Create the prompt for feature grouping and refinement
    response = api_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at analyzing and synthesizing product feedback.",
            },
            {
                "role": "user",
                "content": f"""
                I have a list of feature requests extracted from user reviews. Your task is to:
                1. Analyze these requests to identify truly identical or nearly identical items
                2. Group only the most closely related requests (maintain granularity)
                3. Preserve specific details in feature descriptions rather than generalizing
                4. For each small group, synthesize a concise feature description that retains specific details
                5. Return ONLY a list of these refined feature descriptions
                
                IMPORTANT GUIDELINES:
                - Be MORE GRANULAR rather than general - preserve specific details and nuances
                - Only group features that are essentially asking for the exact same thing
                - Maintain different feature requests as separate items when they have distinct details
                - For example, keep "Add QR code for returns" separate from other return-related features
                - Avoid creating high-level general categories that lose important details
                - Don't number your responses, just provide one feature per line
                - ALL feature descriptions MUST be in English, regardless of the input language
                - Translate the feature descriptions to English if necessary
                
                Here are the raw feature requests:
                
                {features_text}
                """,
            },
        ],
        temperature=0.2,  # Slightly higher temperature for synthesis
    )

    # Extract the refined features from the response
    refined_text = response.choices[0].message.content.strip()

    # Parse the response into a list of refined feature topics
    refined_features = [
        line.strip() for line in refined_text.split("\n") if line.strip()
    ]

    return refined_features


def generate_interview_questions(feature_topic: str, client=None) -> List[str]:
    """
    Generate interview questions for a feature topic using GPT-4o.

    Args:
        feature_topic: Feature topic to generate questions for.
        client: OpenAI client instance. If None, use the global instance.

    Returns:
        List of 3 interview questions.
    """
    # Use provided client or global client
    api_client = client or openai_client

    if not api_client:
        raise ValueError("No OpenAI client available. Please provide API key.")

    # Create the prompt for question generation
    response = api_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert user researcher who creates insightful questions for user interviews.",
            },
            {
                "role": "user",
                "content": f"""
                I need to create interview questions about this feature request: "{feature_topic}"
                
                Please generate EXACTLY 3 core questions that a facilitator could ask during a user interview session.
                
                The questions should help understand:
                1. The user's initial reaction to the feature
                2. Potential use cases or value the user sees in this feature
                3. Any concerns or hesitations the user might have
                
                Format your response as a simple list of 3 questions, without numbering or explanation.
                Each question should be on its own line.
                """,
            },
        ],
        temperature=0.5,
    )

    # Extract the questions from the response
    questions_text = response.choices[0].message.content.strip()

    # Parse the response into a list of questions
    questions = [line.strip() for line in questions_text.split("\n") if line.strip()]

    # Ensure we have exactly 3 questions
    if len(questions) != 3:
        # If not, generate default questions
        questions = [
            f"What do you think about adding {feature_topic}?",
            f"How would you use {feature_topic} in your daily workflow?",
            f"Do you have any concerns about {feature_topic}?",
        ][
            :3
        ]  # Take the first 3, or all if fewer than 3

        # If we have fewer than 3, pad with generic questions
        while len(questions) < 3:
            questions.append(
                f"Can you tell me more about your needs regarding {feature_topic}?"
            )

    return questions
