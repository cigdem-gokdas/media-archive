# 🎬 Media Archive Manager

**Media Archive Manager** is a production-grade Python CLI application for searching, scraping, and archiving movie and TV series data from IMDb. It features automatic rating monitoring and graph-based relationship visualization.

Perfect for movie enthusiasts maintaining a personal archive with automatic updates and visual analytics.

## 🌟 Features

* **Smart Search:** Automated IMDb page discovery via CLI.
* **Dynamic Scraping:** Extracts **title, year, rating, and posters** from JavaScript-heavy pages using Playwright.
* **Polyglot Persistence:** Dual database architecture: **MongoDB** for primary persistence and **FalkorDB (Graph DB)** for relationship graphs.
* **Poster Management:** Automatic high-resolution download with retry logic.
* **Live Monitoring:** Background service tracks rating changes every **6 hours**.
* **Status Tracking:** Mark items as `Watched` / `Not Watched` / `Watching`.
* **Graph Visualization:** Interactive PNG diagrams showing media relationships using NetworkX.
* **Data Export:** JSON export for backup and external use.
* **Fault Tolerance:** Automatic fallback to MongoDB if FalkorDB is unavailable.

---

## 🏗️ Project Purpose & Professional Practices

This project demonstrates several advanced professional software engineering practices:

* **Advanced Web Scraping:** Dynamic content extraction using **Playwright** and **BeautifulSoup4**.
* **Polyglot Persistence:** Dual database architecture (MongoDB + FalkorDB) for flexible data modeling.
* **OOP Architecture:** Abstract base classes, inheritance, and comprehensive **type hints**.
* **Error Handling:** Graceful degradation with fault tolerance and retry logic.
* **Testing:** **28+ unit tests** with 100% pylint compliance.
* **Graph Visualization:** NetworkX-based relationship mapping and interactive network diagrams.

## ⚙️ Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.13.3 | Core application language |
| **Web Scraping** | Playwright, BeautifulSoup4 | Dynamic content extraction |
| **Databases** | MongoDB (PyMongo), FalkorDB (Graph DB) | Primary persistence & Relationship modeling |
| **Visualization** | NetworkX, Matplotlib | Graph visualization engine |
| **Testing** | unittest, unittest.mock | Unit testing and mocking |
| **Containerization** | Docker | Running FalkorDB |
| **Code Quality** | pylint | Code static analysis |

---

## 🚀 Installation & Setup

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
📋 Menu Options
Option	Description
1.	Add New Movie or TV Show (Triggers scraping & DB storage)
2.	List Saved Media (w/ Status)
3.	Export Data to JSON
4.	Update Watch Status (✅/📁/▶)
5.	Start Monitoring Mode (Background rating checks)
6.	Visualize Graph (Generate project_graph_visualization.png)
7.	Sync MongoDB → FalkorDB (Populate graph database)
8.	Exit

💡 Use Cases
Case	Steps	Outcome
1: Add & Archive	Menu 1 → Search "Inception" → Mark as watched	Saved to MongoDB + FalkorDB, Poster downloaded.
2: Track Changes	Menu 5 → Monitoring starts	Checks rating every 6 hours, updates DB, and alerts on change.
3: View Archive Graph	Menu 7 → Menu 6	Generates project_graph_visualization.png showing nodes (movies) and edges (relationships).
4: Export Collection	Menu 3 → Enter filename	JSON file created for backup or external integration.
5: Update Status	Menu 4 → Search for movie → Change status	Database status updated immediately.

⚠️ Known Issues & Troubleshooting
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
# Add movies (Menu 1), Sync to FalkorDB (Menu 7), Visualize (Menu 6)
📂 Project Structure
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

⏱️ Performance Metrics
Movie search: 3-5 seconds

Poster download: 1-2 seconds

Database query: <100ms

Graph generation: 1-5 seconds

Full sync (10 movies): 30-45 seconds

📐 Architecture Highlights
Polyglot Persistence
MongoDB: Primary persistence for all media item metadata (Title, Year, Rating, Poster URL, etc.).

FalkorDB: Secondary database specifically for modeling and visualizing media relationships (e.g., actor/director connections, genre links).

Automatic fallback if FalkorDB is unreachable.

OOP Design
Abstract base classes: StorageBase, MonitorBase, MediaItem.

Concrete implementations: MongoStorage, ArchiveMonitor, Movie, Series.

Extensive use of type hints and dataclasses for robust code.

Error Handling
Strict use of try-except blocks with specific exception types.

Graceful degradation allows the application to continue using MongoDB even if the FalkorDB connection fails.

Retry logic built into network requests (e.g., poster download).

✅ Testing & Quality
Run Tests
Bash

# Run all tests
python3 tests.py

# Check code quality
pylint *.py  # Expected: 10.00/10
Coverage Includes:
OOP model validation

Database CRUD operations

Input sanitization

Network error handling

Edge case scenarios

🤝 Contributing
Suggestions for improvement are welcome!

Batch import from CSV/XLSX

Advanced filtering and search

Email notifications for rating changes

Web UI alternative

IMDb list import feature

📄 License
This project is open source for educational purposes.


Would you like a brief explanation of any of the technologies used, like **FalkorDB** or **Playwright**?