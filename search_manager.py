from playwright.sync_api import sync_playwright

def find_link(movie_name):
    print(f"Searching for {movie_name}...")
    query = movie_name.replace(" ", "+")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            page.goto(f"https://www.imdb.com/find/?q={query}", timeout=30000)

            # SADECE "Titles" sonuçlarını al
            selector = "section[data-testid='find-results-section-title'] li a"

            page.wait_for_selector(selector, timeout=10000)

            first_result = page.locator(selector).first
            href = first_result.get_attribute("href")

            if href and "/title/" in href:
                final = "https://www.imdb.com" + href.split("?")[0]
                print("The link is found:", final)
                return final

            print("No valid title result found.")
            return None

        except Exception as e:
            print("Error:", e)
            return None

        finally:
            browser.close()