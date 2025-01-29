from playwright.sync_api import sync_playwright
import time
import random
import os
import tempfile
import requests
from urllib.parse import urlparse
from pathlib import Path

class XAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.user_data_dir = "./chrome-data"

    def start(self):
        """Initialize the browser using saved session"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
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
                verify=True  # Enable SSL verification
            )
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Map content types to extensions
            extensions = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            content_type = response.headers.get('content-type', '').lower()
            ext = extensions.get(content_type, '.jpg')
            
            # Create temporary file that persists until we're done
            temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            
            # Download in chunks to handle large files
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file.close()
            
            return temp_file.name
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while downloading image: {e}")
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
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def post_thread(self, tweets):
        """
        Post a thread of tweets
        """
        try:
            # Click tweet button to open compose window
            tweet_input = self.page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            tweet_input.fill(tweets[0])
            
            # Add remaining tweets to thread
            for tweet in tweets[1:]:
                # Click the + button to add new tweet
                add_button = self.page.wait_for_selector('[data-testid="addButton"]')
                add_button.click()
                
                # Wait for and fill the new tweet textarea
                tweet_number = tweets.index(tweet)
                tweet_input = self.page.wait_for_selector(f'[data-testid="tweetTextarea_{tweet_number}"]')
                tweet_input.fill(tweet)
                time.sleep(1)  # Small wait between tweets
            
            # Wait for and click Post all button - using the correct selector
            time.sleep(1)  # Wait for button to become interactive
            post_button = self.page.wait_for_selector('[data-testid="tweetButton"]')  # Changed from tweetButtonInline
            print(f"Found button with text: {post_button.inner_text()}")
            post_button.click()
            print("Clicked post button")
            
            # Wait for post to complete
            time.sleep(3)
            
        except Exception as e:
            print(f"Error posting thread: {e}")


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
            print("\nPosting your thread of tweets...")
            bot.post_thread(tweet_texts)
            
        elif choice == "4":
            print("\nClosing the browser...")
            bot.close()
            break
            
        else:
            print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    main()
