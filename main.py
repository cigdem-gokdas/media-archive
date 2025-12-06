"""
Main entry point for the Media Archive Manager application.
Handles user interaction, menu display, and coordinates scraping,
storage, and monitoring workflows.
"""
import sys
import time
from dotenv import load_dotenv

# Senin modüllerin
import search_manager
from scraper import scraper
from data_storage import MongoStorage
from poster_manager import PosterManager
from monitoring import ArchiveMonitor

# Business Logic Importları
from business_logic_and_oop import Movie, Series

def print_menu():
    """
    Display the main interactive menu options to the console.
    """
    print("\n" + "="*34)
    print("🎬 MEDIA ARCHIVE MANAGER")
    print("="*34)
    print("1. Add New Movie or TV Show")
    print("2. List Saved Media (w/ Status)")
    print("3. Export Data to JSON")
    print("4. Update Watch Status (✅/📅/▶)")
    print("5. Start Monitoring Mode")
    print("6. Exit")
    print("="*34)

def add_media_workflow(storage, poster_mgr):
    """
    Execute the workflow for adding new media:
    Search -> Scrape -> Classify -> Save
    """
    media_name = input("\nEnter movie/series name to search: ").strip()

    if not media_name:
        print("Name cannot be empty.")
        return

    search_result = search_manager.find_link(media_name)

    if search_result["status"] != "success":
        print(f"Search failed: {search_result.get('error')}")
        return

    url = search_result["url"]
    print(f"🌍 Link found: {url}")
    print("📥 Fetching data...")

    # Scraper'dan MovieData objesi döner
    data = scraper.scrape_media_data(url)

    if not data:
        print("❌ Failed to fetch data.")
        return

    print(f"✔ Data found: {data.title} ({data.year}) - ⭐ {data.rating}")

    # --- TÜR SEÇİMİ (Movie vs Series) ---
    print("\nIs this a Movie or a TV Series?")
    print("1. Movie 🎬")
    print("2. TV Series 📺")
    type_choice = input("Select (1/2): ")

    media_obj = None

    if type_choice == '1':
        # FİLM
        print("Watched? (y/n): ", end="")
        status = "watched" if input().lower() == 'y' else "not watched"
        
        media_obj = Movie(
            title=data.title,
            year=data.year,
            rating=data.rating,
            poster_url=data.poster_url,
            page_url=data.page_url,
            status=status
        )

    elif type_choice == '2':
        # DİZİ (Watching durumu var)
        print("Status?")
        print("1. To Watch (📅)")
        print("2. Watching (▶)")
        print("3. Watched (✅)")
        s_choice = input("Select (1-3): ")
        
        if s_choice == '2': status = "watching"
        elif s_choice == '3': status = "watched"
        else: status = "not watched"

        media_obj = Series(
            title=data.title,
            year=data.year,
            rating=data.rating,
            poster_url=data.poster_url,
            page_url=data.page_url,
            status=status
        )
    else:
        print("❌ Invalid selection.")
        return

    # Posteri indir
    if data.poster_url:
        print("🖼 Downloading poster...")
        poster_mgr.download_poster(data.poster_url, data.title)

    # Veritabanına kaydet
    storage.save(media_obj)

def list_saved_media(storage):
    """
    Lists media correctly distinguishing between Movie and Series.
    """
    if storage.collection is None:
        print("No database connection.")
        return

    records = list(storage.collection.find({}, {"_id": 0}))
    
    if not records:
        print("Archive is empty.")
        return

    print("\n--- 🎬 Your Archive ---")
    for record in records:
        try:
            # Eksik alanları tamamla
            if "page_url" not in record: record["page_url"] = ""
            if "status" not in record: record["status"] = "not watched"
            
            # Media Type kontrolü
            m_type = record.get("media_type", "movie") # Varsayılan movie

            # Nesneyi oluştur
            # Movie ve Series sınıflarının parametre isimleri aynı olduğu için 
            # dinamik sözlük (dictionary unpacking) kullanabiliriz.
            params = {
                "title": record.get("title"),
                "year": record.get("year"),
                "rating": record.get("rating"),
                "poster_url": record.get("poster_url"),
                "page_url": record.get("page_url"),
                "status": record.get("status")
            }

            if m_type == "series":
                obj = Series(**params)
            else:
                obj = Movie(**params)
            
            print(obj.get_info())
            
        except Exception as e:
            print(f"Error displaying item: {record.get('title', 'Unknown')} - {e}")

def update_status_workflow(storage):
    """
    Update status logic.
    """
    search_term = input("\nEnter name to update: ").strip()
    if not search_term: return

    query = {"title": {"$regex": f".{search_term}.", "$options": "i"}}
    matches = list(storage.collection.find(query))
    
    if not matches:
        print("❌ Not found.")
        return

    selected = matches[0]
    if len(matches) > 1:
        print(f"\nFound {len(matches)} matches:")
        for i, m in enumerate(matches, 1):
            print(f"{i}. {m['title']} ({m['year']})")
        try:
            sel = int(input("Select number: "))
            selected = matches[sel-1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

    print(f"\nSelected: {selected['title']}")
    current_status = selected.get('status', 'not watched')
    print(f"Current: {current_status}")

    # Diziler için ekstra seçenek sun
    is_series = selected.get("media_type") == "series"
    
    print("1. Watched (✅)")
    print("2. Not Watched (📅)")
    if is_series:
        print("3. Watching (▶)")
    
    choice = input("New Status: ")
    new_status = "not watched"
    
    if choice == '1': new_status = "watched"
    elif choice == '2': new_status = "not watched"
    elif choice == '3' and is_series: new_status = "watching"
    else:
        print("Cancelled/Invalid.")
        return

    storage.collection.update_one(
        {"title": selected['title']},
        {"$set": {"status": new_status}}
    )
    print(f"✔ Updated to: {new_status.upper()}")

def main():
    """Main Loop"""
    load_dotenv()
    storage = MongoStorage()
    poster_mgr = PosterManager()

    while True:
        print_menu()
        choice = input("Your Choice (1-6): ")

        if choice == '1':
            add_media_workflow(storage, poster_mgr)
        elif choice == '2':
            list_saved_media(storage)
        elif choice == '3':
            fn = input("Filename (movies.json): ")
            if not fn: fn = "movies."