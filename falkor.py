"""
Module for handling FalkorDB (Graph Database) operations.
This acts as a bonus feature to store movie relationships alongside MongoDB.
"""
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()


class FalkorManager:
    """
    Manages the connection to the FalkorDB graph database.
    It includes error handling to ensure the app runs even if the
    graph database (Docker) is offline.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialize connection settings."""
        self.host = "localhost"
        self.port = 6379
        self.client = None
        self.graph = None
        self.is_active = False

        self._connect()

    def _connect(self):
        """Attempts to connect to the FalkorDB Docker container."""
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            # Create or select a graph named 'IMDB_Graph'
            self.graph = self.client.select_graph("IMDB_Graph")
            self.is_active = True
            print("✔ Connected to FalkorDB (Graph Mode Active)")
        # pylint: disable=broad-exception-caught
        except Exception:
            # If Docker is not running, just print a message and continue
            print("⚠ FalkorDB not detected. Running in MongoDB-only mode.")
            self.is_active = False

    def save_media(self, media_item):
        """
        Saves a media item (Movie or Series) as a node in the graph.
        Uses Cypher Query Language (CQL).
        """
        if not self.is_active:
            return

        try:
            # Simple sanitization to prevent query errors with apostrophes
            title = media_item.title.replace("'", "\\'")
            year = media_item.year
            rating = media_item.rating
            m_type = "Movie" if media_item.media_type == "movie" else "Series"
            status = media_item.status

            # MERGE creates the node if it doesn't exist, or matches it if it does.
            query = f"""
            MERGE (m:{m_type} {{title: '{title}'}})
            SET m.year = '{year}',
                m.rating = '{rating}',
                m.status = '{status}',
                m.poster = '{media_item.poster_url}'
            RETURN m
            """

            self.graph.query(query)
            print(f"🕸 Synced to FalkorDB Graph: {title}")

        # pylint: disable=broad-exception-caught
        except Exception as error:
            print(f" FalkorDB Error: {error}")


# Create a global instance to be used in main.py
falkor_db = FalkorManager()
