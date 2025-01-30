from playwright.sync_api import sync_playwright
import time
import random
import os
import tempfile
import requests
from urllib.parse import urlparse
from pathlib import Path
from find_photo import GoogleImageFinder

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

    def post_thread(self, tweets, image_queries=None):
        try:
            # Navigate to X
            self.page.goto('https://twitter.com/home')
            time.sleep(3)
            print("Navigated to X")
            
            # If we have image queries, get the images first
            image_paths = []
            if image_queries:
                finder = GoogleImageFinder(browser=self.browser)
                finder.start()
                try:
                    image_paths = finder.download_images_for_thread(image_queries)
                finally:
                    finder.close()

            print("Downloaded images")
            
            # Post first tweet
            tweet_input = self.page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            tweet_input.fill(tweets[0])
            
            # Handle first image if available
            if image_paths and len(image_paths) > 0:
                file_input = self.page.locator('[data-testid="fileInput"]').first
                file_input.set_input_files(image_paths[0])
                time.sleep(2)
            
            # After first tweet, click the button to create a thread
            create_thread_button = self.page.locator('[data-testid="addButton"]').first
            create_thread_button.click()
            time.sleep(2)
            
            # Now add remaining tweets to the thread
            for i in range(1, len(tweets)):
                # Get the correct tweet box for the thread
                new_tweet_box = self.page.locator(f'[data-testid="tweetTextarea_{i}"]').first
                new_tweet_box.click()
                new_tweet_box.fill(tweets[i])
                time.sleep(1)
                
                # Handle image for this tweet if available
                if image_paths and i < len(image_paths):
                    # Find the file input within the current tweet's composition area
                    # Look for the file input that's after the current tweet textarea
                    current_tweet = self.page.locator(f'[data-testid="tweetTextarea_{i}"]')
                    file_input = current_tweet.locator('xpath=./following::input[@data-testid="fileInput"]').first
                    file_input.set_input_files(image_paths[i])
                    time.sleep(2)
                
                # If there are more tweets to add, click the append button
                if i < len(tweets) - 1:
                    append_button = self.page.locator('[data-testid="appendButton"]').first
                    append_button.click()
                    time.sleep(2)
            
            # Post the entire thread
            post_button = self.page.locator('[data-testid="tweetButton"]').first
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
    bot = XAutomation()
    bot.start()
    
    while True:
        choice = display_menu()
        
        if choice == "1":
            tweet_text = input("\nWhat would you like to tweet? ")
            print("\nPosting your tweet...")
            bot.post_tweet(tweet_text)
            
        elif choice == "2":
            tweet_text = input("\nWhat would you like to tweet? ")
            image_path = input("Enter the image path or URL: ")
            print("\nPosting your tweet with image...")
            bot.post_tweet_with_image(tweet_text, image_path)
            
        elif choice == "3":
            # tweet_texts = input("\nEnter the tweet texts separated by commas: ").split(',')
            tweet_texts = [
    "1/7 Let's talk about UFC gloves! A fascinating journey from bare knuckles to modern MMA gear. 🥊👊",
    "2/7 In the early days (UFC 1-4), fighters went bare-knuckle! It was raw and controversial. No gloves, no rules! 👊💥",
    "3/7 Some fighters like Art Jimmerson showed up wearing ONE boxing glove! Talk about unique style. 🥊😅",
    # ... more tweets
            ]
            image_queries = [
        "UFC 1 no gloves fighting historical",
        "UFC gloves evolution 1997",
        "Modern UFC gloves design"
    ]
            
            print("\nPosting your thread of tweets...")
            bot.post_thread(tweet_texts, image_queries)
            
        elif choice == "4":
            print("\nClosing the browser...")
            bot.close()
            break
            
        else:
            print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    main()
