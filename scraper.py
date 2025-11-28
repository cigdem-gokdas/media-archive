# playwright ve bs4
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_media_data(url):
    print(f"Navigating to: {url}")

    data = {}

    with sync_playwright() as pw:

        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            html_content = page.content()

        except Exception as exception:
            print(f"Error: {exception}")
            browser.close()
            return None

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
        rating_element = soup.find(
            "div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        if rating_element:
            data["rating"] = rating_element.find("span").text.strip()
        else:
            data["rating"] = "N/A"
    except:
        data["rating"] = "N/A"

    # Find poster of movie
   # try:
    #    poster_div = soup.find("div", class_="ipc-poster")
    #   data["poster_url"] = poster_div.find("img")["src"]
   # except:
    #    data["poster_url"] = None

    data["page_url"] = url

    return data
