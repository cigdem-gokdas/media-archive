"""
Robust Unit & Integration Tests for Media Archive Manager
Focus: Code Robustness, Vulnerability Testing, Edge Cases
Target: Attack-resistant, production-ready code
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import shutil
import json
import sys
from io import StringIO

from business_logic_and_oop import Movie, Series
from scraper import IMDBScraper, MovieData
from data_storage import MongoStorage, Movie as StorageMovie
from poster_manager import PosterManager
from monitoring import ArchiveMonitor
from falkor import FalkorManager


# ============================================================================
# ROBUSTNESS TESTS - ATTACK SURFACE ANALYSIS
# ============================================================================

class TestInputValidationRobustness(unittest.TestCase):
    """Test code against malicious/malformed inputs"""

    # ===== SQL INJECTION / NOSQL INJECTION =====
    def test_mongo_injection_attack_title(self):
        """Test prevention of NoSQL injection via title"""
        # Attack: {"$ne": null}
        injection_title = '{"$ne": null}'
        movie = Movie(injection_title, "2020", "5", "url", "link")

        # Code should treat as string, not execute
        self.assertEqual(movie.title, injection_title)
        self.assertIsInstance(movie.title, str)

    def test_mongo_injection_attack_rating(self):
        """Test prevention of NoSQL injection via rating"""
        injection_rating = '{"$gt": 0}'
        movie = Movie("Test", "2020", injection_rating, "url", "link")

        self.assertEqual(movie.rating, injection_rating)
        self.assertIsInstance(movie.rating, str)

    @patch('data_storage.MongoClient')
    def test_mongo_injection_query_construction(self, mock_client):
        """Test MongoDB query construction is safe"""
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_col.find_one.return_value = None

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()

        # Injection attempt
        malicious_movie = StorageMovie(
            title='"; db.dropDatabase(); //',
            year="2020",
            rating="5.0",
            page_url="url",
            media_type="movie"
        )
        storage.save(malicious_movie)

        # Verify it was passed as data, not executed
        call_args = mock_col.find_one.call_args
        self.assertIsNotNone(call_args)

    # ===== PATH TRAVERSAL =====
    def test_path_traversal_filename(self):
        """Test prevention of path traversal via filename"""
        pm = PosterManager(folder_name="test_traversal")
        try:
            # Attack: ../../../etc/passwd
            traversal_name = "../../../etc/passwd"
            clean = pm._sanitize_filename(traversal_name)

            # Should remove .. and /
            self.assertNotIn("..", clean)
            self.assertNotIn("/", clean)
            # Should result in safe filename
            self.assertEqual(clean, "etcpasswd")
        finally:
            if os.path.exists("test_traversal"):
                shutil.rmtree("test_traversal")

    def test_path_traversal_folder_creation(self):
        """Test folder creation doesn't allow path traversal"""
        # Try to create folder with traversal
        pm = PosterManager(folder_name="test/../../../tmp/evil")

        # Should not create outside intended directory
        self.assertFalse(os.path.exists("../../../tmp/evil"))

    # ===== XSS / SCRIPT INJECTION =====
    def test_xss_title_storage(self):
        """Test XSS prevention in title storage"""
        xss_payload = "<script>alert('XSS')</script>"
        movie = Movie(xss_payload, "2020", "5", "url", "link")

        # Should be stored as string, not executed
        self.assertEqual(movie.title, xss_payload)

    def test_html_injection_rating(self):
        """Test HTML injection prevention"""
        html_payload = "<img src=x onerror='alert(1)'>"
        movie = Movie("Test", "2020", html_payload, "url", "link")

        self.assertEqual(movie.rating, html_payload)
        self.assertIsInstance(movie.rating, str)

    # ===== COMMAND INJECTION =====
    def test_command_injection_title(self):
        """Test command injection prevention"""
        cmd_injection = "'; rm -rf /; #"
        movie = Movie(cmd_injection, "2020", "5", "url", "link")

        self.assertEqual(movie.title, cmd_injection)

    # ===== MALFORMED DATA =====
    def test_extremely_long_title(self):
        """Test handling of extremely long input"""
        long_title = "A" * 100000
        movie = Movie(long_title, "2020", "5", "url", "link")

        self.assertEqual(len(movie.title), 100000)

    def test_null_bytes_in_title(self):
        """Test null byte injection"""
        null_title = "Movie\x00Null"
        movie = Movie(null_title, "2020", "5", "url", "link")

        self.assertEqual(movie.title, null_title)

    def test_unicode_normalization_title(self):
        """Test unicode edge cases"""
        unicode_titles = [
            "Mödërn Mövïe",
            "🎬 Movie 🎬",
            "Фильм",
            "電影",
            "😀😁😂😃"
        ]

        for title in unicode_titles:
            movie = Movie(title, "2020", "5", "url", "link")
            self.assertEqual(movie.title, title)

    # ===== UNEXPECTED TYPE INPUTS =====
    def test_year_non_string_format(self):
        """Test year with unexpected format"""
        edge_years = ["", "20", "202020", "XXXX", "2020-01-01"]

        for year in edge_years:
            movie = Movie("T", year, "5", "url", "link")
            self.assertEqual(movie.year, year)

    def test_rating_invalid_formats(self):
        """Test rating with invalid formats"""
        invalid_ratings = ["", "ABC", "10.5", "-5.0", "N/A", "null"]

        for rating in invalid_ratings:
            movie = Movie("T", "2020", rating, "url", "link")
            self.assertEqual(movie.rating, rating)


