# Media Archive Manager

**Media Archive Manager** is a robust Python CLI application designed to search, scrape, archive, and monitor movie and TV series data from IMDb. It utilizes **Playwright** for dynamic content scraping, **MongoDB** for data persistence, and includes a background monitoring system to track rating changes.

**Project Purpose**

This project demonstrates a production-grade Python application with:

Advanced web scraping using modern tools
Polyglot persistence (SQL + Graph databases)
Comprehensive error handling and monitoring
Professional OOP architecture with abstract base classes
Full test coverage and CI/CD readiness

Perfect for movie enthusiasts who want to maintain a personal archive of films and series with automatic rating updates and relationship tracking.

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
**Testing:** unittest, unittest.mock

## Project Structure

* `main.py` - Entry point of the application (CLI Menu).
* `scraper.py` - Handles HTML fetching and parsing logic.
* `search_manager.py` - Manages IMDb search navigation.
* `data_storage.py` - MongoDB connection and CRUD operations.
* `poster_manager.py` - Handles downloading and saving images.
* `monitoring.py` - Background process for updating ratings.
* `business_logic_and_oop.py` - Data classes and interface definitions.
* `falkor.py` - Manages Graph Database connections and Cypher queries.
* `tests.py` - Comprehensive Unit & Integration tests for code robustness.
* `requirements.txt` - Lists all Python dependencies required to run the project.
* `.env.example` - Template file for environment variables configuration.
* `README.md` - Project documentation and setup guide.


## Installation

**Prerequisites**

Python 3.13+
MongoDB (Local or Cloud Atlas)
Docker (optional, for FalkorDB)

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
5.  **Configure Environment Variables:**
    Create a `.env` file from the example template to store your configuration:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and configure your MongoDB connection string:
    ```ini
    # For Local MongoDB (Default)
    MONGO_URI="mongodb://localhost:27017/"

    # OR for MongoDB Atlas (Cloud)
    # MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
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

## 🕹️ Usage

Run the main application:
python main.py


### Main Menu Options
================================== 🎬 MEDIA ARCHIVE MANAGER
Add New Movie or TV Show

List Saved Media (w/ Status)

Export Data to JSON

Update Watch Status (✅/📅/▶️)

Start Monitoring Mode

Exit ==================================


## 💡 Use Cases

### Case 1: Adding a Movie
Search for a title, scrape data, select type, and save to database.
Your Choice (1-6): 1 Enter movie/series name to search: Inception 🌍 Link found: https://www.imdb.com/title/tt1375666/ 📥 Fetching data... ✔ Data found: Inception (2010) - ⭐ 8.8

Is this a Movie or a TV Series?

Movie 🎬

TV Series 📺 Select (1/2): 1 Watched? (y/n): y 🖼 Downloading poster... 💾 'Inception' saved successfully. 🕸️ Synced to FalkorDB Graph: Inception


### Case 2: Monitoring Ratings
The system checks for rating changes in the background.
Your Choice (1-6): 5 📡 Starting monitoring mode (Press CTRL+C to stop)...

[2024-01-15 10:30:45] Starting Update Check... Checking: Inception... No changes. (8.8) Checking: Breaking Bad... UPDATE DETECTED: 9.4 -> 9.5 Database updated.


### Case 3: Exporting Your Archive
Your Choice (1-6): 3 Filename (movies.json): my_collection.json ✅ Exported to my_collection.json successfully.

### Case 4: Updating Watch Status
Change the status of a saved item (e.g., from "Not Watched" to "Watched").
Your Choice (1-6): 4

🔍 Update Mode Initialized... Enter name to update (or partial name): matrix

Found 1 matches:

The Matrix (1999) Select number: 1

Selected: The Matrix Current Status: NOT WATCHED

Set New Status:

Watched (✅)

Not Watched (📅) Choice: 1 ✔ Updated 'The Matrix' to: WATCHED


### Case 5: Monitoring Mode (Background Task)
The system periodically checks IMDb for rating changes.
Your Choice (1-6): 5 📡 Starting monitoring mode (Press CTRL+C to stop)...

[2024-01-15 10:30:45] Starting Update Check... Checking: Inception... No changes. (8.8) Checking: Breaking Bad... UPDATE DETECTED: 9.4 -> 9.5 Database updated.


### Case 6: Exiting
Your Choice (1-6): 6 Exiting...