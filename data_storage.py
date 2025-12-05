from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

load_dotenv() 


CLOUD_URI = os.getenv("MONGO_URI")

LOCAL_URI = "mongodb://localhost:27017/"


def get_database():
    try:
        uri = CLOUD_URI if CLOUD_URI else LOCAL_URI
        client = MongoClient(uri)
        db = client["imdb_database"]
        print(f"✔ MongoDB connection successful ({'Cloud' if CLOUD_URI else 'Local'})")
        return db
    except Exception as e:
        print("❌ MongoDB connection error:", e)
        return None


db = get_database()

collection = db["movies"] if db is not None else None



def save_to_mongodb(movie_data):
    if not collection:
        print("❌ No database connection.")
        return

    existing = collection.find_one({
        "$or": [
            {"title": movie_data.get("title")},
            {"page_url": movie_data.get("page_url")}
        ]
    })

    if existing:
        print("ℹ️ Movie already exists.")
    else:
        collection.insert_one(movie_data)
        print("💾 Movie saved.")


def list_movies():
    if not collection:
        print("❌ No database connection.")
        return

    movies = list(collection.find({}, {"_id": 0}))

    if not movies:
        print("📭 No movies saved.")
        return

    for i, movie in enumerate(movies, start=1):
        print(f"{i}. {movie.get('title')} ({movie['year']}) ⭐ {movie['rating']}")


def export_json():
    if not collection:
        print("❌ No database connection.")
        return

    movies = list(collection.find({}, {"_id": 0}))

    if not movies:
        print("📭 No movies to export.")
        return

    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)

    print("✅ movies.json exported.")