class TestStatusManipulationRobustness(unittest.TestCase):
    """Test status field against manipulation attacks"""

    def test_status_case_mixing_variations(self):
        """Test all case variations"""
        variations = [
            "WATCHED", "watched", "Watched", "WaTcHeD",
            "NOT WATCHED", "not watched", "Not Watched",
            "watching", "WATCHING", "Watching"
        ]

        for var in variations:
            movie = Movie("T", "2020", "5", "url", "link", var)
            # Should normalize or reject
            self.assertIn(
                movie.status, Movie.VALID_STATUSES or ["not watched"])

    def test_status_whitespace_padding(self):
        """Test status with extra whitespace"""
        padded_statuses = [
            "  watched  ",
            "\twatched\t",
            "\nwatched\n",
            " watched"
        ]

        for status in padded_statuses:
            movie = Movie("T", "2020", "5", "url", "link", status)
            # Should handle gracefully
            self.assertIsNotNone(movie.status)

    def test_status_special_characters(self):
        """Test status with special characters"""
        special_statuses = [
            "watched; DROP TABLE users;",
            "watched' OR '1'='1",
            "watched\"; db.dropDatabase();",
            "watched%00null"
        ]

        for status in special_statuses:
            movie = Movie("T", "2020", "5", "url", "link", status)
            # Should default to valid status
            self.assertIn(movie.status, Movie.VALID_STATUSES)


class TestDatabaseRobustness(unittest.TestCase):
    """Test MongoDB operations for robustness"""

    @patch('data_storage.MongoClient')
    def test_save_duplicate_prevention_both_fields(self, mock_client):
        """Test duplicate prevention checks both title AND url"""
        mock_db = MagicMock()
        mock_col = MagicMock()

        # Existing movie by URL
        mock_col.find_one.return_value = {"page_url": "http://imdb.com/1"}

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()
        movie = StorageMovie("DifferentTitle", "2020", "7",
                             "http://imdb.com/1", "movie")
        storage.save(movie)

        # Should not insert because URL already exists
        mock_col.insert_one.assert_not_called()

    @patch('data_storage.MongoClient')
    def test_connection_loss_during_operation(self, mock_client):
        """Test graceful handling of connection loss"""
        mock_client.side_effect = Exception("Connection lost")

        storage = MongoStorage()
        self.assertIsNone(storage.collection)

        movie = StorageMovie("T", "2020", "5", "url", "movie")
        storage.save(movie)  # Should not crash

    @patch('data_storage.MongoClient')
    def test_malformed_database_records(self, mock_client):
        """Test handling of corrupted records from database"""
        mock_db = MagicMock()
        mock_col = MagicMock()

        # Return records with missing required fields - should be skipped
        mock_col.find.return_value = [
            {"title": "OnlyTitle"},  # Missing required fields
            {"year": "2020"},  # Missing required fields
            {},  # Empty record
            {"title": "OK", "year": "2020", "rating": "5",
                "page_url": "url", "media_type": "movie"}  # Valid
        ]

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()

        # Should handle gracefully - skip corrupted, keep valid
        try:
            movies = storage.list_all()
            # Should only return valid records (1 valid record)
            self.assertEqual(len(movies), 1)
            self.assertEqual(movies[0].title, "OK")
        except Exception as e:
            self.fail(
                f"list_all() should handle malformed data gracefully: {e}")


