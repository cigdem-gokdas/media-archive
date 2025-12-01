from pymongo import MongoClient
import sys

MONGO_URI = "mongodb+srv://basakeris4_db_user:W75ChngTsbK3oOD9@mediaarchive.sb5mpfd.mongodb.net/?appName=MediaArchive"

def get_database():
   
    try:
        client = MongoClient(MONGO_URI)
       
        db = client['MediaArchiveDB']
        return db
    except Exception as e:
        print(f" Database error: {e}")
        return None

def save_media_to_db(media_data):
  
    db = get_database()
    if db is None:
        return

    # we used a collection named 'movies' 
    collection = db['movies']

    existing_movie = collection.find_one({"title": media_data["title"]})
    
    if existing_movie:
        print(f"This movie is already on the list: {media_data['title']}")
    else:
        #add some storage space to mongodb 
        collection.insert_one(media_data)
        print(f"Saved to database: {media_data['title']}")

def get_all_movies():
    
    db = get_database()
    collection = db['movies']
    # find all movies and shows
    movies = collection.find()
    
    print("MOVİES FROM THE ARCHIVE ")
    for movie in movies:
        print(f"- {movie.get('title')} ({movie.get('year')}) | Puan: {movie.get('rating')}")
    
