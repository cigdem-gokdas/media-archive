"""
Main entry point for the Media Archive Manager application.
Handles user interaction, menu display, and coordinates scraping,
storage, and monitoring workflows.
"""
import sys
import time
from dotenv import load_dotenv

import search_manager
from scraper import scraper
from data_storage import MongoStorage, Movie
from poster_manager import PosterManager
from monitoring import ArchiveMonitor

def print_menu():
    """
    Display the main interactive menu options to the console.
    """
    print("\n" + "="*34)
    print("🎬 MEDIA ARCHIVE MANAGER")
    print("="*34)
    print("1. Add New Movie or TV Show (Search & Save)")
    print("2. List Saved Media")
    print("3. Export Data to JSON")
    print("4. Start Monitoring Mode")
    print("5. Exit")
    print("="*34)

def add_media_workflow(storage, poster_mgr):
    """
    Execute the workflow for adding new media:
    1. Search for the title
    2. Scrape details from URL
    3. Download poster image
    4. Save to database
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
    print(" [INIT] Scraper default values: Title='Unknown', Year='0000', Rating='N/A'")

    data = scraper.scrape_media_data(url)

    if not data:
        print("Failed to fetch data.")
        return

    print(f" Data updated: {data.title} ({data.year}) - ⭐ {data.rating}")


    if data.poster_url:
        poster_mgr.download_poster(data.poster_url, data.title)

    media_to_save = Movie(
        title=data.title,
        year=data.year,
        rating=data.rating,
        page_url=data.page_url,
        poster_url=data.poster_url
    )

    storage.save(media_to_save)

def main():
    """
    Main application loop. Initializes necessary components (Storage, PosterManager)
    and processes user input in an infinite loop.
    """
    load_dotenv()
    storage = MongoStorage()
    poster_mgr = PosterManager()

    while True:
        print_menu()
        choice = input("Your Choice (1-5): ")

        if choice == '1':
            add_media_workflow(storage, poster_mgr)

        elif choice == '2':
            storage.list_all()

        elif choice == '3':
            filename = input("Filename (default: movies.json): ").strip()
            if not filename:
                storage.export_json()
            else:
                storage.export_json(filename)

        elif choice == '4':
            print("\n Starting monitoring mode (Press CTRL+C to stop)...")
            try:
                monitor = ArchiveMonitor(interval_hours=6)
                monitor.start()
            except KeyboardInterrupt:
                print("\n Monitoring stopped.")

        elif choice == '5':
            print("Exiting...")
            sys.exit()

        else:
            print("Invalid choice, please try again.")

        time.sleep(1)

if __name__ == "__main__":
    main()
