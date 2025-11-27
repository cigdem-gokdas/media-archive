# playwright
from playwright.sync_api import sync_playwright


def find_link(movie_name):
    print(f"Searching for {movie_name}...")
    search_query = movie_name.replace(" ", "+")

    # start playwright
    with sync_playwright() as pw:

        # launch browser
        browser = pw.chromium.launch(headless=True)
        # we show that we are not bots to enter IMDB
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:

            # navigate to the search page
            page.goto(f"https://www.imdb.com/find/?q={search_query}")

            page.wait_for_selector(
                "ul.ipc-metadata-list li.find-result-item", timeout=10000)
            first_result = page.locator(
                "ul.ipc-metadata-list li.find-result-item a").first
            link_extension = first_result.get_attribute("href")
            clean_link = link_extension.split('?')[0]
            link = "https://www.imdb.com" + clean_link
            print(f"The link is found:{link}")
            return link

        except Exception as exception:
            print(f"{movie_name} not found.Error: {exception}")
            return None
