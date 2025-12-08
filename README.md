# Media Archive Manager

**Media Archive Manager** is a Python application for searching, scraping, and archiving movie and TV series data from IMDb. It features automatic rating monitoring and graph-based relationship visualization. 


## Technologies used


**Language**  Python 3.13.3
**Web Scraping**  Playwright, BeautifulSoup4 
**Databases**  MongoDB (PyMongo), FalkorDB (Graph DB) 
**Visualization** NetworkX, Matplotlib 
**Testing**  unittest, unittest.mock 
**Containerization**  Docker 
**Code Quality**  pylint 

## Installation & Setup

### Prerequisites

* Python 3.13+
* MongoDB (local instance or Atlas cloud)
* Docker (optional, but required for graph visualization using FalkorDB)

### Setup Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/media-archive-manager.git](https://github.com/yourusername/media-archive-manager.git)
    cd media-archive-manager
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate      # Windows
    ```

3.  **Install dependencies and Playwright browser:**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

4.  **Configure environment variables:**
    ```bash
    cp .env.example .env
    # IMPORTANT: Edit the .env file with your MongoDB URI
    ```

### How to Run

To start the application and access the main menu:

```bash
python3 main.py
Menu Options
Option	Description
1.	Add New Movie or TV Show 
2.	List Saved Media
3.	Export Data to JSON
4.	Update Watch Status 
5.	Start Monitoring Mode 
6.	Visualize Graph 
7.	Sync MongoDB → FalkorDB 
8.	Exit

Use Cases
Case	Steps	Outcome
1: Add & Archive	Menu 1 → Search "Inception" → Mark as watched	Saved to MongoDB + FalkorDB, Poster downloaded.
2: Track Changes	Menu 5 → Monitoring starts	Checks rating every 6 hours, updates DB, and alerts on change.
3: View Archive Graph	Menu 7 → Menu 6	Generates project_graph_visualization.png showing nodes (movies) and edges (relationships).
4: Export Collection	Menu 3 → Enter filename	JSON file created for backup or external integration.
5: Update Status	Menu 4 → Search for movie → Change status	Database status updated immediately.

Known Issues & Troubleshooting
Issue	Cause	Solution
Graph shows only 2 nodes	Movies not synchronized to FalkorDB.	1. Verify Docker is running (docker ps). 2. Use Menu 7 to Sync MongoDB → FalkorDB.
"FalkorDB is not running"	Docker container not started.	In Terminal 1, run: docker run -p 6379:6379 -it --rm falkordb/falkordb
Graph visualization slow	Large dataset (50+ items).	Normal behavior. Average time is 2-10 seconds.
Movies missing from graph	Incomplete scraping or network error.	1. Check MongoDB data: mongosh → db.movies.find(). 2. Re-add incomplete entries.

Optional: Full Docker + FalkorDB Setup
For complete graph database features, run the following in two separate terminals:

Terminal 1: Start FalkorDB

Bash

docker run -p 6379:6379 -it --rm falkordb/falkordb
Terminal 2: Run Application

Bash

python3 main.py
Project Structure
File	Purpose
main.py	CLI menu and workflow orchestration
scraper.py	IMDb HTML fetching and parsing
search_manager.py	IMDb search automation
data_storage.py	MongoDB CRUD operations
falkor.py	FalkorDB graph management with relationships
poster_manager.py	Image download with retry logic
monitoring.py	Background rating update checks
business_logic_and_oop.py	OOP models (Movie, Series, Abstract classes)
visualize_falkor_graph.py	Graph visualization engine
tests.py	28+ unit tests
