"""
Unit tests for AppBot client
"""

import os
import unittest
from unittest.mock import patch, Mock

from appbot import AppBotClient


class TestAppBotClient(unittest.TestCase):
    """Test case for AppBotClient"""

    def setUp(self):
        self.test_username = "test_username"
        self.test_password = "test_password"
        self.client = AppBotClient(
            username=self.test_username, password=self.test_password
        )

    def test_init_with_params(self):
        client = AppBotClient(username="user", password="pass")
        self.assertEqual(client.username, "user")
        self.assertEqual(client.password, "pass")

    @patch.dict(
        os.environ,
        {"APPBOT_API_USERNAME": "env_user", "APPBOT_API_PASSWORD": "env_pass"},
    )
    def test_init_with_env_vars(self):
        client = AppBotClient()
        self.assertEqual(client.username, "env_user")
        self.assertEqual(client.password, "env_pass")

    def test_init_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                AppBotClient()

    @patch("requests.request")
    def test_request(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        result = self.client._request(
            "test/endpoint", method="GET", params={"key": "value"}
        )

        # Check that the method was called once
        self.assertEqual(mock_request.call_count, 1)

        # Check each argument individually
        args, kwargs = mock_request.call_args
        print(f"Debug - request args: {args}")
        print(f"Debug - request kwargs: {kwargs}")
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "https://api.appbot.co/api/v2/test/endpoint")
        self.assertEqual(kwargs["auth"], (self.test_username, self.test_password))
        self.assertEqual(kwargs["params"], {"key": "value"})

        # Make sure timeout exists, but be flexible about the value
        self.assertIn("timeout", kwargs)

        # Check the result
        self.assertEqual(result, {"key": "value"})

    @patch("appbot.client.AppBotClient._request")
    def test_get_token_info(self, mock_request):
        mock_request.return_value = {"api_key": "BDQXXXXXX"}
        result = self.client.get_token_info()
        mock_request.assert_called_once_with("me")
        self.assertEqual(result, {"api_key": "BDQXXXXXX"})

    @patch("appbot.client.AppBotClient._request")
    def test_get_apps(self, mock_request):
        mock_request.return_value = {"results": [{"id": 68, "name": "Test App"}]}
        result = self.client.get_apps()
        mock_request.assert_called_once_with("apps")
        self.assertEqual(result, [{"id": 68, "name": "Test App"}])

    @patch("appbot.client.AppBotClient._request")
    def test_get_reviews(self, mock_request):
        mock_request.return_value = {
            "results": [{"id": 123, "rating": 5}],
            "count": 1,
            "page": 1,
            "total_count": 1,
            "total_pages": 1,
        }

        result = self.client.get_reviews(
            app_id=123,
            start="2023-01-01",
            end="2023-01-31",
            keyword="test",
            country=1,
            sentiments=["positive", "neutral"],
            dlangs=["en"],
            version="1.0.0",
            topic=42,
            page=1,
        )

        # Check that the method was called once
        self.assertEqual(mock_request.call_count, 1)

        # Check endpoint
        args, kwargs = mock_request.call_args
        print(f"Debug - get_reviews args: {args}")
        print(f"Debug - get_reviews kwargs: {kwargs}")
        self.assertEqual(args[0], "apps/123/reviews")

        # Check that timeout exists
        self.assertIn("timeout", kwargs)

        # Check all the parameters are present with correct values
        params = kwargs.get("params", {})
        expected_params = {
            "start": "2023-01-01",
            "end": "2023-01-31",
            "keyword": "test",
            "country": 1,
            "sentiments": "positive+neutral",
            "dlangs": "en",
            "version": "1.0.0",
            "topic": 42,
            "page": 1,
        }

        for key, value in expected_params.items():
            self.assertEqual(
                params.get(key), value, f"Parameter '{key}' should be {value}"
            )

        self.assertEqual(result["results"], [{"id": 123, "rating": 5}])

    @patch("appbot.client.AppBotClient._request")
    def test_get_sentiment_breakdown(self, mock_request):
        mock_request.return_value = {
            "results": {"positive": 4728, "negative": 510, "neutral": 304, "mixed": 231}
        }

        result = self.client.get_sentiment_breakdown(
            app_id=123, start="2023-01-01", end="2023-01-31"
        )

        mock_request.assert_called_once_with(
            "apps/123/sentiment/breakdown",
            params={"start": "2023-01-01", "end": "2023-01-31"},
        )

        self.assertEqual(result["results"]["positive"], 4728)
        self.assertEqual(result["results"]["negative"], 510)

    @patch("appbot.client.AppBotClient._request")
    def test_get_popular_words(self, mock_request):
        mock_request.return_value = {
            "results": [
                {"word": "game", "counter": 1555, "positive": 1368},
                {"word": "love", "counter": 747, "positive": 710},
            ],
            "count": 2,
        }

        result = self.client.get_popular_words(app_id=123)

        mock_request.assert_called_once_with("apps/123/words/popular", params={})

        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["word"], "game")

    @patch("appbot.client.AppBotClient._request")
    def test_get_phrases(self, mock_request):
        mock_request.return_value = {
            "results": [{"phrase": "wonderful app", "counter": 1555, "positive": 1368}],
            "count": 1,
        }

        result = self.client.get_phrases(app_id=123, phrase_word_count=2)

        mock_request.assert_called_once_with(
            "apps/123/phrases", params={"phrase_word_count": 2}
        )

        self.assertEqual(result["results"][0]["phrase"], "wonderful app")

    def test_get_phrases_invalid_word_count(self):
        with self.assertRaises(ValueError):
            self.client.get_phrases(app_id=123, phrase_word_count=5)

    @patch("appbot.client.AppBotClient._request")
    def test_get_ratings_live(self, mock_request):
        mock_response = {
            "all_time": None,
            "current_version": {
                "count": 4596,
                "average": 4.88,
                "breakdown": {"5": 4301, "4": 178},
            },
        }
        mock_request.return_value = mock_response

        result = self.client.get_ratings_live(app_id=123, country="US")

        mock_request.assert_called_once_with(
            "apps/123/ratings", params={"country": "US"}
        )

        self.assertEqual(result["current_version"]["count"], 4596)


if __name__ == "__main__":
    unittest.main()
