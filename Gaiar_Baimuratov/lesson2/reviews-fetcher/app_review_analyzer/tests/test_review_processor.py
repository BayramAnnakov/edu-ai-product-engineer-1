"""
Unit tests for review processor functions.
"""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from src.review_processor import (
    load_reviews,
    chunk_reviews,
    extract_features_from_chunk,
    group_and_refine_features,
    generate_interview_questions,
)


def test_load_reviews():
    # Create a temporary JSON file with test reviews
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
        json.dump(
            {
                "results": [
                    {"body": "This is review 1"},
                    {"body": "This is review 2"},
                    {"body": ""},  # Empty review should be skipped
                ]
            },
            f,
        )
        temp_file = f.name

    try:
        # Test loading reviews
        reviews = load_reviews(temp_file)
        assert len(reviews) == 2
        assert reviews[0] == "This is review 1"
        assert reviews[1] == "This is review 2"
    finally:
        # Clean up the temp file
        os.unlink(temp_file)


def test_chunk_reviews_empty():
    """Test chunking with empty review list."""
    assert chunk_reviews([]) == []


def test_chunk_reviews_small_list():
    """Test chunking with a list small enough to fit in one chunk."""
    # Mock a short list of reviews
    reviews = ["Short review 1", "Short review 2", "Short review 3"]
    chunks = chunk_reviews(reviews, 4000)
    assert len(chunks) == 1
    assert len(chunks[0]) == 3


@patch("tiktoken.encoding_for_model")
def test_chunk_reviews_multiple_chunks(mock_encoding):
    """Test chunking with list requiring multiple chunks."""
    # Setup mock encoding to return specific token counts
    mock_encode = MagicMock()
    # Each review will be 2000 tokens
    mock_encode.return_value = list(range(2000))
    mock_encoding.return_value.encode = mock_encode

    # With 2000 tokens per review and max 4000 tokens (minus overhead),
    # each chunk should hold only 1 review
    reviews = ["Review 1", "Review 2", "Review 3"]
    chunks = chunk_reviews(reviews, 4000)

    assert len(chunks) == 3
    assert chunks[0] == ["Review 1"]
    assert chunks[1] == ["Review 2"]
    assert chunks[2] == ["Review 3"]


@patch("tiktoken.encoding_for_model")
def test_chunk_reviews_oversized_review(mock_encoding):
    """Test handling a single review that exceeds max tokens."""
    # Setup mock encoding
    mock_encode = MagicMock()
    mock_encode.side_effect = lambda x: list(range(6000 if x == "Huge review" else 100))
    mock_encoding.return_value.encode = mock_encode

    reviews = ["Short review", "Huge review", "Another short review"]
    chunks = chunk_reviews(reviews, 4000)

    # Should create at least 2 chunks
    assert len(chunks) >= 2

    # Check if the chunks contain what we expect
    found_short = False
    found_huge_truncated = False

    for chunk in chunks:
        if len(chunk) == 1:
            if "Short review" in chunk[0]:
                found_short = True
            if isinstance(chunk[0], str) and chunk[0].startswith("Huge review"):
                found_huge_truncated = True

    # Either the short review is in its own chunk or the huge review is truncated
    assert found_short or found_huge_truncated


class MockOpenAIResponse:
    """Mock class for OpenAI API responses."""

    def __init__(self, content):
        self.choices = [
            type(
                "obj",
                (object,),
                {"message": type("obj", (object,), {"content": content})},
            )
        ]


@patch("openai.OpenAI")
def test_extract_features_from_chunk(mock_openai):
    # Setup mock OpenAI client
    mock_client = MagicMock()
    mock_response = MockOpenAIResponse("Feature 1\nFeature 2\nFeature 3")
    mock_client.chat.completions.create.return_value = mock_response

    # Test feature extraction
    chunk = ["Review 1 asking for feature 1", "Review 2 asking for feature 2"]
    features = extract_features_from_chunk(chunk, client=mock_client)

    # Verify OpenAI API was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4o"
    assert len(call_args["messages"]) == 2
    assert "system" in call_args["messages"][0]["role"]
    assert "user" in call_args["messages"][1]["role"]
    assert "Review 1" in call_args["messages"][1]["content"]
    assert "Review 2" in call_args["messages"][1]["content"]

    # Verify results
    assert len(features) == 3
    assert features[0] == "Feature 1"
    assert features[1] == "Feature 2"
    assert features[2] == "Feature 3"


@patch("openai.OpenAI")
def test_group_and_refine_features(mock_openai):
    # Setup mock OpenAI client
    mock_client = MagicMock()
    mock_response = MockOpenAIResponse("Refined Feature 1\nRefined Feature 2")
    mock_client.chat.completions.create.return_value = mock_response

    # Test feature refinement
    raw_features = [
        "Add dark mode",
        "Implement night theme",
        "Option to add comments",
        "Allow users to comment on posts",
    ]
    refined = group_and_refine_features(raw_features, client=mock_client)

    # Verify OpenAI API was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4o"
    assert len(call_args["messages"]) == 2
    # Verify all raw features are included in the prompt
    for feature in raw_features:
        assert feature in call_args["messages"][1]["content"]

    # Verify results
    assert len(refined) == 2
    assert refined[0] == "Refined Feature 1"
    assert refined[1] == "Refined Feature 2"


@patch("openai.OpenAI")
def test_generate_interview_questions(mock_openai):
    # Setup mock OpenAI client
    mock_client = MagicMock()
    mock_response = MockOpenAIResponse("Question 1?\nQuestion 2?\nQuestion 3?")
    mock_client.chat.completions.create.return_value = mock_response

    # Test question generation
    feature = "Add dark mode"
    questions = generate_interview_questions(feature, client=mock_client)

    # Verify OpenAI API was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4o"
    assert len(call_args["messages"]) == 2
    assert feature in call_args["messages"][1]["content"]

    # Verify results
    assert len(questions) == 3
    assert questions[0] == "Question 1?"
    assert questions[1] == "Question 2?"
    assert questions[2] == "Question 3?"


@patch("openai.OpenAI")
def test_generate_interview_questions_handles_incorrect_count(mock_openai):
    # Setup mock OpenAI client to return only 2 questions
    mock_client = MagicMock()
    mock_response = MockOpenAIResponse("Question 1?\nQuestion 2?")
    mock_client.chat.completions.create.return_value = mock_response

    # Test question generation
    feature = "Add dark mode"
    questions = generate_interview_questions(feature, client=mock_client)

    # Verify results
    assert len(questions) == 3  # Should always return exactly 3 questions
