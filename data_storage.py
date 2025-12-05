from pymongo import MongoClient
import json


LOCAL_URI = "mongodb://localhost:27017/"

CLOUD_URI = "mongodb+srv://project:attempt123@cluster0.fffrqal.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"




def get_database():
   
    if CLOUD_URI and "attempt123" in CLOUD_URI:  
        try:
            client = MongoClient(CLOUD_URI)
            db = client["imdb_database"]
            print("✔ Connected to MongoDB CLOUD")
            return db
        except Exception as e:
            print("❌ Cloud connection failed:", e)

    
    try:
        client = MongoClient(LOCAL_URI)
        db = client["imdb_database"]
        print("✔ Connected to MongoDB LOCAL")
        return db
    except Exception as e:
        print("❌ Local connection failed:", e)

    return None


db = get_database()
collection = db["movies"] if db is not None else None




def save_to_mongodb(movie_data):
    if collection is None:
        print("❌ No database connection, save failed.")
        return

    
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




def list_movies():
    if collection is None:
        print("❌ No database connection.")
        return

    print("\n--- Saved Movies ---")
    movies = list(collection.find({}, {"_id": 0}))

    if not movies:
        print("📭 No saved movies.\n")
        return

    for i, movie in enumerate(movies, start=1):
        print(f"{i}. {movie.get('title')} ({movie.get('year')}) - ⭐ {movie.get('rating')}")
    print()




def export_json():
    if collection is None:
        print("❌ No database connection.")
        return

    print("\n📤 JSON export started...")

    movies = list(collection.find({}, {"_id": 0}))

    if not movies:
        print("📭 No movies found, JSON export cancelled.\n")
        return

    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)

    print("✅ movies.json created successfully!\n")