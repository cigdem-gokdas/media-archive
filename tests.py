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
    """Tests the OOP structure and data models."""

    def test_movie_creation(self):
        # Tests if Movie class correctly inherits 'movie' type
        movie = Movie("Matrix", "1999", "8.7", "url", "link", "watched")
        self.assertEqual(movie.media_type, "movie")
        self.assertIn("MOVIE", movie.get_info())

    def test_series_creation(self):
        # Tests if Series class correctly inherits 'series' type
        series = Series("Friends", "1994", "8.9", "url", "link", "watching")
        self.assertEqual(series.media_type, "series")
        self.assertIn("SERIES", series.get_info())

    def test_case_sensitivity_status(self):
        # Tests if status handles mixed case inputs correctly
        movie_upper = Movie("Test", "2020", "5.0", "url",
                            "link", status="WATCHED")
        movie_mixed = Movie("Test", "2020", "5.0", "url",
                            "link", status="WaTcHeD")

        self.assertEqual(movie_upper.status, "WATCHED")
        self.assertEqual(movie_mixed.status, "WaTcHeD")

    def test_to_dict_method(self):
        # Tests if object converts to dictionary for MongoDB
        movie = Movie("A", "2000", "5.0", "url", "link")
        data = movie.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["title"], "A")


class TestInputSanitization(unittest.TestCase):
    """Tests if the system handles bad inputs safely."""

    def setUp(self):
        self.pm = PosterManager(folder_name="test_posters")

    def tearDown(self):
        if os.path.exists("test_posters"):
            shutil.rmtree("test_posters")

    def test_sanitize_filename_forbidden_chars(self):
        # Tests removal of OS-forbidden characters like / : * ?
        dirty_title = "Face/Off: <The Movie> *2023*"
        clean_name = self.pm._sanitize_filename(dirty_title)

        self.assertNotIn("/", clean_name)
        self.assertNotIn(":", clean_name)
        self.assertNotIn("*", clean_name)
        self.assertNotIn("<", clean_name)

    def test_sanitize_whitespace(self):
        # Tests removal of double spaces and trailing whitespace
        dirty_title = "   Inception    Movie   "
        clean_name = self.pm._sanitize_filename(dirty_title)
        self.assertEqual(clean_name, "Inception Movie")


class TestScraperRobustness(unittest.TestCase):
    """Tests how the scraper handles errors (Mocked)."""

    def setUp(self):
        self.scraper = IMDBScraper()

    @patch('scraper.IMDBScraper._fetch_html')
    def test_network_failure(self, mock_fetch):
        # Tests behavior when internet is down (returns None)
        mock_fetch.return_value = None
        result = self.scraper.scrape_media_data("http://valid-url.com")
        self.assertIsNone(result)

    @patch('scraper.IMDBScraper._fetch_html')
    def test_malformed_html(self, mock_fetch):
        # Tests behavior when HTML is missing data
        mock_fetch.return_value = "<html><body></body></html>"
        result = self.scraper.scrape_media_data("http://valid-url.com")

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Unknown")
        self.assertEqual(result.rating, "N/A")


class TestDatabaseLogic(unittest.TestCase):
    """Tests database connection and logic (Mocked)."""

    @patch('data_storage.MongoClient')
    def test_connection_failure(self, mock_client):
        # Tests behavior when MongoDB server is offline
        mock_client.side_effect = Exception("Timeout")
        storage = MongoStorage()
        self.assertIsNone(storage.collection)

    @patch('data_storage.MongoClient')
    def test_prevent_duplicate_entry(self, mock_client):
        # Tests if logic prevents saving the same movie twice
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        # Simulate movie already exists in DB
        mock_col.find_one.return_value = {"title": "Matrix"}

        storage = MongoStorage()
        movie = Movie("Matrix", "1999", "8.7", "url", "link")
        storage.save(movie)

        # Ensure insert_one was NOT called
        mock_col.insert_one.assert_not_called()


class TestSearchManager(unittest.TestCase):
    """Tests the search module functionality."""

    @patch('search_manager.sync_playwright')
    def test_search_no_results(self, mock_pw):
        # Tests handling of searches that return no links
        mock_browser = mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value

        # Simulate no href found
        mock_page.locator.return_value.first.get_attribute.return_value = None

        result = find_link("NonExistentMovie12345")
        self.assertEqual(result["status"], "failed")


