"""
This module handles the background monitoring of media content.
It checks for rating updates and keeps the database synchronized
by running periodic checks using the scraper and storage modules.
"""
import time
from abc import ABC, abstractmethod
from datetime import datetime

from scraper import scraper
from data_storage import MongoStorage


class MonitorBase(ABC):
    """
    Abstract base class for any monitoring system.
    """

    def __init__(self, interval_hours: int):
        """
        Initialize the monitor with a specific time interval.
        """
        self.interval_seconds = interval_hours * 3600
        self.storage = MongoStorage()

    @abstractmethod
    def check_updates(self):
        """
        Abstract method to contain the core update logic.
        """

    def get_time(self) -> str:
        """
        Returns the current timestamp as a formatted string
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ArchiveMonitor(MonitorBase):
    """
    Concrete implementation of the monitoring system for the IMDB archive.
    """

    def check_updates(self):
        """
        Fetches all movies from the database and checks for updates
        by re-scraping their data.
        """
        print(f"\n[{self.get_time()}]  Starting Update Check...")

        if self.storage.collection is None:
            print("No database connection.")
            return

        try:
            all_records = list(self.storage.collection.find({}, {"_id": 0}))
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(f"Error reading data: {e}")
            return

        if not all_records:
            print("Database is empty, nothing to monitor.")
            return

        print(f"Total {len(all_records)} items to check.")

        for record in all_records:
            self._process_item(record)
            time.sleep(2)

        print(f"[{self.get_time()}] Check Cycle Completed.")

    def _process_item(self, item: dict):
        """
        Process a single movie item: Scrape fresh data and update DB if needed.
        """
        title = item.get("title", "Unknown")
        url = item.get("page_url")
        old_rating = item.get("rating", "N/A")

        if not url:
            return

        print(f"Checking: {title}...")

        new_data = scraper.scrape_media_data(url)

        if not new_data:
            print(f"Failed to fetch data: {title}")
            return

        if new_data.rating != old_rating:
            print(f"UPDATE DETECTED: {old_rating} -> {new_data.rating}")

            if self.storage.collection is not None:
                self.storage.collection.update_one(
                    {"page_url": url},
                    {"$set": {
                        "rating": new_data.rating,
                        "year": new_data.year,
                        "poster_url": new_data.poster_url,
                        "last_updated": self.get_time()
                    }}
                )
                print("Database updated.")
        else:
            print(f"No changes. ({new_data.rating})")

    def start(self):
        """
        Starts the infinite monitoring loop.
        """
        print(f" MONITORING SYSTEM ACTIVE (Period: {self.interval_seconds}s)")

        try:
            while True:
                self.check_updates()
                print(
                    f"\n Sleeping for {self.interval_seconds} seconds for next check...\n")
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("\nStopped by user.")


if __name__ == "__main__":
    monitor = ArchiveMonitor(interval_hours=6)
    monitor.start()
