"""
Unit tests for UI utilities.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path

# Add app_review_analyzer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app_review_analyzer"))

# Import the UI utils to test
from src.ui_utils import (
    display_header,
    display_section,
    display_success,
    display_error,
    display_warning,
    display_stats_table,
    generate_llm_summary,
    format_duration,
    TimedOperation,
)


class TestUIUtils(unittest.TestCase):
    """Tests for UI utilities."""

    def setUp(self):
        # Create a console mock to capture output
        self.mock_console = MagicMock()
        self.stdout_backup = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.stdout_backup

    @patch("src.ui_utils.console")
    def test_display_header(self, mock_console):
        """Test displaying a header."""
        display_header("TEST HEADER")
        mock_console.print.assert_called()

        # Since we can't easily inspect the Panel object directly,
        # just verify the function called console.print at least once
        self.assertGreater(mock_console.print.call_count, 0)

    @patch("src.ui_utils.console")
    def test_display_section(self, mock_console):
        """Test displaying a section."""
        display_section("Test Section")
        mock_console.print.assert_called()

        # Verify the section title is included
        section_arg = mock_console.print.call_args[0][0]
        self.assertIn("Test Section", section_arg)

    @patch("src.ui_utils.console")
    def test_display_success(self, mock_console):
        """Test displaying a success message."""
        display_success("Success message")
        mock_console.print.assert_called_once()

        # Check success formatting
        success_arg = mock_console.print.call_args[0][0]
        self.assertIn("Success message", success_arg)
        self.assertIn("✓", success_arg)

    @patch("src.ui_utils.console")
    def test_display_error(self, mock_console):
        """Test displaying an error message."""
        display_error("Error message")
        mock_console.print.assert_called_once()

        # Check error formatting
        error_arg = mock_console.print.call_args[0][0]
        self.assertIn("Error message", error_arg)
        self.assertIn("ERROR", error_arg)

    @patch("src.ui_utils.console")
    def test_display_warning(self, mock_console):
        """Test displaying a warning message."""
        display_warning("Warning message")
        mock_console.print.assert_called_once()

        # Check warning formatting
        warning_arg = mock_console.print.call_args[0][0]
        self.assertIn("Warning message", warning_arg)
        self.assertIn("⚠", warning_arg)

    @patch("src.ui_utils.console")
    def test_display_stats_table(self, mock_console):
        """Test displaying a stats table."""
        table_data = [{"Name": "Test1", "Value": 42}, {"Name": "Test2", "Value": 100}]

        display_stats_table("Test Table", table_data)
        mock_console.print.assert_called_once()

        # Since we directly pass the table object to console.print
        # without keyword args, just verify the call happened
        mock_console.print.assert_called_once()

    def test_format_duration(self):
        """Test formatting durations."""
        self.assertEqual(format_duration(30), "30s")
        self.assertEqual(format_duration(90), "1m 30s")
        self.assertEqual(format_duration(3600), "1h 0m 0s")
        self.assertEqual(format_duration(3725), "1h 2m 5s")

    @patch("openai.OpenAI")
    def test_generate_llm_summary(self, mock_openai):
        """Test generating LLM summary."""
        # Setup mock OpenAI response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Test summary"))]
        mock_client.chat.completions.create.return_value = mock_completion

        # Test data
        test_data = {
            "app_id": "test123",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "total_count": 1000,
            "feature_count": 15,
            "raw_feature_count": 50,
            "top_features": ["Feature 1", "Feature 2"],
            "country_stats": {"USA": 500, "Germany": 300},
        }

        result = generate_llm_summary(test_data, mock_client)

        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()

        # Verify the result
        self.assertEqual(result, "Test summary")

    @patch("time.time")
    @patch("src.ui_utils.console")
    def test_timed_operation(self, mock_console, mock_time):
        """Test timed operation context manager."""
        # Mock time.time to return predictable values
        mock_time.side_effect = [100, 105]  # Start time, end time (5 seconds elapsed)

        with TimedOperation("Test Operation", mock_console):
            # Operation inside context
            pass

        # Verify start and complete messages
        self.assertEqual(mock_console.print.call_count, 2)

        # First call should be "Starting"
        start_arg = mock_console.print.call_args_list[0][0][0]
        self.assertIn("Starting: Test Operation", start_arg)

        # Second call should be "Completed" with duration
        complete_arg = mock_console.print.call_args_list[1][0][0]
        self.assertIn("Completed: Test Operation", complete_arg)
        self.assertIn("5s", complete_arg)  # Should include formatted duration


if __name__ == "__main__":
    unittest.main()
