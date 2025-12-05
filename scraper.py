# playwright ve bs4
from dataclasses import dataclass
from typing import Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json


@dataclass
class MovieData:
    title: str
    year: str
    rating: str
    poster_url: Optional[str]
    page_url: str


class IMDBScraper:

    def scrape_media_data(self, url: str) -> Optional[MovieData]:
        print(f"Navigating to: {url}")

        html_content = self._fetch_html(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        return self._parse_data(soup, url)

    def _fetch_html(self, url: str) -> Optional[str]:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                return page.content()

            except Exception as exception:
                print(f"Error: {exception}")
                return None
            finally:
                browser.close()

    def _parse_data(self, soup: BeautifulSoup, url: str) -> MovieData:
        title = "Unknown"
        year = "0000"
        rating = "N/A"
        poster_url = None

        json_ld_tag = soup.find("script", type="application/ld+json")
        if json_ld_tag:
            try:
                data = json.loads(json_ld_tag.string)
                title = soup.find("h1").text.strip(
                ) if soup.find("h1") else "Unknown"
                poster_url = data.get("image")

                if "aggregateRating" in data:
                    rating = str(data["aggregateRating"].get(
                        "ratingValue", "N/A"))

                year = data.get("datePublished", "0000")[:4]
            except:
                pass

        if title == "Unknown":
            try:
                title = soup.find("h1").text.strip()
            except:
                pass

        if rating == "N/A":
            try:
                box = soup.find(
                    "div", attrs={"data-testid": "hero-rating-bar__aggregate-rating__score"})
                if box:
                    rating = box.find("span").text.strip()
            except:
                pass

        if poster_url and "._V1_" in poster_url:
            poster_url = poster_url.split("._V1_")[0] + "._V1_.jpg"

        return MovieData(title=title, year=year, rating=rating, poster_url=poster_url, page_url=url)


scraper = IMDBScraper()
