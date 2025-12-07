"""
Unit tests for Media Archive Manager project.

This module validates the correctness of OOP models, database operations,
and file handling. Edge cases and error scenarios are tested to ensure
code robustness and fault tolerance.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import shutil

from business_logic_and_oop import Movie, Series
from scraper import IMDBScraper
from data_storage import MongoStorage, Movie as StorageMovie
from poster_manager import PosterManager
from search_manager import find_link


class TestMediaModels(unittest.TestCase):
    """Test OOP classes (Movie and Series) for data integrity."""

    def test_movie_creation(self):
        """Test Movie object creation with correct media_type."""
        movie = Movie("Matrix", "1999", "8.7", "url", "link", "watched")
        self.assertEqual(movie.media_type, "movie")
        self.assertIn("MOVIE", movie.get_info())

    def test_series_creation(self):
        """Test Series object creation with correct media_type."""
        series = Series("Friends", "1994", "8.9", "url", "link", "watching")
        self.assertEqual(series.media_type, "series")
        self.assertIn("SERIES", series.get_info())

    def test_case_sensitivity_status(self):
        """Test that uppercase status is normalized to lowercase."""
        movie_upper = Movie("Test", "2020", "5.0", "url",
                            "link", status="WATCHED")
        self.assertEqual(movie_upper.status, "watched")

    def test_to_dict_method(self):
        """Test conversion of Movie object to dictionary."""
        movie = Movie("A", "2000", "5.0", "url", "link")
        data = movie.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["title"], "A")


class TestInputSanitization(unittest.TestCase):
    """Test filename sanitization for poster storage."""

    def setUp(self):
        """Create temporary folder for test posters."""
        self.pm = PosterManager(folder_name="test_posters")

    def tearDown(self):
        """Clean up temporary folder after tests."""
        if os.path.exists("test_posters"):
            shutil.rmtree("test_posters")

    def test_sanitize_filename_forbidden_chars(self):
        """Test removal of invalid filesystem characters."""
        dirty_title = "Face/Off: <The Movie> *2023*"
        # pylint: disable=protected-access
        clean_name = self.pm._sanitize_filename(dirty_title)

        self.assertNotIn("/", clean_name)
        self.assertNotIn(":", clean_name)
        self.assertNotIn("*", clean_name)
        self.assertNotIn("<", clean_name)

    def test_sanitize_whitespace(self):
        """Test trimming and normalization of whitespace."""
        dirty_title = "   Inception    Movie   "
        # pylint: disable=protected-access
        clean_name = self.pm._sanitize_filename(dirty_title)
        self.assertEqual(clean_name, "Inception Movie")


class TestScraperRobustness(unittest.TestCase):
    """Test scraper error handling and edge cases."""

    def setUp(self):
        """Initialize scraper instance."""
        self.scraper = IMDBScraper()

    @patch('scraper.IMDBScraper._fetch_html')
    def test_network_failure(self, mock_fetch):
        """Test scraper gracefully handles network failures."""
        mock_fetch.return_value = None
        result = self.scraper.scrape_media_data("http://valid-url.com")
        self.assertIsNone(result)

    @patch('scraper.IMDBScraper._fetch_html')
    def test_malformed_html(self, mock_fetch):
        """Test scraper handles malformed HTML gracefully."""
        mock_fetch.return_value = "<html><body></body></html>"
        result = self.scraper.scrape_media_data("http://valid-url.com")

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Unknown")
        self.assertEqual(result.rating, "N/A")


class TestDatabaseLogic(unittest.TestCase):
    """Test MongoDB connection and CRUD operations."""

    @patch('data_storage.MongoClient')
    def test_connection_failure(self, mock_client):
        """Test handling of database connection failure."""
        mock_client.side_effect = Exception("Timeout")
        storage = MongoStorage()
        self.assertIsNone(storage.collection)

    @patch('data_storage.MongoClient')
    def test_prevent_duplicate_entry(self, mock_client):
        """Test prevention of duplicate movie entries."""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        # Simulate existing movie in database
        mock_col.find_one.return_value = {"title": "Matrix"}

        storage = MongoStorage()
        movie = Movie("Matrix", "1999", "8.7", "url", "link")
        storage.save(movie)

        # Verify insert_one was not called
        mock_col.insert_one.assert_not_called()


class TestSearchManager(unittest.TestCase):
    """Test IMDb search functionality."""

    @patch('search_manager.sync_playwright')
    def test_search_no_results(self, mock_pw):
        """Test handling of search with no results."""
        mock_browser = (
            mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        )
        mock_page = mock_browser.new_context.return_value.new_page.return_value

        # Simulate no search results
        mock_page.locator.return_value.first.get_attribute.return_value = None

        result = find_link("NonExistentMovie12345")
        self.assertEqual(result["status"], "failed")


class TestEdgeCaseInputs(unittest.TestCase):
    """Test robustness against unusual and extreme inputs."""

    @patch('search_manager.sync_playwright')
    def test_search_case_insensitivity(self, mock_pw):
        """Test that search handles mixed-case input correctly."""
        mock_browser = (
            mock_pw.return_value.__enter__.return_value.chromium.launch.return_value
        )
        mock_page = mock_browser.new_context.return_value.new_page.return_value
        mock_page.locator.return_value.first.get_attribute.return_value = None

        try:
            # Test with mixed-case input
            result = find_link("mAtRiX ReLoAdEd")
            self.assertIsInstance(result, dict)
            self.assertEqual(result["search_term"], "mAtRiX ReLoAdEd")
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.fail(f"Search failed with mixed-case input: {err}")

    def test_model_whitespace_trimming(self):
        """Test that whitespace is properly trimmed from filenames."""
        poster_mgr = PosterManager()
        dirty_input = "   The Dark Knight   "
        # pylint: disable=protected-access
        clean_filename = poster_mgr._sanitize_filename(dirty_input)

        self.assertEqual(clean_filename, "The Dark Knight")
        self.assertFalse(clean_filename.startswith(" "))
        self.assertFalse(clean_filename.endswith(" "))

    def test_extreme_input_length(self):
        """Test that system handles extremely long titles without crashing."""
        long_title = "A" * 5000

        try:
            movie = Movie(long_title, "2024", "1.0", "url", "link")
            self.assertEqual(len(movie.title), 5000)
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.fail(f"System crashed on extreme length input: {err}")


class TestFileSystemResilience(unittest.TestCase):
    """Test handling of filesystem errors and permission issues."""

    @patch('builtins.open')
    def test_json_export_permission_error(self, mock_open):
        """Test graceful handling of file write permission errors."""
        mock_open.side_effect = PermissionError("Access Denied")

        storage = MongoStorage()
        fake_movie = Movie("Test", "2020", "5", "url", "link")
        with patch.object(storage, 'list_all', return_value=[fake_movie]):
            try:
                storage.export_json("movies.json")
            except PermissionError:
                self.fail(
                    "Application crashed: PermissionError not handled properly"
                )
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    def test_poster_manager_bad_path(self):
        """Test handling of invalid folder path."""
        # pylint: disable=unused-variable
        PosterManager(folder_name="INVALID_FOLDER_<>|")
        # Should not crash due to try-except in _create_folder


class TestDeepValidation(unittest.TestCase):
    """Test business logic consistency."""

    def test_movie_vs_series_logic(self):
        """Test that Movie and Series types are properly differentiated."""
        mov = Movie("M", "2000", "1", "u", "l")
        ser = Series("S", "2000", "1", "u", "l")

        self.assertNotEqual(mov.media_type, ser.media_type)
        self.assertTrue(mov.media_type == "movie")
        self.assertFalse(ser.media_type == "movie")

    def test_numeric_validation_in_strings(self):
        """Test that year field accepts both numeric and unknown values."""
        movie = Movie("Test", "2023", "9.0", "url", "link")
        self.assertTrue(movie.year.isdigit())

        # Test with non-numeric year
        movie_unknown = Movie("Test", "Unknown", "9.0", "url", "link")
        self.assertEqual(movie_unknown.year, "Unknown")


class TestMongoStorageListAll(unittest.TestCase):
    """Test MongoDB list_all() retrieval functionality."""

    @patch('data_storage.MongoClient')
    def test_list_all_returns_movie_objects(self, mock_client):
        """Test that list_all() returns Movie dataclass instances."""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        mock_col.find.return_value = [
            {
                "title": "Inception",
                "year": "2010",
                "rating": "8.8",
                "page_url": "https://imdb.com/title/tt1375666/"
            }
        ]

        storage = MongoStorage()
        movies = storage.list_all()

        self.assertEqual(len(movies), 1)
        self.assertIsInstance(movies[0], StorageMovie)
        self.assertEqual(movies[0].title, "Inception")


class TestMovieAndSeriesComparison(unittest.TestCase):
    """Test Movie and Series object differentiation."""

    def test_movie_different_from_series(self):
        """Test that Movie and Series have distinct media_type values."""
        movie = Movie("Test Movie", "2020", "7.5", "url", "link", "watched")
        series = Series("Test Series", "2020", "7.5",
                        "url", "link", "watching")

        self.assertEqual(movie.media_type, "movie")
        self.assertEqual(series.media_type, "series")
        self.assertNotEqual(movie.media_type, series.media_type)

    def test_series_has_watching_status(self):
        """Test that Series accepts watching status but Movie rejects it."""
        series = Series("Breaking Bad", "2008", "9.5",
                        "url", "link", "watching")
        self.assertEqual(series.status, "watching")

        # Movie should normalize invalid status
        movie = Movie("Test", "2020", "7.0", "url", "link", "watching")
        self.assertNotEqual(movie.status, "watching")


class TestStatusNormalization(unittest.TestCase):
    """Test status field normalization and validation."""

    def test_movie_status_case_insensitive(self):
        """Test that Movie status is normalized to lowercase."""
        movie1 = Movie("T1", "2020", "5", "u", "l", "WATCHED")
        movie2 = Movie("T2", "2020", "5", "u", "l", "WaTcHeD")

        self.assertEqual(movie1.status, "watched")
        self.assertEqual(movie2.status, "watched")

    def test_series_status_normalization(self):
        """Test that Series status handles all valid variations."""
        series1 = Series("T1", "2020", "5", "u", "l", "WATCHING")
        series2 = Series("T2", "2020", "5", "u", "l", "NoT WaTcHeD")

        self.assertEqual(series1.status, "watching")
        self.assertEqual(series2.status, "not watched")

    def test_invalid_status_defaults_correctly(self):
        """Test that invalid status defaults to not watched."""
        movie = Movie("T", "2020", "5", "u", "l", "invalid_status")
        series = Series("T", "2020", "5", "u", "l", "invalid_status")

        self.assertEqual(movie.status, "not watched")
        self.assertEqual(series.status, "not watched")


class TestDatabaseSaveWithoutDuplicate(unittest.TestCase):
    """Test duplicate prevention in database operations."""

    @patch('data_storage.MongoClient')
    def test_save_prevents_duplicate_title(self, mock_client):
        """Test that save() prevents duplicate titles."""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        mock_col.find_one.return_value = {"title": "Matrix"}

        storage = MongoStorage()
        movie = StorageMovie("Matrix", "1999", "8.7", "url", "link")
        storage.save(movie)

        mock_col.insert_one.assert_not_called()

    @patch('data_storage.MongoClient')
    def test_save_prevents_duplicate_url(self, mock_client):
        """Test that save() prevents duplicate URLs."""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        mock_col.find_one.return_value = {
            "page_url": "https://imdb.com/title/tt0133093/"
        }

        storage = MongoStorage()
        movie = StorageMovie(
            "The Matrix", "1999", "8.7", "url",
            "https://imdb.com/title/tt0133093/"
        )
        storage.save(movie)

        mock_col.insert_one.assert_not_called()


class TestPosterFilenameValidation(unittest.TestCase):
    """Test poster manager filename validation and sanitization."""

    def setUp(self):
        """Initialize PosterManager for testing."""
        self.pm = PosterManager(folder_name="test_posters_validation")

    def tearDown(self):
        """Clean up test folder after tests."""
        if os.path.exists("test_posters_validation"):
            shutil.rmtree("test_posters_validation")

    def test_filename_removes_special_chars(self):
        """Test removal of invalid filesystem characters from filenames."""
        # Test various invalid characters
        invalid_titles = [
            "Movie: The Sequel",
            "Film / Part 1",
            'Movie "The Best"',
            "Show * Episode 1",
            "Title <2024>",
            "Film | Director's Cut"
        ]

        for title in invalid_titles:
            # pylint: disable=protected-access
            clean = self.pm._sanitize_filename(title)

            # Verify no invalid characters remain
            invalid_chars = [':', '/', '"', '*', '<', '>', '|', '?']
            for char in invalid_chars:
                self.assertNotIn(
                    char, clean,
                    f"Character '{char}' found in: {clean}"
                )

    def test_filename_trims_whitespace(self):
        """Test that whitespace is properly trimmed from filenames."""
        titles = [
            ("   Inception   ", "Inception"),
            ("The   Dark   Knight", "The Dark Knight"),
            ("  Multiple  Spaces  ", "Multiple Spaces")
        ]

        for dirty, expected in titles:
            # pylint: disable=protected-access
            clean = self.pm._sanitize_filename(dirty)
            self.assertEqual(clean, expected)


if __name__ == '__main__':
    print("\nRunning Media Archive Manager Test Suite...")
    print("=" * 60)
    unittest.main(verbosity=2)
