import os
import requests
import re
from pathlib import Path


class PosterManager:
    """Handles all image downloading operations for movie posters."""
    
    def __init__(self, folder_name="posters"):
        """
        Initialize the PosterManager.
        
        Args:
            folder_name (str): Name of the folder to store posters. Default is "posters".
        """
        self.folder_name = folder_name
        self.poster_folder = Path(self.folder_name)
        
        # Create a session with retry strategy for better reliability
        self.session = requests.Session()
        self._setup_session()
        self._create_folder()
    
    def _setup_session(self):
        """Set up the requests session with proper headers and retries."""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set persistent headers for IMDB compatibility
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        })
    
    def _create_folder(self):
        """
        Automatically creates the poster folder if it doesn't exist.
        """
        try:
            self.poster_folder.mkdir(exist_ok=True)
            print(f"✓ Poster folder '{self.folder_name}/' is ready.")
        except Exception as e:
            print(f"✗ Error creating folder: {e}")
    
    def _sanitize_filename(self, title):
        """
        Sanitize the movie title to create a valid filename.
        Removes or replaces invalid characters.
        
        Args:
            title (str): The movie title to sanitize.
        
        Returns:
            str: The sanitized title suitable for a filename.
        """
        # Remove or replace invalid filename characters
        # Invalid characters: < > : " / \ | ? *
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Strip leading/trailing spaces
        sanitized = sanitized.strip()
        
        return sanitized
    
    def download_poster(self, poster_url, title):
        """
        Download a poster image from the given URL and save it locally.
        
        Workflow:
        1. Receive URL: Takes the high-quality poster URL from the Scraper.
        2. Folder Check: Ensures the posters/ folder exists.
        3. Sanitization: Cleans the movie title to create a valid filename.
        4. Download: Uses requests with iter_content() to download in chunks.
        
        Args:
            poster_url (str): The URL of the poster image to download.
            title (str): The movie title (used to create the filename).
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not poster_url:
            print(f"✗ No poster URL provided for '{title}'")
            return False
        
        try:
            # Sanitize the title to create a valid filename
            sanitized_title = self._sanitize_filename(title)
            
            if not sanitized_title:
                print(f"✗ Could not create valid filename from title: '{title}'")
                return False
            
            # Create the full file path with .jpg extension
            file_path = self.poster_folder / f"{sanitized_title}.jpg"
            
            # Check if file already exists
            if file_path.exists():
                print(f"→ Poster already exists: {file_path.name}")
                return True
            
            print(f"⬇ Downloading poster for '{title}'...")
            
            # Set dynamic headers based on source
            headers = {
                "Referer": "https://www.imdb.com/",
            }
            
            # Download the image with streaming (iter_content)
            response = self.session.get(poster_url, headers=headers, timeout=15, allow_redirects=True, stream=True)
            response.raise_for_status()
            
            # Save the image in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            
            file_size_kb = file_path.stat().st_size / 1024
            print(f"✓ Poster saved: {file_path.name} ({file_size_kb:.2f} KB)")
            return True
        
        except requests.exceptions.MissingSchema:
            print(f"✗ Invalid URL format: {poster_url}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error while downloading poster for '{title}'")
            return False
        except requests.exceptions.Timeout:
            print(f"✗ Download timeout for poster of '{title}'")
            return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Request error for '{title}': {e}")
            return False
        except IOError as e:
            print(f"✗ Error saving file for '{title}': {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error downloading poster for '{title}': {e}")
            return False
    
    def download_multiple_posters(self, media_data_list):
        """
        Download multiple posters from a list of media data.
        
        Args:
            media_data_list (list): List of dictionaries containing 'title' and 'poster_url'.
        
        Returns:
            dict: Statistics about the download process.
        """
        stats = {
            "total": len(media_data_list),
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for media_data in media_data_list:
            title = media_data.get("title", "Unknown")
            poster_url = media_data.get("poster_url")
            
            if self.download_poster(poster_url, title):
                stats["successful"] += 1
            else:
                stats["failed"] += 1
        
        return stats
    
    def get_downloaded_posters(self):
        """
        Get a list of all downloaded posters in the folder.
        
        Returns:
            list: List of filenames of downloaded posters.
        """
        if not self.poster_folder.exists():
            return []
        
        return [f.name for f in self.poster_folder.glob("*.jpg")] 