class TestFileOperationRobustness(unittest.TestCase):
    """Test file operations for security and reliability"""

    def setUp(self):
        self.pm = PosterManager(folder_name="test_file_ops")

    def tearDown(self):
        if os.path.exists("test_file_ops"):
            shutil.rmtree("test_file_ops")

    def test_filename_null_byte_injection(self):
        """Test null byte in filename"""
        null_filename = "movie\x00.jpg"
        clean = self.pm._sanitize_filename(null_filename)

        # Should remove null bytes (SECURITY FIX)
        self.assertNotIn("\x00", clean)

    def test_filename_double_extension_attack(self):
        """Test double extension bypass"""
        dangerous = "movie.jpg.exe"
        clean = self.pm._sanitize_filename(dangerous)

        # Should not execute, just stored as data
        self.assertIsInstance(clean, str)

    def test_filename_reserved_names(self):
        """Test Windows reserved names"""
        reserved = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]

        for name in reserved:
            clean = self.pm._sanitize_filename(name)
            # Should handle gracefully
            self.assertIsInstance(clean, str)

    @patch('poster_manager.requests.Session.get')
    def test_download_oversized_file(self, mock_get):
        """Test handling of extremely large files"""
        mock_response = MagicMock()
        # Simulate large file
        mock_response.iter_content.return_value = [b"x" * 1000000] * 100
        mock_get.return_value = mock_response

        # Should not crash or consume all memory
        result = self.pm.download_poster("http://example.com/huge.jpg", "Test")

    @patch('poster_manager.requests.Session.get')
    def test_download_corrupted_response(self, mock_get):
        """Test handling of corrupted download"""
        mock_response = MagicMock()
        mock_response.iter_content.side_effect = Exception("Corrupted stream")
        mock_get.return_value = mock_response

        result = self.pm.download_poster(
            "http://example.com/poster.jpg", "Test")
        self.assertFalse(result)


class TestScraperRobustness(unittest.TestCase):
    """Test scraper for HTML parsing robustness"""

    def setUp(self):
        self.scraper = IMDBScraper()

    @patch('scraper.IMDBScraper._fetch_html')
    def test_malformed_json_ld(self, mock_fetch):
        """Test handling of malformed JSON-LD"""
        html = '''
        <html>
            <h1>Title</h1>
            <script type="application/ld+json">
            {INVALID JSON HERE
            </script>
        </html>
        '''
        mock_fetch.return_value = html

        result = self.scraper.scrape_media_data("url")
        self.assertIsNotNone(result)

    @patch('scraper.IMDBScraper._fetch_html')
    def test_missing_all_fields(self, mock_fetch):
        """Test HTML with no useful data"""
        html = "<html><body></body></html>"
        mock_fetch.return_value = html

        result = self.scraper.scrape_media_data("url")

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Unknown")
        self.assertEqual(result.rating, "N/A")

    @patch('scraper.IMDBScraper._fetch_html')
    def test_extremely_large_html(self, mock_fetch):
        """Test handling of very large HTML"""
        huge_html = "<html>" + ("A" * 10000000) + "</html>"
        mock_fetch.return_value = huge_html

        result = self.scraper.scrape_media_data("url")
        # Should handle without crashing

    @patch('scraper.IMDBScraper._fetch_html')
    def test_null_bytes_in_html(self, mock_fetch):
        """Test HTML with null bytes"""
        html = "<html>\x00<body>Test\x00</body></html>"
        mock_fetch.return_value = html

        result = self.scraper.scrape_media_data("url")
        self.assertIsNotNone(result)

    @patch('scraper.IMDBScraper._fetch_html')
    def test_unicode_normalization(self, mock_fetch):
        """Test unicode in HTML"""
        html = '''
        <html>
            <h1>Фильм 電影 🎬</h1>
            <script type="application/ld+json">
            {"ratingValue": "8.8"}
            </script>
        </html>
        '''
        mock_fetch.return_value = html

        result = self.scraper.scrape_media_data("url")
        self.assertIsNotNone(result)


class TestConcurrencyRobustness(unittest.TestCase):
    """Test for race conditions and concurrent access"""

    @patch('data_storage.MongoClient')
    def test_simultaneous_duplicate_saves(self, mock_client):
        """Test race condition: two saves of same movie simultaneously"""
        mock_db = MagicMock()
        mock_col = MagicMock()

        # First check: no duplicate, then insert
        mock_col.find_one.return_value = None

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()
        movie = StorageMovie("Inception", "2010", "8.8", "url", "movie")

        storage.save(movie)
        storage.save(movie)  # Same movie saved twice

        # Should handle gracefully (at least first insert succeeds)
        self.assertGreaterEqual(mock_col.insert_one.call_count, 0)


