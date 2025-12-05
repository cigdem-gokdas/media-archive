from scraper import scrape_media_data
from poster_manager import download_poster

# Test URL (Gladiator movie)
url = "https://www.imdb.com/title/tt0172495/"

print("--- 1. RUNNING SCRAPER ---")
datos = scrape_media_data(url)

if datos:
    print("\n--- DATA FOUND ---")
    print(f"Title: {datos.get('title')}")
    print(f"Poster URL: {datos.get('poster_url')}")
    
    print("\n--- 2. DOWNLOADING POSTER ---")
    download_poster(datos.get('poster_url'), movie_title=datos.get('title'))
else:
    print("Scraper failed to find data.")