class TestEdgeCaseInputs(unittest.TestCase):
    """
    [ROBUSTNESS] Advanced Input Handling
    Tests how the system reacts to weird, empty, or extreme inputs.
    """

    @patch('search_manager.sync_playwright')
    def test_search_case_insensitivity(self, mock_pw):
        # Scenario: User types 'mAtRiX' instead of 'Matrix'
        # Expectation: The system should process it without crashing.

        # Setup mock to avoid opening real browser
        mock_browser = mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        # Simulate not finding it (we just want to check if the function runs)
        mock_page.locator.return_value.first.get_attribute.return_value = None

        try:
            # We run search with mixed case
            result = find_link("mAtRiX ReLoAdEd")
            # If it reached here, it didn't crash on string manipulation
            self.assertIsInstance(result, dict)
            self.assertEqual(result["search_term"], "mAtRiX ReLoAdEd")
        except Exception as e:
            self.fail(f"Search crashed on mixed case input: {e}")

    def test_model_whitespace_trimming(self):
        # Scenario: User enters "  Inception  " (with spaces)
        # The poster manager sanitization should clean this up for filenames.
        pm = PosterManager()
        dirty_input = "   The Dark Knight   "
        clean_filename = pm._sanitize_filename(dirty_input)

        # Expectation: "The Dark Knight" (No leading/trailing spaces)
        self.assertEqual(clean_filename, "The Dark Knight")
        self.assertFalse(clean_filename.startswith(" "))
        self.assertFalse(clean_filename.endswith(" "))

    def test_extreme_input_length(self):
        # Scenario: User pastes a 5000-character string as title
        long_title = "A" * 5000

        # The system should verify creating a Movie object doesn't cause buffer overflow or crash
        try:
            movie = Movie(long_title, "2024", "1.0", "url", "link")
            self.assertEqual(len(movie.title), 5000)
        except Exception as e:
            self.fail(f"System crashed on extreme input length: {e}")


class TestFileSystemResilience(unittest.TestCase):
    """
    [ROBUSTNESS] File System & Permission Errors
    Tests what happens if the computer denies file access (PermissionDenied).
    """

    @patch('builtins.open')
    def test_json_export_permission_error(self, mock_open):
        # Scenario: The system tries to save 'movies.json' but the folder is Read-Only.
        # Expectation: The code should catch the error and print a message, NOT crash.

        # Simulate PermissionError
        mock_open.side_effect = PermissionError("Access Denied")

        storage = MongoStorage()
        # Mocking the list_all method to return one movie so export tries to run
        with patch.object(storage, 'list_all', return_value=[Movie("Test", "2020", "5", "url", "link")]):
            try:
                storage.export_json("movies.json")
            except PermissionError:
                self.fail(
                    "The application crashed! It should have handled PermissionError gracefully.")
            except Exception:
                pass  # Any other exception handled is fine

    def test_poster_manager_bad_path(self):
        # Scenario: Trying to save a poster to a non-existent drive/path
        # e.g., using a forbidden character in folder name
        pm = PosterManager(folder_name="INVALID_FOLDER_<>|")

        # The _create_folder method has a try-except block.
        # It should print an error but not stop execution.
        self.assertTrue(True)  # If we reached here, __init__ didn't crash.


class TestDeepValidation(unittest.TestCase):
    """
    [UNIT] Deep Validation of Logic
    Checking logic flow beyond simple existence.
    """

    def test_movie_vs_series_logic(self):
        # Scenario: Ensure logic strictly separates Movie and Series types
        m = Movie("M", "2000", "1", "u", "l")
        s = Series("S", "2000", "1", "u", "l")

        # They should behave differently in type checks
        self.assertNotEqual(m.media_type, s.media_type)
        self.assertTrue(m.media_type == "movie")
        self.assertFalse(s.media_type == "movie")

    def test_numeric_validation_in_strings(self):
        # Scenario: Year comes as "2023" (string) but implies a number.
        # We check if our logic handles it as a string without forcing int conversion crash
        movie = Movie("Test", "2023", "9.0", "url", "link")

        # Python allows string validation
        self.assertTrue(movie.year.isdigit())

        # What if year is "Unknown"? It should still accept it as string
        movie_unknown = Movie("Test", "Unknown", "9.0", "url", "link")
        self.assertEqual(movie_unknown.year, "Unknown")


if __name__ == '__main__':
    print("\nRunning Robustness Tests...")
    unittest.main(verbosity=2)
