# playwright ve bs4
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_media_data(url):
    print(f"Navigating to: {url}")

    data = {}

    with sync_playwright() as pw:

        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, wait_until="networkidle")
        page.wait_for_load_state("domcontentloaded")

        html_content = page.content()

        browser.close()
    # For finding specific data.
    soup = BeautifulSoup(html_content, "html.parser")
    # Find title of movie
    try:
        data["title"] = soup.find("h1").text.strip()
    except:
        data["title"] = "Unknown title."
    # Find year of movie
    try:
        year_element = soup.select_one(
            "ul.ipc-inline-list li a[href*='releaseinfo']")
        if year_element:
            data["year"] = year_element.text.strip()
        else:
            data["year"] = "0000"
    except:
        data["year"] = "0000"
    # Find rating N/A of movie
    try:
        rating_element = soup.select_one("span.sc-bde20123-1.iZlgcd")
        if not rating_element:
            rating_element = soup.find(
                "span", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        data["rating"] = rating_element.text.strip() if rating_element else "N/A"
    except:
        data["rating"] = "N/A"
    # Find poster of movie
    try:
        poster_div = soup.find("div", class_="ipc-poster")
        data["poster_url"] = poster_div.find("img")["src"]
    except:
        data["poster_url"] = None

    data["page_url"] = url

    return data
