"""
This module handles data storage operations, including MongoDB connections
and JSON exports for movie data.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional
from dataclasses import asdict
import json
import os

from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Movie:
    """Dataclass representing a movie item."""
    title: str
    year: str
    rating: str
    page_url: str
    media_type: str

    poster_url: Optional[str] = None
    last_updated: Optional[str] = None
    status: Optional[str] = None


class StorageBase(ABC):
    """Defines the required storage interface for all storage types."""

    @abstractmethod
    def save(self, movie: Movie) -> None:
        """Save a movie into storage."""

    @abstractmethod
    def list_all(self) -> List[Movie]:
        """Return all stored movie objects."""

    @abstractmethod
    def export_json(self, filename: str = "movies.json") -> None:
        """Export movie list to JSON file."""


class MongoStorage(StorageBase):
    """MongoDB storage implementation using Movie dataclass."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.cloud_uri = os.getenv("MONGO_URI")
        self.local_uri = "mongodb://localhost:27017/"

        self.db = self._connect()
        if self.db is not None:
            self.collection = self.db["movies"]
        else:
            self.collection = None

    def _connect(self):
        """Connect to MongoDB."""
        try:
            uri = self.cloud_uri or self.local_uri
            client = MongoClient(uri)
            db = client["imdb_database"]
            print(
                f"Connected to MongoDB ({'Cloud' if self.cloud_uri else 'Local'})")
            return db
         # pylint: disable=broad-exception-caught
        except Exception as e:
            print("MongoDB connection error:", e)
            return None

    def save(self, movie: Movie) -> None:
        """Save Movie dataclass to MongoDB."""
        if self.collection is None:
            print("No database connection.")
            return

        movie_dict = asdict(movie)

        existing = self.collection.find_one({
            "$or": [
                {"title": movie.title},
                {"page_url": movie.page_url}
            ]
        })

        if existing:
            print(f"Movie '{movie.title}' already exists.")
            return

        self.collection.insert_one(movie_dict)
        print(f"'{movie.title}' saved successfully.")

    def list_all(self) -> List[Movie]:
        """Return all stored movies as Movie dataclasses."""
        if self.collection is None:
            print("No database connection.")
            return []

        records = list(self.collection.find({}, {"_id": 0}))

        movies = []
        for record in records:
            try:
                if not isinstance(record, dict):
                    continue

                # Check all required fields exist
                required_fields = ['title', 'year',
                                   'rating', 'page_url', 'media_type']
                if not all(k in record for k in required_fields):
                    continue

                # Extract and validate fields
                valid_keys = {k: v for k, v in record.items()
                              if k in Movie.__annotations__}

                # Ensure required fields
                valid_keys['media_type'] = record.get('media_type', 'movie')
                valid_keys['status'] = record.get('status', 'not watched')

                movies.append(Movie(**valid_keys))

            except (KeyError, ValueError, TypeError):
                # Skip corrupted records silently
                continue

        print("\n--- Saved Movies ---")
        for i, m in enumerate(movies, start=1):
            print(f"{i}. {m.title} ({m.year}) ⭐ {m.rating}")
        return movies

    def export_json(self, filename: str = "movies.json") -> None:
        """Export all movies to a JSON file."""
        try:
            movies = self.list_all()
            if not movies:
                print("No movies to export.")
                return

            data = [asdict(m) for m in movies]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"Exported to {filename} successfully.")
        except PermissionError:
            print(f" Permission denied: Cannot write to {filename}")
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(f" Error exporting JSON: {e}")
