import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from data_storage import db_manager, DatabaseManager
from scraper import scraper_engine, BaseScraper


class BaseMonitor(ABC):

    def __init__(self, interval_hours: int):
        self.interval_seconds = interval_hours * 3600

    @abstractmethod
    def run_cycle(self):

        pass

    def get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MovieMonitor(BaseMonitor):

    def __init__(self, check_interval_hours=24):

        super().__init__(check_interval_hours)

    def run_cycle(self):
        print(f"\n[{self.get_timestamp()}]  STARTING MONITORING CYCLE...")

        movies = db_manager.get_all_movies()
        total = len(movies)

        if total == 0:
            print(" Database is empty. Nothing to monitor.")
            return

        print(f" Found {total} movies in the watchlist.")

        for movie in movies:
            self._check_single_movie(movie)
            time.sleep(3)

        print(f"[{self.get_timestamp()}]  CYCLE COMPLETE.")

    def _check_single_movie(self, movie_doc):
        title = movie_doc.get("title", "Unknown")
        url = movie_doc.get("page_url")
        old_rating = movie_doc.get("rating", "N/A")

        if not url:
            return

        print(f"Checking: {title}...")
        new_data = scraper_engine.scrape(url)

        if not new_data:
            print(f" Failed to fetch data for '{title}'.")
            return

        if new_data.rating != old_rating:
            print(
                f"UPDATE: Rating changed {old_rating} -> {new_data.rating}")

            db_manager.update_movie_rating(
                movie_id=movie_doc["_id"],
                new_rating=new_data.rating,
                new_year=new_data.year,
                new_poster=new_data.poster_url,
                timestamp=self.get_timestamp()
            )
            print(" Database updated.")
        else:
            print(f"   💤 No change. ({new_data.rating})")
            db_manager.log_check(movie_doc["_id"], self.get_timestamp())

    def start(self):

        print("=" * 40)
        print("       IMDB MONITORING SYSTEM (OOP)       ")
        print(f"       Interval: {self.interval_seconds / 3600} hours")
        print("=" * 40)

        try:
            while True:
                self.run_cycle()
                print(f"\n⏳ Sleeping for {self.interval_seconds} seconds...\n")
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("\n Monitoring stopped by user.")


if __name__ == "__main__":
    app = MovieMonitor(check_interval_hours=6)
    app.start()
