import os
import requests

def download_poster(url, folder="posters/", movie_title=None):
    # If URL is empty, stop
    if not url:
        print("No poster URL found.")
        return

    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    try:
        print(f"Downloading image: {url}")
        # Request the image from internet
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            # Use movie title if provided, otherwise use URL-based filename
            if movie_title:
                file_name = f"{movie_title}.jpg"
            else:
                file_name = url.split("/")[-1].split("?")[0]
                # Ensure it ends with .jpg
                if not file_name.endswith(".jpg"):
                    file_name += ".jpg"
            
            full_path = os.path.join(folder, file_name)

            # Save to hard drive
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            print(f"SUCCESS! Image saved at: {full_path}")
        else:
            print("Error: Website refused the download.")

    except Exception as e:
        print(f"Unexpected Error: {e}")
