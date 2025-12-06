"""
Unit tests for my Media Archive Project.
This module checks if the models, database logic, and file operations work correctly.
I also added some edge cases to make sure the program is robust.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import shutil

# Project Imports
from business_logic_and_oop import Movie, Series
from scraper import IMDBScraper
from data_storage import MongoStorage
from poster_manager import PosterManager
from search_manager import find_link


class TestMediaModels(unittest.TestCase):
    """Testing my OOP classes (Movie and Series) to see if they hold data correctly."""

    def test_movie_creation(self):
        """Checking if a Movie object is created with the correct type 'movie'."""
        movie = Movie("Matrix", "1999", "8.7", "url", "link", "watched")
        self.assertEqual(movie.media_type, "movie")
        self.assertIn("MOVIE", movie.get_info())

    def test_series_creation(self):
        """Checking if a Series object is created with the correct type 'series'."""
        series = Series("Friends", "1994", "8.9", "url", "link", "watching")
        self.assertEqual(series.media_type, "series")
        self.assertIn("SERIES", series.get_info())

    def test_case_sensitivity_status(self):
        """What if I type 'WATCHED' in caps? It should convert it to 'watched'."""
        movie_upper = Movie("Test", "2020", "5.0", "url",
                            "link", status="WATCHED")

        self.assertEqual(movie_upper.status, "watched")

    def test_to_dict_method(self):
        """Testing if the object converts to a dictionary for MongoDB storage."""
        movie = Movie("A", "2000", "5.0", "url", "link")
        data = movie.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["title"], "A")


class TestInputSanitization(unittest.TestCase):
    """Testing if the system cleans up bad filenames properly."""

    def setUp(self):
        """Setting up a temporary folder for posters."""
        self.pm = PosterManager(folder_name="test_posters")

    def tearDown(self):
        """Cleaning up the temporary folder after tests."""
        if os.path.exists("test_posters"):
            shutil.rmtree("test_posters")

    def test_sanitize_filename_forbidden_chars(self):
        """Removing bad characters like / or : so the OS doesn't crash."""
        dirty_title = "Face/Off: <The Movie> *2023*"
        # pylint: disable=protected-access
        clean_name = self.pm._sanitize_filename(dirty_title)

        self.assertNotIn("/", clean_name)
        self.assertNotIn(":", clean_name)
        self.assertNotIn("*", clean_name)
        self.assertNotIn("<", clean_name)

    def test_sanitize_whitespace(self):
        """Trimming extra spaces from the title."""
        dirty_title = "   Inception    Movie   "
        # pylint: disable=protected-access
        clean_name = self.pm._sanitize_filename(dirty_title)
        self.assertEqual(clean_name, "Inception Movie")


class TestScraperRobustness(unittest.TestCase):
    """Mocking the scraper to see how it handles errors."""

    def setUp(self):
        self.scraper = IMDBScraper()

    @patch('scraper.IMDBScraper._fetch_html')
    def test_network_failure(self, mock_fetch):
        """Simulating a network error (no internet), it should return None."""
        mock_fetch.return_value = None
        result = self.scraper.scrape_media_data("http://valid-url.com")
        self.assertIsNone(result)

    @patch('scraper.IMDBScraper._fetch_html')
    def test_malformed_html(self, mock_fetch):
        """If HTML is broken/empty, it should handle it gracefully."""
        mock_fetch.return_value = "<html><body></body></html>"
        result = self.scraper.scrape_media_data("http://valid-url.com")

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Unknown")
        self.assertEqual(result.rating, "N/A")


class TestDatabaseLogic(unittest.TestCase):
    """Testing database logic without actually connecting to MongoDB."""

    @patch('data_storage.MongoClient')
    def test_connection_failure(self, mock_client):
        """If the DB server is down, it should handle the timeout."""
        mock_client.side_effect = Exception("Timeout")
        storage = MongoStorage()
        self.assertIsNone(storage.collection)

    @patch('data_storage.MongoClient')
    def test_prevent_duplicate_entry(self, mock_client):
        """Logic check: Don't save the movie if it already exists."""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        # Simulating that the movie is already in the DB
        mock_col.find_one.return_value = {"title": "Matrix"}

        storage = MongoStorage()
        movie = Movie("Matrix", "1999", "8.7", "url", "link")
        storage.save(movie)

        # Checking that insert_one was NOT called
        mock_col.insert_one.assert_not_called()