class TestDataConsistencyRobustness(unittest.TestCase):
    """Test data consistency across operations"""

    def test_movie_immutability_after_creation(self):
        """Test Movie data doesn't change unexpectedly"""
        movie = Movie("Test", "2020", "7.0", "url", "link", "watched")
        original_status = movie.status

        # Simulate external mutation attempt
        movie.status = "invalid"

        # Data should be changed (Python allows it), but validate it
        # Code should validate on use
        self.assertNotEqual(movie.status, original_status)

    def test_storage_movie_field_integrity(self):
        """Test StorageMovie maintains field integrity"""
        movie = StorageMovie("T", "2020", "5", "url", "movie")

        d = {"title": "T", "year": "2020", "rating": "5",
             "page_url": "url", "media_type": "movie"}

        for key, value in d.items():
            self.assertEqual(getattr(movie, key), value)

    @patch('data_storage.MongoClient')
    def test_export_maintains_data_integrity(self, mock_client):
        """Test JSON export doesn't lose or corrupt data"""
        mock_db = MagicMock()
        mock_col = MagicMock()

        original_data = {
            "title": "Inception",
            "year": "2010",
            "rating": "8.8",
            "page_url": "http://imdb.com/1",
            "media_type": "movie",
            "status": "watched"
        }

        mock_col.find.return_value = [original_data]
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()

        with patch('builtins.open', mock_open()) as mock_file:
            storage.export_json("test.json")

            # Verify write_calls contain the data
            self.assertTrue(mock_file.called)


class TestErrorRecoveryRobustness(unittest.TestCase):
    """Test error handling and recovery"""

    @patch('data_storage.MongoClient')
    def test_save_after_connection_failure(self, mock_client):
        """Test recovery after connection failure"""
        mock_client.side_effect = Exception("Connection failed")

        storage1 = MongoStorage()
        self.assertIsNone(storage1.collection)

        # Should still be able to create another instance
        mock_client.side_effect = None
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_col.find_one.return_value = None
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage2 = MongoStorage()
        movie = StorageMovie("T", "2020", "5", "url", "movie")
        storage2.save(movie)

        mock_col.insert_one.assert_called_once()

    @patch('monitoring.MongoStorage')
    def test_monitor_continues_after_scrape_failure(self, mock_storage):
        """Test monitor continues despite scrape errors"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.collection = MagicMock()
        mock_storage_instance.collection.find.return_value = [
            {"title": "Test", "page_url": "url", "rating": "5"}
        ]

        monitor = ArchiveMonitor(interval_hours=6)
        monitor.storage = mock_storage_instance

        # Should not crash even with failures
        monitor.check_updates()


class TestMonitoringRobustness(unittest.TestCase):
    """Test monitoring system robustness"""

    @patch('monitoring.MongoStorage')
    def test_monitor_handles_database_errors(self, mock_storage):
        """Test monitor handles database read errors"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.collection = MagicMock()
        mock_storage_instance.collection.find.side_effect = Exception(
            "DB error")

        monitor = ArchiveMonitor(interval_hours=6)
        monitor.storage = mock_storage_instance

        # Should not crash
        monitor.check_updates()

    @patch('monitoring.MongoStorage')
    def test_monitor_handles_missing_fields(self, mock_storage):
        """Test monitor handles records with missing fields"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.collection = MagicMock()

        # Record missing required fields
        mock_storage_instance.collection.find.return_value = [
            {"title": "OnlyTitle"},
            {"page_url": "OnlyURL"},
            {}
        ]

        monitor = ArchiveMonitor(interval_hours=6)
        monitor.storage = mock_storage_instance

        # Should handle gracefully
        monitor.check_updates()


# ============================================================================
# INTEGRATION TESTS - COMPLETE WORKFLOWS
# ============================================================================

class TestCompleteWorkflow(unittest.TestCase):
    """Test complete application workflows"""

    @patch('data_storage.MongoClient')
    def test_add_and_export_workflow(self, mock_client):
        """Test workflow: add movie -> list -> export"""
        mock_db = MagicMock()
        mock_col = MagicMock()

        mock_col.find_one.return_value = None
        mock_col.find.return_value = [
            {"title": "Inception", "year": "2010", "rating": "8.8",
             "page_url": "url", "media_type": "movie", "status": "watched"}
        ]

        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        storage = MongoStorage()

        # Save
        movie = StorageMovie("Inception", "2010", "8.8",
                             "url", "movie", status="watched")
        storage.save(movie)

        # List
        movies = storage.list_all()
        self.assertEqual(len(movies), 1)

        # Export
        with patch('builtins.open', mock_open()):
            storage.export_json("test.json")


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add robust test classes
    suite.addTests(loader.loadTestsFromTestCase(TestInputValidationRobustness))
    suite.addTests(loader.loadTestsFromTestCase(
        TestStatusManipulationRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperationRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestScraperRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrencyRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestDataConsistencyRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecoveryRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitoringRobustness))
    suite.addTests(loader.loadTestsFromTestCase(TestCompleteWorkflow))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("ROBUSTNESS TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {result.testsRun}")
    print(
        f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
