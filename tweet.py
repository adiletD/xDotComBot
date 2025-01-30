from playwright.sync_api import sync_playwright
import time
import random
import os
import tempfile
import requests
from urllib.parse import urlparse
from pathlib import Path
from find_photo import GoogleImageFinder
from datetime import datetime
import sys
# from thread_manager import ThreadManager

class XAutomation:
    def __init__(self, user_data_dir="./chrome-data"):
        self.playwright = None
        self.browser = None
        self.page = None
        self.user_data_dir = user_data_dir

    def start(self):
        """Initialize the browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False
        )
        self.page = self.browser.new_page()
        self.page.goto('https://twitter.com/home')
        time.sleep(2)

    def post_tweet(self, text):
        try:
            # Fill tweet text directly in the "What is happening?!" field
            self.page.fill('div[role="textbox"]', text)
            time.sleep(random.uniform(1, 2))
            
            # Try multiple selectors for the Post button
            try:
                # First attempt with the most specific selector
                self.page.click('div[data-testid="tweetButtonInline"]', timeout=3000)
            except:
                try:
                    # Second attempt with the text content
                    self.page.click('text="Post"', timeout=3000)
                except:
                    try:
                        # Third attempt with a different testid
                        self.page.click('div[data-testid="tweetButton"]', timeout=3000)
                    except Exception as e:
                        print(f"Could not find the Post button. Error: {e}")
                        return
            
            print("Tweet posted successfully!")
            time.sleep(3)
        except Exception as e:
            print(f"Error posting tweet: {e}")

    def _is_url(self, path):
        """Check if the given path is a URL."""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except:
            return False

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

    def post_tweet_with_image(self, text, image_path):
        """
        Post a tweet with an image. The image_path can be either:
        - A local file path
        - A URL to an image
        """
        try:
            temp_file = None
            
            # If it's a URL, download it first
            if self._is_url(image_path):
                temp_file = self._download_image(image_path)
                if not temp_file:
                    raise Exception("Failed to download image")
                image_path = temp_file
            
            # Fill tweet text
            self.page.fill('div[role="textbox"]', text)
            time.sleep(1)
            
            # Upload the image
            file_input = 'input[accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime"]'
            self.page.set_input_files(file_input, image_path)
            time.sleep(3)  # Increased wait time for image upload
            
            # Try multiple selectors for the Post button with retries
            max_retries = 3
            for _ in range(max_retries):
                try:
                    # First attempt with the most specific selector
                    post_button = self.page.locator('div[data-testid="tweetButtonInline"]')
                    if post_button.is_enabled():
                        post_button.click()
                        break
                except:
                    try:
                        # Second attempt with the text content
                        post_button = self.page.locator('text="Post"')
                        if post_button.is_enabled():
                            post_button.click()
                            break
                    except:
                        try:
                            # Third attempt with a different testid
                            post_button = self.page.locator('div[data-testid="tweetButton"]')
                            if post_button.is_enabled():
                                post_button.click()
                                break
                        except:
                            time.sleep(1)  # Wait before retry
            else:
                raise Exception("Could not click the Post button after multiple attempts")
            
            time.sleep(3)  # Wait for post to complete
            print("Tweet with image posted successfully!")
            
        except Exception as e:
            print(f"Error posting tweet with image: {e}")
        
        finally:
            # Clean up temporary file if we created one
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def close(self):
        """Close browser and playwright"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def post_thread(self, tweets, image_paths=None):
        try:
            # Navigate to X
            self.page.goto('https://twitter.com/home')
            time.sleep(3)
            print("Navigated to X")
            
            # Post first tweet
            tweet_input = self.page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            # tweet_input.click()  # Need to click first
            tweet_input.fill(tweets[0])
            # time.sleep(1)
            
            # Handle first image if available
            if image_paths and len(image_paths) > 0:
                print(f"Setting input files for image {image_paths[0]}")
                file_input = 'input[accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime"]'
                self.page.set_input_files(file_input, image_paths[0])
                # file_input.set_input_files(image_paths[0])
                time.sleep(2)
            
            # After first tweet, click the button to create a thread
            print("Clicking the add button to create a thread")
            create_thread_button = self.page.wait_for_selector('[data-testid="addButton"]')
            create_thread_button.click()
            time.sleep(2)
            
            # Now add remaining tweets to the thread
            for i in range(1, len(tweets)):
                print(f"Adding tweet {i+1} to the thread")
                # Get the correct tweet box for the thread
                new_tweet_box = self.page.wait_for_selector(f'[data-testid="tweetTextarea_{i}"]')
                # new_tweet_box.click()
                new_tweet_box.fill(tweets[i])
                time.sleep(1)
                
                # Handle image for this tweet if available
                if image_paths and i < len(image_paths):
                    # Check if image exists for this specific tweet
                    image_path = image_paths[i]
                    image_name = Path(image_path).name
                    if f"tweet_{i}" in image_name and os.path.exists(image_path):
                        current_tweet = self.page.locator(f'[data-testid="tweetTextarea_{i}"]')
                        file_input = current_tweet.locator('xpath=./following::input[@data-testid="fileInput"]').first
                        file_input.set_input_files(image_path)
                        time.sleep(1)
                
                # If there are more tweets to add, click the append button
                if i < len(tweets) - 1:
                    add_button = self.page.wait_for_selector('[data-testid="addButton"]')
                    add_button.click()
                    time.sleep(1)
            
           # Post the entire thread
            post_button = self.page.wait_for_selector('[data-testid="tweetButton"]')  # Changed from tweetButtonInline
            post_button.click()
            time.sleep(3)
            
            print("Thread posted successfully!")
            
        except Exception as e:
            print(f"Error posting thread: {e}")
            raise