class TestSearchManager(unittest.TestCase):
    """Testing the search functionality."""

    @patch('search_manager.sync_playwright')
    def test_search_no_results(self, mock_pw):
        """If no link is found, status should be 'failed'."""
        mock_browser = mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value

        # Simulating no href attribute found
        mock_page.locator.return_value.first.get_attribute.return_value = None

        result = find_link("NonExistentMovie12345")
        self.assertEqual(result["status"], "failed")


class TestEdgeCaseInputs(unittest.TestCase):
    """
    [ROBUSTNESS] Testing weird or extreme inputs.
    Basically trying to break my own code.
    """

    @patch('search_manager.sync_playwright')
    def test_search_case_insensitivity(self, mock_pw):
        """
        Scenario: User types 'mAtRiX' instead of 'Matrix'.
        It shouldn't crash.
        """
        mock_browser = mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        # Simulate not finding it (just checking if function runs)
        mock_page.locator.return_value.first.get_attribute.return_value = None

        try:
            # Running search with mixed case
            result = find_link("mAtRiX ReLoAdEd")
            # If we are here, it didn't crash
            self.assertIsInstance(result, dict)
            self.assertEqual(result["search_term"], "mAtRiX ReLoAdEd")
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.fail(f"Search crashed on mixed case input: {err}")

    def test_model_whitespace_trimming(self):
        """
        Scenario: User inputs "  Inception  ".
        Poster manager should clean this up.
        """
        poster_mgr = PosterManager()
        dirty_input = "   The Dark Knight   "
        # pylint: disable=protected-access
        clean_filename = poster_mgr._sanitize_filename(dirty_input)

        # Expectation: "The Dark Knight"
        self.assertEqual(clean_filename, "The Dark Knight")
        self.assertFalse(clean_filename.startswith(" "))
        self.assertFalse(clean_filename.endswith(" "))

    def test_extreme_input_length(self):
        """
        Scenario: Inputting a very long title (5000 chars).
        The system should not crash due to buffer overflow.
        """
        long_title = "A" * 5000

        try:
            movie = Movie(long_title, "2024", "1.0", "url", "link")
            self.assertEqual(len(movie.title), 5000)
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.fail(f"System crashed on extreme input length: {err}")


class TestFileSystemResilience(unittest.TestCase):
    """
    [ROBUSTNESS] File System & Permission Errors.
    What happens if the computer says 'Access Denied'?
    """

    @patch('builtins.open')
    def test_json_export_permission_error(self, mock_open):
        """
        Scenario: Trying to save 'movies.json' but folder is Read-Only.
        The code should catch the error and not crash.
        """
        # Simulating PermissionError
        mock_open.side_effect = PermissionError("Access Denied")

        storage = MongoStorage()
        # Mocking list_all so export tries to run
        fake_movie = Movie("Test", "2020", "5", "url", "link")
        with patch.object(storage, 'list_all', return_value=[fake_movie]):
            try:
                storage.export_json("movies.json")
            except PermissionError:
                self.fail("The application crashed! "
                          "It should have handled PermissionError gracefully.")
            except Exception:  # pylint: disable=broad-exception-caught
                pass  # Any other exception is fine

    def test_poster_manager_bad_path(self):
        """
        Scenario: Trying to use a bad path/folder name.
        """
        # pylint: disable=unused-variable
        PosterManager(folder_name="INVALID_FOLDER_<>|")

        # The _create_folder method has a try-except block.
        # It prints an error but shouldn't stop execution.
        # If we reached here, it passed.


class TestDeepValidation(unittest.TestCase):
    """
    [UNIT] Logic Validation.
    Checking if the logic actually makes sense.
    """

    def test_movie_vs_series_logic(self):
        """Making sure Movie and Series are treated differently."""
        mov = Movie("M", "2000", "1", "u", "l")
        ser = Series("S", "2000", "1", "u", "l")

        # They should not be equal in type
        self.assertNotEqual(mov.media_type, ser.media_type)
        self.assertTrue(mov.media_type == "movie")
        self.assertFalse(ser.media_type == "movie")

    def test_numeric_validation_in_strings(self):
        """
        Scenario: Year is '2023' (string) but implies a number.
        The system should accept strings and not crash on int conversion.
        """
        movie = Movie("Test", "2023", "9.0", "url", "link")

        # Python allows string validation
        self.assertTrue(movie.year.isdigit())

        # If year is 'Unknown', it should still accept it
        movie_unknown = Movie("Test", "Unknown", "9.0", "url", "link")
        self.assertEqual(movie_unknown.year, "Unknown")


if __name__ == '__main__':
    print("\nRunning Robustness Tests...")
    unittest.main(verbosity=2)
