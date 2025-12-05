from playwright.sync_api import sync_playwright
import json 

def find_link(movie_name):
    # Inform the user about the search
    print(f"Searching for {movie_name}...")
    query = movie_name.replace(" ", "+")

   # Default result structure (JSON format) to be returned
    result = {
        "search_term": movie_name,
        "url": None,
        "status": "failed",
        "error": None
    }

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
            # Navigate to the IMDb search page
            page.goto(f"https://www.imdb.com/find/?q={query}", timeout=30000)

            # Target only the "Titles" section in the search results
            selector = "section[data-testid='find-results-section-title'] li a"

            page.wait_for_selector(selector, timeout=10000)

            first_result = page.locator(selector).first
            href = first_result.get_attribute("href")
           
            # Check if a valid link was found
            if href and "/title/" in href:
                final = "https://www.imdb.com" + href.split("?")[0]
                print("The link is found:", final)
                
                
                result["url"] = final
                result["status"] = "success"
                return result

            print("No valid title result found.")
            result["error"] = "No valid title found"
            return result

        except Exception as e:
            print("Error:", e)
            result["error"] = str(e)
            return result

        finally:
            browser.close()