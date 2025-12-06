"""
Main entry point for the Media Archive Manager application.
Handles user interaction, menu display, and coordinates scraping,
storage, and monitoring workflows.
"""
import sys
import time
from dotenv import load_dotenv

from falkor import falkor_db
import search_manager
from scraper import scraper
from data_storage import MongoStorage
from poster_manager import PosterManager
from monitoring import ArchiveMonitor

# Business Logic Imports
from business_logic_and_oop import Movie, Series


def print_menu():
    """
    Display the main interactive menu options to the console.
    """
    print("\n" + "="*34)
    print("MEDIA ARCHIVE MANAGER")
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
    print(f" Link found: {url}")
    print(" Fetching data...")

    # Scraper'dan MovieData objesi döner
    data = scraper.scrape_media_data(url)

    if not data:
        print(" Failed to fetch data.")
        return

    print(f"✔ Data found: {data.title} ({data.year}) - ⭐ {data.rating}")

    # ---(Movie vs Series) ---
    print("\nIs this a Movie or a TV Series?")
    print("1. Movie ")
    print("2. TV Series ")
    type_choice = input("Select (1/2): ")

    media_obj = None

    if type_choice == '1':
        # movie
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
        # tv series
        print("Status?")
        print("1. To Watch ")
        print("2. Watching ")
        print("3. Watched ")
        s_choice = input("Select (1-3): ")

        if s_choice == '2':
            status = "watching"
        elif s_choice == '3':
            status = "watched"
        else:
            status = "not watched"

        media_obj = Series(
            title=data.title,
            year=data.year,
            rating=data.rating,
            poster_url=data.poster_url,
            page_url=data.page_url,
            status=status
        )
    else:
        print(" Invalid selection.")
        return

    # Posteri indir
    if data.poster_url:
        print(" Downloading poster...")
        poster_mgr.download_poster(data.poster_url, data.title)

    # Veritabanına kaydet
    storage.save(media_obj)
    falkor_db.save_media(media_obj)


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

    print("\n---  Your Archive ---")
    for record in records:
        try:
            if "page_url" not in record:
                record["page_url"] = ""
            if "status" not in record:
                record["status"] = "not watched"

            m_type = record.get("media_type", "movie")

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
            print(
                f"Error displaying item: {record.get('title', 'Unknown')} - {e}")


def update_status_workflow(storage):
    """
    Update status logic.
    """
    if storage.collection is None:
        print("No database connection.")
        return

    search_term = input("\nEnter name to update: ").strip().lower()
    if not search_term:
        return

    # We pull all the data and filter it in Python (no uppercase/lowercase problem)
    all_media = list(storage.collection.find({}, {"_id": 0}))

    matches = []
    for media in all_media:
        if search_term in media.get("title", "").lower():
            matches.append(media)

    if not matches:
        print(" Not found.")
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

    is_series = selected.get("media_type") == "series"

    print("1. Watched ")
    print("2. Not Watched")
    if is_series:
        print("3. Watching")

    choice = input("New Status: ")
    new_status = "not watched"

    if choice == '1':
        new_status = "watched"
    elif choice == '2':
        new_status = "not watched"
    elif choice == '3' and is_series:
        new_status = "watching"
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
        choice = input("Your Choice (1-6): ").strip()

        if choice == '1':
            add_media_workflow(storage, poster_mgr)
        elif choice == '2':
            list_saved_media(storage)
        elif choice == '3':
            fn = input("Filename (movies.json): ").strip()
            if not fn:
                fn = "movies.json"
                if not fn:
                    fn = "movies.json"
            storage.export_json(fn)
        elif choice == '4':
            update_status_workflow(storage)
        elif choice == '5':
            print("\n📡 Starting monitoring mode (Press CTRL+C to stop)...")
            try:
                monitor = ArchiveMonitor(interval_hours=6)
                monitor.start()
            except KeyboardInterrupt:
                print("\n Monitoring stopped.")
        elif choice == '6':
            print("Exiting...")
            sys.exit()
        else:
            print(" Invalid choice, please try 1-6.")

        time.sleep(1)


if __name__ == "__main__":
    main()