def display_menu():
    print("\n=== X Automation Menu ===")
    print("1. Post a text tweet")
    print("2. Post a tweet with image")
    print("3. Post a thread of tweets")
    print("4. Exit")
    return input("Choose an option (1-4): ")

def main():
    # Test post_thread directly
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test tweets
        tweets = [
            "1/7 Test tweet one",
            "2/7 Test tweet two",
            "3/7 Test tweet three",
            "4/7 Test tweet four",
            "5/7 Test tweet five",
            "6/7 Test tweet six",
            "7/7 Test tweet seven"
        ]
        
        # Initialize XAutomation
        bot = XAutomation()
        bot.start()
        
        try:
            # Test post_thread with some sample images
            image_paths = [
                "threads/thread_20250130_154145/images/tweet_0.png",
                "threads/thread_20250130_154145/images/tweet_1.jpg",
                "threads/thread_20250130_154145/images/tweet_2.webp",
                "threads/thread_20250130_154145/images/tweet_3.jpg",
                "threads/thread_20250130_154145/images/tweet_4.jpg",
                "threads/thread_20250130_154145/images/tweet_5.jpg",
                "threads/thread_20250130_154145/images/tweet_6.jpg"
            ]
            
            print("Testing post_thread function...")
            bot.post_thread(tweets=tweets, image_paths=image_paths)
            
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            bot.close()
        return

    # # Original main code
    # bot = XAutomation()
    
    # # manager = ThreadManager()


    # while True:
    #     print("\nOptions:")
    #     print("1. Create and post a new thread")
    #     print("2. Post from an existing thread file")
    #     print("3. Generate thread preview only")
    #     print("4. Exit")
        
    #     choice = input("\nChoice: ")
        
    #     if choice == "1":
    #         topic = input("\nWhat would you like the thread to be about? ")
    #         manager.create_and_post_thread(topic)
            
    #     elif choice == "2":
    #         thread_file = input("\nEnter the path to the thread file: ")
    #         if os.path.exists(thread_file):
    #             manager.post_from_file(thread_file)
    #         else:
    #             print("\nFile not found!")
                
    #     elif choice == "3":
    #         topic = input("\nWhat would you like the thread to be about? ")
    #         manager.preview_thread(topic)
            
    #     elif choice == "4":
    #         print("\nClosing the browser...")
    #         bot.close()
    #         break
            
    #     else:
    #         print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    main()
