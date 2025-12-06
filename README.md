# Media Archive Manager

**Media Archive Manager** is a robust Python CLI application designed to search, scrape, archive, and monitor movie and TV series data from IMDb. It utilizes **Playwright** for dynamic content scraping, **MongoDB** for data persistence, and includes a background monitoring system to track rating changes.

## Features

* **Smart Search:** Search for movies or series directly via the CLI; automatically finds the correct IMDb page.
* **Dynamic Scraping:** Extracts detailed information (Title, Year, Rating, Poster) using `Playwright` and `BeautifulSoup`, handling dynamic JavaScript content effectively.
* **Database Integration:** Stores metadata in a **MongoDB** database (supports both Local and Cloud/Atlas connections).
* **Poster Downloader:** Automatically downloads and saves high-resolution movie posters locally.
* **Live Monitoring:** A background service that periodically checks archived media for rating updates and keeps the database synchronized.
* **Data Export:** Export your entire collection to a JSON file for backup or external use.
* **Status Tracking:** Mark movies and series as 'Watched' (✅) or 'Not Watched' (📅) directly from the CLI to keep track of your viewing progress.
* **Graph Database Support (Bonus):** Implements **FalkorDB** alongside MongoDB, demonstrating a **Polyglot Persistence** architecture to model data relationships using a Graph structure.
* **Fault Tolerant Architecture:** The system uses a fail-safe mechanism; if FalkorDB (Docker) is not running, it automatically degrades to MongoDB-only mode without crashing.

## Tech Stack

* **Language:** Python 3.13.3
* **Web Scraping:** Playwright, BeautifulSoup4
* **Database:** MongoDB (PyMongo)
* **Network:** Requests (for image downloads)
* **Configuration:** Python-dotenv
* **Graph Database:** FalkorDB (Redis-based Graph DB)
* **Containerization:** Docker (for running FalkorDB)

## Project Structure

* `main.py` - Entry point of the application (CLI Menu).
* `scraper.py` - Handles HTML fetching and parsing logic.
* `search_manager.py` - Manages IMDb search navigation.
* `data_storage.py` - MongoDB connection and CRUD operations.
* `poster_manager.py` - Handles downloading and saving images.
* `monitoring.py` - Background process for updating ratings.
* `business_logic_and_oop.py` - Data classes and interface definitions.
* `falkor.py` - Manages Graph Database connections and Cypher queries.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/media-archive-manager.git](https://github.com/yourusername/media-archive-manager.git)
    cd media-archive-manager
    ```

2.  **Create a Virtual Environment (Optional but recommended):**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browsers:**
    Since the scraper uses a headless Chromium browser, you need to install the binaries:
    ```bash
    playwright install chromium
    ```

## Configuration

1.  Rename the example environment file:
    ```bash
    mv .env.example .env
    ```
2.  Open `.env` and configure your MongoDB connection string:
    ```ini
    MONGO_URI="mongodb://localhost:27017/" 
    # Or your MongoDB Atlas connection string
    ```

## How to Enable Graph Database (Bonus Feature)

To unlock the **FalkorDB ** features, you need **Docker**. The system is designed to check for this container at startup.

1.  **Run the FalkorDB Container:**
    ```bash
    docker run -p 6379:6379 -it --rm falkordb/falkordb
    ```

2.  **Start the Application:**
    Open a new terminal and run:
    ```bash
    python main.py
    ```

3.  **Verification:**
    You will see `✔ Connected to FalkorDB (Graph Mode Active)` in the startup logs. When you add a movie, it will be synced to the Graph automatically.

## Usage

Run the main application:

```bash
python main.py