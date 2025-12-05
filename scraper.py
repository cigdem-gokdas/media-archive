# Simple web scraping with requests
from bs4 import BeautifulSoup
import requests
import json


def scrape_media_data(url):
    print(f"Navigating to: {url}")

    data = {}

    try:
        # Make HTTP request with user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        html_content = response.text

    except Exception as exception:
        print(f"Error: {exception}")
        return None

    # For finding specific data.
    soup = BeautifulSoup(html_content, "html.parser")

    json_ld_tag = soup.find("script", type="application/ld+json")

    if json_ld_tag:
        try:
            imdb_data = json.loads(json_ld_tag.string)
            # Title
            data["title"] = soup.find("h1").text.strip()

            # Poster
            data["poster_url"] = imdb_data.get("image", None)

            # Puan
            if "aggregateRating" in imdb_data:
                data["rating"] = str(
                    imdb_data["aggregateRating"].get("ratingValue", "N/A"))
            else:
                data["rating"] = "N/A"

            # Year
            if "datePublished" in imdb_data:
                data["year"] = imdb_data["datePublished"][:4]
            else:
                data["year"] = "0000"

            print("Data was pulled from JSON.")

        except:
            print("JSON")
            data = scrape_from_html(soup)

        if data.get("poster_url") and "._V1_" in data["poster_url"]:
            clean_url = data["poster_url"].split("._V1_")[0] + "._V1_.jpg"
            data["poster_url"] = clean_url

        data["page_url"] = url
        return data

    def scrape_from_html(soup):
        backup_data = {}

        # Find title of movie
        try:
            backup_data["title"] = soup.find("h1").text.strip()
        except:
            backup_data["title"] = "Unknown"

        # Find year of movie
        try:
            year_link = soup.select_one("a[href*='releaseinfo']")
            if year_link:
                backup_data["year"] = year_link.text.strip()
            else:
                items = soup.select("ul.ipc-inline-list li")
                backup_data["year"] = items[0].text.strip(
                ) if items else "0000"
        except:
            backup_data["year"] = "0000"

        # Find rating N/A of movie
        try:
            rating_box = soup.find(
                "div", attrs={"data-testid": "hero-rating-bar__aggregate-rating__score"})
            if rating_box:
                backup_data["rating"] = rating_box.find("span").text.strip()
            else:
                backup_data["rating"] = "N/A"
        except:
            backup_data["rating"] = "N/A"

        # Find poster of movie
        try:
            poster_div = soup.find("div", class_="ipc-poster")
            backup_data["poster_url"] = poster_div.find("img")["src"]
        except:
            backup_data["poster_url"] = None

        return backup_data
