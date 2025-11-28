#playwright
from playwright.sync_api import sync_playwright


def find_link(movie_name):
    print(f"Searching for {movie_name}...")
    search_query = movie_name.replace(" ", "+")

    #start playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        #anti-bot headers
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/114.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            #navigate to the search page
            page.goto(
                f"https://www.imdb.com/find/?q={search_query}",
                wait_until="domcontentloaded",
                timeout=30000
            )
            selector = "ul.ipc-metadata-list li:first-child a"
            page.wait_for_selector(selector, timeout=20000)

            first_result = page.locator(selector).first
            href = first_result.get_attribute("href")
            
            if not href:
                print("no results.")
                return None

            clean_link = href.split("?")[0]
            final_link = "https://www.imdb.com" + clean_link
            print(f"The link is found: {final_link}")
            return final_link

        except Exception as error:
            print(f"{movie_name} not found.Error: {error}")

            try:
                print(f"Page Title: {page.title()}")
            except:
                pass
            return None
        finally:
            browser.close()
