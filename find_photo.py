from playwright.sync_api import sync_playwright
import time
from urllib.parse import quote_plus
import os
import requests
import tempfile
from urllib.parse import urlparse

class GoogleImageFinder:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self.page = None
        
    def start(self):
        """Initialize the browser"""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        self.page = self._browser.new_page()
        
    def close(self):
        """Clean up resources"""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
            
    def search_image(self, query):
        """Search for an image and return its URL"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            
            self.page.goto(url, wait_until='networkidle')
            self.page.wait_for_selector('.H8Rx8c', timeout=10000)
            
            first_image = self.page.locator('.H8Rx8c img').first
            first_image.click()
            time.sleep(2)
            
            image_url = first_image.get_attribute('src')
            
            if image_url and image_url.startswith('data:'):
                full_image = self.page.locator('img[class*="iPVvYb"]').first
                actual_url = full_image.get_attribute('src')
                if actual_url:
                    image_url = actual_url
                    
            return image_url
            
        except Exception as e:
            print(f"Error searching for image: {e}")
            return None 

    def download_images_for_thread(self, queries, output_dir="thread_images"):
        """
        Search for images and download them to a local folder with ordered names.
        Returns a list of local file paths to the downloaded images.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        local_paths = []
        for i, query in enumerate(queries, 1):
            print(f"Searching for: {query}")
            url = self.search_image(query)
            if url:
                # Generate filename based on order
                ext = '.jpg'  # Default extension
                if url.lower().endswith(('.png', '.gif', '.webp')):
                    ext = os.path.splitext(url)[1]
                filename = f"tweet_{i}{ext}"
                filepath = os.path.join(output_dir, filename)
                
                # Download the image
                if url.startswith('data:'):
                    print(f"Skipping data URL for query: {query}")
                    continue
                    
                downloaded_path = self._download_image(url)
                if downloaded_path:
                    # Move the temp file to our desired location
                    os.replace(downloaded_path, filepath)
                    local_paths.append(filepath)
                    print(f"Downloaded image to: {filepath}")
                
            time.sleep(2)  # Delay between searches
        
        return local_paths 

    def _download_image(self, url):
        """Download image from URL to a temporary file with proper headers."""
        try:
            # Set up headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Make request with headers and timeout
            response = requests.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            
            # Map content types to extensions
            extensions = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            content_type = response.headers.get('content-type', '').lower()
            ext = extensions.get(content_type, '.jpg')
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            
            # Download in chunks
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
def main():
    finder = GoogleImageFinder()
    finder.start()
    
    # Example queries
    queries = [
        "UFC gloves evolution history",
        "Art Jimmerson one glove UFC 1",
        "Modern UFC gloves"
    ]
    
    try:
        # Download images and get local paths
        local_paths = finder.download_images_for_thread(queries)
        print("\nDownloaded images:")
        for i, path in enumerate(local_paths, 1):
            print(f"{i}. {path}")
    finally:
        finder.close() 

if __name__ == "__main__":
    main()