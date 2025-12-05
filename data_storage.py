from pymongo import MongoClient
import json

LOCAL_URI = "mongodb://localhost:27017/"

CLOUD_URI = None

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
    if collection is not None:
        
        existing = collection.find_one({
            "$or": [
                {"title": movie_data.get("title")},
                {"page_url": movie_data.get("page_url")}
            ]
        })

        if existing:
            print("ℹ️ This movie is already saved.")
        else:
            collection.insert_one(movie_data)
            print("💾 Movie saved to MongoDB.")
    else:
        print("❌ No database connection, save failed.")


def list_movies():
    if collection is not None:
        print("\n--- Saved Movies ---")
        movies = list(collection.find({}, {"_id": 0}))

        if not movies:
            print("📭 No saved movies.\n")
            return

        for i, movie in enumerate(movies, start=1):
            print(f"{i}. {movie.get('title')} ({movie.get('year')}) - ⭐ {movie.get('rating')}")
        print()
    else:
        print("❌ No database connection.")


def export_json():
    if collection is not None:
        print("\n📤 JSON export started...")

        movies = list(collection.find({}, {"_id": 0}))

        if not movies:
            print("📭 No movies found in database, JSON cannot be created.\n")
            return

        with open("movies.json", "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=4)

        print("✅ movies.json created successfully!\n")
    else:
        print("❌ No database connection.")