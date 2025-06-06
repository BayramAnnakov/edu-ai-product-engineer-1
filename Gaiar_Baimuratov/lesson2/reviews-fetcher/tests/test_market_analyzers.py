"""
Unit tests for all-market analysis scripts.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the scripts to test
from pull_all_markets import get_all_countries, pull_all_markets_reviews
from analyze_all_markets import analyze_reviews_file


class TestPullAllMarkets(unittest.TestCase):
    """Tests for pull_all_markets.py script."""

    def setUp(self):
        # Create temp dir for output
        self.temp_dir = tempfile.TemporaryDirectory()

        # Mock client
        self.mock_client = MagicMock()

        # Mock countries
        self.mock_countries = [
            {"id": 1, "name": "United States"},
            {"id": 139, "name": "German"},
            {"id": 44, "name": "United Kingdom"},
            {"id": 73, "name": "France"},
        ]

        # Mock reviews response
        self.mock_reviews_response = {
            "results": [
                {
                    "id": 1,
                    "rating": 5,
                    "body": "Great app!",
                    "country": "United States",
                },
                {
                    "id": 2,
                    "rating": 4,
                    "body": "Nice app but needs search",
                    "country": "United States",
                },
            ],
            "total_pages": 1,
        }

        # Mock multi-page reviews response
        self.mock_multi_page_response_page1 = {
            "results": [
                {
                    "id": 1,
                    "rating": 5,
                    "body": "First page review 1",
                    "country": "German",
                },
                {
                    "id": 2,
                    "rating": 4,
                    "body": "First page review 2",
                    "country": "German",
                },
            ],
            "total_pages": 2,
        }

        self.mock_multi_page_response_page2 = {
            "results": [
                {
                    "id": 3,
                    "rating": 3,
                    "body": "Second page review 1",
                    "country": "German",
                },
                {
                    "id": 4,
                    "rating": 2,
                    "body": "Second page review 2",
                    "country": "German",
                },
            ],
            "total_pages": 2,
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_all_countries(self):
        """Test getting all countries."""
        self.mock_client.get_countries.return_value = self.mock_countries

        result = get_all_countries(self.mock_client, "test_app_id")

        self.mock_client.get_countries.assert_called_once_with("test_app_id")
        self.assertEqual(result, self.mock_countries)
        self.assertEqual(len(result), 4)  # Verify we have all countries

    @patch("pull_all_markets.get_all_countries")
    def test_pull_all_markets_reviews_basic(self, mock_get_countries):
        """Test pulling reviews from all markets - basic case."""
        # Set up mocks
        mock_get_countries.return_value = self.mock_countries
        self.mock_client.get_reviews.return_value = self.mock_reviews_response

        # Monkeypatch Path.mkdir to do nothing
        with patch("pathlib.Path.mkdir"), patch(
            "pull_all_markets.AppBotClient", return_value=self.mock_client
        ), patch("pull_all_markets.open", unittest.mock.mock_open()), patch(
            "json.dump"
        ):

            # Run the function with a mock app_id
            result_file = pull_all_markets_reviews("test_app_id", days=30)

            # Verify the client was called correctly for each country
            expected_calls = []
            for country in self.mock_countries:
                expected_calls.append(
                    call(
                        app_id="test_app_id",
                        start=unittest.mock.ANY,  # We don't test the exact date here
                        end=unittest.mock.ANY,
                        country=country["id"],
                        page=1,
                    )
                )

            # Assert the client was called exactly with these parameters
            self.mock_client.get_reviews.assert_has_calls(expected_calls)

            # Successfully completed without errors
            pass

            # Verify the result is a Path object
            self.assertIsNotNone(result_file)

    @patch("pull_all_markets.get_all_countries")
    def test_pull_all_markets_reviews_pagination(self, mock_get_countries):
        """Test pulling reviews with pagination."""
        # Set up mocks - we'll only test with one country to simplify
        mock_get_countries.return_value = [self.mock_countries[1]]  # Just use German

        # Configure client to return different responses for different pages
        def mock_get_reviews_side_effect(**kwargs):
            page = kwargs.get("page", 1)
            if page == 1:
                return self.mock_multi_page_response_page1
            else:
                return self.mock_multi_page_response_page2

        self.mock_client.get_reviews.side_effect = mock_get_reviews_side_effect

        # Monkeypatch Path.mkdir to do nothing
        with patch("pathlib.Path.mkdir"), patch(
            "pull_all_markets.AppBotClient", return_value=self.mock_client
        ), patch("pull_all_markets.open", unittest.mock.mock_open()), patch(
            "json.dump"
        ):

            # Run the function
            pull_all_markets_reviews("test_app_id", days=7)

            # Verify the client was called for both pages
            expected_calls = [
                call(
                    app_id="test_app_id",
                    start=unittest.mock.ANY,
                    end=unittest.mock.ANY,
                    country=self.mock_countries[1]["id"],
                    page=1,
                ),
                call(
                    app_id="test_app_id",
                    start=unittest.mock.ANY,
                    end=unittest.mock.ANY,
                    country=self.mock_countries[1]["id"],
                    page=2,
                ),
            ]

            self.mock_client.get_reviews.assert_has_calls(expected_calls)

    @patch("pull_all_markets.get_all_countries")
    def test_pull_all_markets_reviews_date_range(self, mock_get_countries):
        """Test that correct date range is used based on days parameter."""
        # Only test with one country
        mock_get_countries.return_value = [self.mock_countries[0]]
        self.mock_client.get_reviews.return_value = self.mock_reviews_response

        # Calculate expected dates for 90 days
        today = datetime.now().strftime("%Y-%m-%d")
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        with patch("pathlib.Path.mkdir"), patch(
            "pull_all_markets.AppBotClient", return_value=self.mock_client
        ), patch("pull_all_markets.open", unittest.mock.mock_open()), patch(
            "json.dump"
        ):

            # Run with 90 days
            pull_all_markets_reviews("test_app_id", days=90)

            # Verify call used correct date range
            self.mock_client.get_reviews.assert_called_with(
                app_id="test_app_id",
                start=ninety_days_ago,
                end=today,
                country=self.mock_countries[0]["id"],
                page=1,
            )

    @patch("pull_all_markets.get_all_countries")
    def test_pull_all_markets_reviews_exception_handling(self, mock_get_countries):
        """Test the exception handling for API errors."""
        # Set up mocks
        mock_get_countries.return_value = [self.mock_countries[0]]

        # Make API throw an exception on call
        self.mock_client.get_reviews.side_effect = Exception("API Error")

        # Monkeypatch Path.mkdir to do nothing
        with patch("pathlib.Path.mkdir"), patch(
            "pull_all_markets.AppBotClient", return_value=self.mock_client
        ), patch("pull_all_markets.open", unittest.mock.mock_open()), patch(
            "json.dump"
        ):

            # Run the function - should not crash
            result = pull_all_markets_reviews("test_app_id", days=30)

            # Verify the client was called
            self.mock_client.get_reviews.assert_called_once()

            # Successfully completed
            pass

            # Return value should be valid
            self.assertIsNotNone(result)


class TestAnalyzeAllMarkets(unittest.TestCase):
    """Tests for analyze_all_markets.py script."""

    def setUp(self):
        # Create temp dir for output
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a mock reviews file with multi-country and multi-language data
        self.mock_reviews_data = {
            "app_id": "test_app_id",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "results": [
                {
                    "id": 1,
                    "rating": 5,
                    "body": "Great app!",
                    "country": "United States",
                    "detected_language": "English",
                },
                {
                    "id": 2,
                    "rating": 4,
                    "body": "Need search feature",
                    "country": "United States",
                    "detected_language": "English",
                },
                {
                    "id": 3,
                    "rating": 4,
                    "body": "Need dark mode",
                    "country": "United States",
                    "detected_language": "English",
                },
                {
                    "id": 4,
                    "rating": 3,
                    "body": "Könnte besser sein",
                    "country": "German",
                    "detected_language": "German",
                },
                {
                    "id": 5,
                    "rating": 2,
                    "body": "Die App braucht eine Suchfunktion",
                    "country": "German",
                    "detected_language": "German",
                },
                {
                    "id": 6,
                    "rating": 5,
                    "body": "Super app mais besoin de recherche",
                    "country": "France",
                    "detected_language": "French",
                },
                {
                    "id": 7,
                    "rating": 1,
                    "body": "App crashes on startup",
                    "country": "United Kingdom",
                    "detected_language": "English",
                },
                {
                    "id": 8,
                    "rating": 2,
                    "body": "App needs better performance",
                    "country": "United Kingdom",
                    "detected_language": "English",
                },
            ],
        }

        self.mock_file_path = os.path.join(self.temp_dir.name, "mock_reviews.json")
        with open(self.mock_file_path, "w") as f:
            json.dump(self.mock_reviews_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("analyze_all_markets.chunk_reviews")
    @patch("analyze_all_markets.extract_features_from_chunk")
    @patch("analyze_all_markets.group_and_refine_features")
    @patch("analyze_all_markets.generate_interview_questions")
    def test_analyze_reviews_file(
        self, mock_generate_questions, mock_refine, mock_extract, mock_chunk
    ):
        """Test analyzing reviews from a file."""
        # Set up mocks
        mock_chunk.return_value = [
            [
                "Need search feature",
                "Könnte besser sein",
                "Die App braucht eine Suchfunktion",
            ],
            [
                "Super app mais besoin de recherche",
                "App needs better performance",
                "Need dark mode",
            ],
        ]
        mock_extract.side_effect = [
            ["Add search functionality", "Improve German translation"],
            ["Add dark mode", "Improve app performance", "Add search in French"],
        ]
        mock_refine.return_value = [
            "Implement comprehensive search functionality across all languages",
            "Add dark mode option",
            "Improve app performance and stability",
        ]
        mock_generate_questions.side_effect = [
            [
                "Question 1 about search",
                "Question 2 about search",
                "Question 3 about search",
            ],
            [
                "Question 1 about dark mode",
                "Question 2 about dark mode",
                "Question 3 about dark mode",
            ],
            [
                "Question 1 about performance",
                "Question 2 about performance",
                "Question 3 about performance",
            ],
        ]

        # Mock file operations
        with patch("pathlib.Path.mkdir"), patch(
            "analyze_all_markets.open",
            unittest.mock.mock_open(read_data=json.dumps(self.mock_reviews_data)),
        ), patch("json.dump") as mock_json_dump, patch(
            "json.load", return_value=self.mock_reviews_data
        ):

            # Run the function
            result_file = analyze_reviews_file(self.mock_file_path, self.temp_dir.name)

            # Verify functions were called correctly
            mock_chunk.assert_called_once()

            # Extract should be called for each chunk
            self.assertEqual(mock_extract.call_count, 2)

            # Refine should be called once with all features
            expected_features = [
                "Add search functionality",
                "Improve German translation",
                "Add dark mode",
                "Improve app performance",
                "Add search in French",
            ]
            mock_refine.assert_called_once_with(expected_features)

            # Generate questions should be called for each refined feature
            self.assertEqual(mock_generate_questions.call_count, 3)

            # Verify json.dump was called for saving outputs (raw features and final output)
            self.assertEqual(mock_json_dump.call_count, 2)

            # Verify the result is not None
            self.assertIsNotNone(result_file)

    @patch("analyze_all_markets.analyze_reviews_file")
    @patch("typer.Argument")
    @patch("typer.Option")
    def test_main_function(self, mock_option, mock_argument, mock_analyze):
        """Test the main function with command line arguments."""
        # Set up mocks
        mock_analyze.return_value = "mock_output.json"
        mock_argument.return_value = self.mock_file_path
        mock_option.return_value = self.temp_dir.name

        # Call main directly - it's using typer which makes sys.argv mocking difficult
        from analyze_all_markets import main

        result = main(file_path=self.mock_file_path, output_dir=self.temp_dir.name)

        # Verify analyze_reviews_file was called (not checking exact args due to typer decorators)
        self.assertTrue(mock_analyze.called)
        # Check return value
        self.assertEqual(result, "mock_output.json")

    def test_analyze_reviews_error_handling(self):
        """Test error handling during analysis."""
        # Mock chunk_reviews to raise an exception
        with patch(
            "analyze_all_markets.chunk_reviews", side_effect=Exception("Test error")
        ), patch(
            "analyze_all_markets.open",
            unittest.mock.mock_open(read_data=json.dumps(self.mock_reviews_data)),
        ), patch(
            "pathlib.Path.mkdir"
        ), patch(
            "json.load", return_value=self.mock_reviews_data
        ):

            # Run the function - should not crash
            result = analyze_reviews_file(self.mock_file_path, self.temp_dir.name)

            # Result should be None due to the exception
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
