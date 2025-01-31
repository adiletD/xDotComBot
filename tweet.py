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

    def _has_hashtag(self, text):
        """Check if text contains a hashtag"""
        return '#' in text

    def _handle_hashtag_overlay(self, element):
        """Handle hashtag overlay only when it appears"""
        try:
            # Only press Tab to move focus away
            element.press('Tab')
            time.sleep(0.5)
        except Exception as e:
            print(f"Error handling hashtag: {e}")

    def _ends_with_hashtag(self, text: str) -> bool:
        """Check if the text ends with a hashtag"""
        # Split by whitespace and check if last word starts with #
        words = text.strip().split()
        return bool(words) and words[-1].startswith('#')

    def _split_hashtag_content(self, text):
        """Split text into content and hashtag if it ends with a hashtag"""
        if not self._ends_with_hashtag(text):
            return text, None
            
        words = text.split()
        hashtag = words[-1]  # Get the last word (hashtag)
        content = ' '.join(words[:-1])  # Get everything except hashtag
        return content, hashtag

    def _check_and_dismiss_overlay(self, current_tweet_box=None):
        """Check for hashtag overlay and dismiss it if present"""
        try:
            # Try multiple selectors to find the overlay
            overlay_selectors = [
                'div[role="listbox"]',
                'div[data-testid="typeaheadDropdown"]',
                'div[data-testid="typeaheadOverlay"]',
                'div[role="menu"]'
            ]
            
            for selector in overlay_selectors:
                try:
                    overlay = self.page.locator(selector)
                    if overlay.is_visible():
                        print(f"Hashtag overlay detected with selector {selector}, dismissing...")
                        
                        # Click in the thread area to dismiss overlay
                        self.page.click('div[data-testid="cellInnerDiv"]')
                        time.sleep(0.5)
                        
                        # Verify overlay is gone
                        if not overlay.is_visible():
                            print("Overlay dismissed successfully")
                            return True
                except Exception as e:
                    continue
            
            return False
        except Exception as e:
            print(f"Error checking for overlay: {e}")
            return False

    def _fill_tweet_safely(self, element, text):
        """Fill tweet content safely handling hashtags"""
        content, hashtag = self._split_hashtag_content(text)
        
        # Fill main content first
        element.click()
        time.sleep(0.5)
        
        if hashtag:
            # Fill everything and add a space at the end to dismiss overlay
            full_text = f"{content} {hashtag} "  # Note the extra space at the end
            element.fill(full_text)
            time.sleep(0.5)
            # Don't remove the space - let it stay to keep overlay dismissed
        else:
            # If no hashtag, just fill the content normally
            element.fill(text)
            time.sleep(0.5)

    def post_thread(self, tweets, image_paths=None):
        try:
            # Navigate to X
            self.page.goto('https://twitter.com/home')
            time.sleep(3)
            print("Navigated to X")
            
            # Post first tweet
            tweet_input = self.page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            self._fill_tweet_safely(tweet_input, tweets[0])
            
            # Handle first image if available
            if image_paths and len(image_paths) > 0:
                print(f"Setting input files for image {image_paths[0]}")
                file_input = 'input[accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime"]'
                self.page.set_input_files(file_input, image_paths[0])
                time.sleep(2)
            
            # Check for overlay before clicking add button
            self._check_and_dismiss_overlay(tweet_input)
            
            # After first tweet, click the button to create a thread
            print("Clicking the add button to create a thread")
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    add_button = self.page.wait_for_selector(
                        '[data-testid="addButton"]',
                        timeout=5000,
                        state='visible'
                    )
                    
                    if add_button:
                        add_button.click(force=True)
                        time.sleep(2)
                        
                        # Verify a new tweet box appeared
                        if self.page.locator('[data-testid="tweetTextarea_1"]').is_visible():
                            print("Successfully added new tweet box")
                            break
                        else:
                            print("New tweet box not visible after click, retrying...")
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_attempts - 1:
                        raise Exception("Failed to click add button after multiple attempts")
                    time.sleep(2)
            
            # Now add remaining tweets to the thread
            for i in range(1, len(tweets)):
                print(f"\nAdding tweet {i+1} to the thread")
                
                # Wait for the new tweet box
                new_tweet_box = self.page.wait_for_selector(f'[data-testid="tweetTextarea_{i}"]')
                self._fill_tweet_safely(new_tweet_box, tweets[i])
                
                # Handle image for this tweet if available
                if image_paths and i < len(image_paths):
                    image_path = image_paths[i]
                    image_name = Path(image_path).name
                    if f"tweet_{i}" in image_name and os.path.exists(image_path):
                        current_tweet = self.page.locator(f'[data-testid="tweetTextarea_{i}"]')
                        file_input = current_tweet.locator('xpath=./following::input[@data-testid="fileInput"]').first
                        file_input.set_input_files(image_path)
                        time.sleep(1)
                
                # Check for overlay before proceeding
                self._check_and_dismiss_overlay(new_tweet_box)
                
                # If there are more tweets to add, click the append button
                if i < len(tweets) - 1:
                    print("Clicking add button for next tweet...")
                    add_button = self.page.wait_for_selector('[data-testid="addButton"]')
                    add_button.click(force=True)
                    time.sleep(2)
            
            # Check for overlay before final post
            last_tweet_box = self.page.locator(f'[data-testid="tweetTextarea_{len(tweets)-1}"]')
            self._check_and_dismiss_overlay(last_tweet_box)
            
            # Post the entire thread with retries
            max_post_attempts = 5
            for attempt in range(max_post_attempts):
                try:
                    post_button = self.page.wait_for_selector('[data-testid="tweetButton"]', timeout=5000)
                    if post_button.is_enabled():
                        post_button.click(force=True)
                        time.sleep(3)
                        break
                except Exception as e:
                    print(f"Post attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_post_attempts - 1:
                        raise Exception("Failed to click post button after multiple attempts")
                    time.sleep(2)
            
            print("Thread posted successfully!")
            display_menu()
            
        except Exception as e:
            print(f"Error posting thread: {e}")
            raise

    def test_hashtag_handling(self):
        """Test method to verify hashtag handling in threads"""
        try:
            # Test tweets with hashtags at the end
            test_tweets = [
                "First tweet testing hashtag handling #test",  # First tweet ends with hashtag
                "Second tweet in the middle",
                "Third tweet also has hashtag #testing",
                "Fourth tweet normal",
                "Last tweet ends with hashtag #final"  # Last tweet ends with hashtag
            ]
            
            print("\nStarting hashtag handling test...")
            print("Test tweets:")
            for i, tweet in enumerate(test_tweets, 1):
                print(f"{i}. {tweet}")
            
            # Post the test thread
            self.post_thread(tweets=test_tweets)
            
            print("\nHashtag handling test completed!")
            
        except Exception as e:
            print(f"Error during hashtag test: {e}")
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
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
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
        elif sys.argv[1] == "hashtag_test":
            # Test hashtag handling
            bot = XAutomation()
            bot.start()
            try:
                bot.test_hashtag_handling()
            finally:
                bot.close()
            return

    # Original main code
    bot = XAutomation()
    
    while True:
        choice = display_menu()
        
        if choice == "1":
            text = input("\nEnter your tweet: ")
            bot.post_tweet(text)
        elif choice == "2":
            text = input("\nEnter your tweet: ")
            image_url = input("Enter image URL: ")
            bot.post_tweet_with_image(text, image_url)
        elif choice == "3":
            # Get number of tweets
            num_tweets = int(input("\nHow many tweets in the thread? "))
            tweets = []
            for i in range(num_tweets):
                tweet = input(f"\nEnter tweet {i+1}: ")
                tweets.append(tweet)
            bot.post_thread(tweets)
        elif choice == "4":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice!")

if __name__ == "__main__":
    main()
