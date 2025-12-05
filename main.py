from scraper import scrape_media_data
from poster_manager import download_poster
import os


def remove_unwanted_posters(valid_titles, folder="posters"):
    # Remove poster files that are not in valid_titles set
    if not os.path.isdir(folder):
        return
    for fname in os.listdir(folder):
        if not fname.lower().endswith('.jpg'):
            continue
        stem = os.path.splitext(fname)[0]
        if stem not in valid_titles:
            path = os.path.join(folder, fname)
            try:
                os.remove(path)
                print(f"Removed unwanted poster: {fname}")
            except Exception as e:
                print(f"Failed to remove {fname}: {e}")


def run_urls(urls):
    saved_titles = set()
    for url in urls:
        print(f"--- RUNNING SCRAPER for {url} ---")
        datos = scrape_media_data(url)
        if datos:
            title = datos.get('title')
            poster_url = datos.get('poster_url')
            print("\n--- DATA FOUND ---")
            print(f"Title: {title}")
            print(f"Poster URL: {poster_url}")

            if title and title != 'Unknown' and poster_url:
                download_poster(poster_url, movie_title=title)
                # store sanitized form the downloader uses
                from poster_manager import _sanitize_filename
                saved_titles.add(_sanitize_filename(title))
            else:
                # If no valid title, try to remove any file that was saved from that URL
                if poster_url:
                    file_name = poster_url.split("/")[-1].split("?")[0]
                    file_path = os.path.join('posters', file_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"Removed poster with no title: {file_name}")
                        except Exception as e:
                            print(f"Failed to remove {file_name}: {e}")
        else:
            print("Scraper failed to find data.")

    # Clean up any remaining posters that are not saved_titles
    remove_unwanted_posters(saved_titles)


if __name__ == '__main__':
    # Add more IMDb URLs here
    urls = [
        "https://www.imdb.com/title/tt0172495/",  # Gladiator
        "https://www.imdb.com/title/tt0111161/",  # The Shawshank Redemption
        "https://www.imdb.com/title/tt0468569/",  # The Dark Knight
    ]
    run_urls(urls)
