from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



@dataclass
class Movie:
    title: str
    year: str
    rating: str
    page_url: str


class StorageBase(ABC):

    @abstractmethod
    def save(self, movie: Movie) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List[Movie]:
        pass

    @abstractmethod
    def export_json(self, filename: str = "movies.json") -> None:
        pass



class MongoStorage(StorageBase):

    def __init__(self):
        self.cloud_uri = os.getenv("MONGO_URI")
        self.local_uri = "mongodb://localhost:27017/"

        self.db = self._connect()
        self.collection = self.db["movies"] if self.db else None

    def _connect(self):

        try:
            uri = self.cloud_uri or self.local_uri
            client = MongoClient(uri)
            db = client["imdb_database"]

            print(f"✔ Connected to MongoDB ({'Cloud' if self.cloud_uri else 'Local'})")
            return db

        except Exception as e:
            print("❌ MongoDB connection error:", e)
            return None


    def save(self, movie: Movie) -> None:

        if not self.collection:
            print("❌ No database connection.")
            return

        movie_dict = asdict(movie)

        existing = self.collection.find_one({
            "$or": [
                {"title": movie.title},
                {"page_url": movie.page_url}
            ]
        })

        if existing:
            print(f"ℹ️ Movie '{movie.title}' already exists.")
            return

        self.collection.insert_one(movie_dict)
        print(f"💾 '{movie.title}' saved successfully.")

    def list_all(self) -> List[Movie]:

        if not self.collection:
            print("❌ No database connection.")
            return []

        records = list(self.collection.find({}, {"_id": 0}))
        movies = [Movie(**record) for record in records]

        print("\n--- Saved Movies ---")
        for i, m in enumerate(movies, start=1):
            print(f"{i}. {m.title} ({m.year}) ⭐ {m.rating}")

        return movies

    def export_json(self, filename: str = "movies.json") -> None:

        movies = self.list_all()

        if not movies:
            print("📭 No movies to export.")
            return

        data = [asdict(movie) for movie in movies]

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ Exported to {filename} successfully.")