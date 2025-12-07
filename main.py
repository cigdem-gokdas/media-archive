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
import visualize_falkor_graph
from scraper import scraper
from data_storage import MongoStorage
from data_storage import Movie as StorageMovie
from poster_manager import PosterManager
from monitoring import ArchiveMonitor
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
    print("6. Visualize Graph (FalkorDB)")
    print("7. Sync MongoDB → FalkorDB")
    print("8. Exit")
    print("="*34)


def add_media_workflow(storage, poster_mgr):
    """
    Execute the workflow for adding new media.
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

    # Download poster
    if data.poster_url:
        print(" Downloading poster...")
        poster_mgr.download_poster(data.poster_url, data.title)

    storage_movie = StorageMovie(
        title=media_obj.title,
        year=media_obj.year,
        rating=media_obj.rating,
        page_url=media_obj.page_url,
        poster_url=media_obj.poster_url,
        last_updated=None
    )
    storage.save(storage_movie)

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
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(
                f"Error displaying item: {record.get('title', 'Unknown')} - {e}")


# pylint: disable=too-many-branches
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


def visualize_graph_workflow():
    """
    Generate and display graph visualization from FalkorDB.
    """
    print("\n📊 Generating graph visualization...")

    try:
        visualize_falkor_graph.visualize_graph_data()
        print("✓ Graph visualization saved to 'project_graph_visualization.png'")
    except ConnectionError:
        print("FalkorDB is not running!")
        print("\nTo use graph visualization:")
        print("1. Start Docker container:")
        print("docker run -p 6379:6379 falkordb/falkordb")
        print("2. Run this option again")
    except FileNotFoundError:
        print("Required visualization libraries not found")
        print("Install with: pip install matplotlib networkx")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error generating visualization: {e}")


def sync_to_falkor_workflow(storage):
    """
    Manually sync existing movies from MongoDB to FalkorDB.
    Useful when FalkorDB wasn't running during initial data entry.
    """
    if storage.collection is None:
        print("No database connection.")
        return

    print("\n📊 Syncing movies to FalkorDB...")

    # Check if FalkorDB is active
    if not falkor_db.is_active:
        print("FalkorDB is not running!")
        print("\nTo enable FalkorDB:")
        print("1. Start Docker container:")
        print("   docker run -p 6379:6379 falkordb/falkordb")
        print("2. Run this option again")
        return

    # Fetch all movies from MongoDB
    records = list(storage.collection.find({}, {"_id": 0}))

    if not records:
        print("No movies to sync.")
        return

    print(f"Found {len(records)} movies in MongoDB")

    synced = 0
    failed = 0

    for record in records:
        try:
            m_type = record.get("media_type", "movie")

            params = {
                "title": record.get("title"),
                "year": record.get("year"),
                "rating": record.get("rating"),
                "poster_url": record.get("poster_url"),
                "page_url": record.get("page_url"),
                "status": record.get("status", "not watched")
            }

            if m_type == "series":
                media_obj = Series(**params)
            else:
                media_obj = Movie(**params)

            # Save to FalkorDB
            falkor_db.save_media(media_obj)
            synced += 1
            print(f"✓ Synced: {record.get('title')}")

        except Exception as e:  # pylint: disable=broad-exception-caught
            failed += 1
            print(f"⚠️  Failed to sync {record.get('title')}: {e}")

    print("\n✓ Sync Complete!")
    print(f"  Synced: {synced}")
    print(f"  Failed: {failed}")


# pylint: disable=too-many-branches
def main():
    """Main Loop"""
    load_dotenv()
    storage = MongoStorage()
    poster_mgr = PosterManager()

    while True:
        print_menu()
        choice = input("Your Choice (1-8): ").strip()

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
            visualize_graph_workflow()
        elif choice == '7':
            sync_to_falkor_workflow(storage)
        elif choice == '8':
            print("Exiting...")
            sys.exit()
        else:
            print(" Invalid choice, please try 1-8.")

        time.sleep(1)


if __name__ == "__main__":
    main()
