from playwright.sync_api import sync_playwright
import time
from urllib.parse import quote_plus
import os
import requests
import tempfile
from urllib.parse import urlparse
from datetime import datetime
import re

class GoogleImageFinder:
    def __init__(self, browser=None):
        self._browser = browser
        self.page = None
        self._owns_browser = browser is None
        
    def start(self):
        """Initialize the browser"""
        if self._owns_browser:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=False)
        self.page = self._browser.new_page()
        
    def close(self):
        """Clean up resources"""
        if self.page:
            self.page.close()
        # Only close browser if we created it
        if self._owns_browser:
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

    def download_images_for_thread(self, queries, thread_id=None, output_dir="thread_images"):
        thread_id = thread_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        thread_dir = os.path.join(output_dir, f"thread_{thread_id}")
        os.makedirs(thread_dir, exist_ok=True)
        
        local_paths = [None] * len(queries)  # Initialize with None placeholders
        
        for i, query in enumerate(queries):
            print(f"Searching for image {i+1}/{len(queries)}: {query}")
            url = self.search_image(query)
            
            if url and not url.startswith('data:'):
                ext = '.jpg'
                if url.lower().endswith(('.png', '.gif', '.webp')):
                    ext = os.path.splitext(url)[1]
                filename = f"tweet_{i}{ext}"
                filepath = os.path.join(thread_dir, filename)
                
                downloaded_path = self._download_image(url)
                if downloaded_path:
                    os.replace(downloaded_path, filepath)
                    local_paths[i] = filepath
                    print(f"✓ Downloaded image {i+1}")
                else:
                    print(f"✗ Failed to download image {i+1}")
            else:
                print(f"✗ No valid image URL found for tweet {i+1}")
            
            time.sleep(2)
        
        # Remove None values while maintaining order
        return [path for path in local_paths if path is not None]

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

    def download_single_image(self, url, filename_base, output_dir="thread_images"):
        """Download a single image from a direct URL"""
        try:
            ext = '.jpg'
            if url.lower().endswith(('.png', '.gif', '.webp')):
                ext = os.path.splitext(url)[1]
            
            filename = f"{filename_base}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            downloaded_path = self._download_image(url)
            if downloaded_path:
                os.replace(downloaded_path, filepath)
                return filepath
            
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