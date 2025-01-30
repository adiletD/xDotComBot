from thread_generator import ThreadGenerator
from find_photo import GoogleImageFinder
from tweet import XAutomation
from datetime import datetime
import os
import webbrowser
import time

class ThreadManager:
    def __init__(self):
        self.generator = ThreadGenerator()
        self.x_bot = XAutomation()
        
    def create_and_post_thread(self, topic):
        """Main workflow to generate and post a thread"""
        try:
            # 1. Generate thread content
            print(f"Generating thread about: {topic}")
            thread_data = self.generator.generate_thread(topic)
            
            # Check if thread generation was successful
            if thread_data is None:
                print("Thread generation failed - incomplete thread detected")
                if self._get_retry_confirmation():
                    return self.create_and_post_thread(topic)
                return
            
            # Save thread to markdown and get user confirmation/edits
            thread_dir = self._save_thread_preview(topic, thread_data)
            if not self._preview_and_edit_thread(thread_dir):
                return
            
            # Load potentially edited thread data
            thread_data = self._load_thread_from_markdown(thread_dir)
            
            # Start the browser session first
            self.x_bot.start()
            
            # Now pass the browser instance to handle images
            image_paths = self._handle_images(thread_data, self.x_bot.browser)
            if not image_paths:
                return
            
            # 3. Post the thread
            print("Posting thread...")
            self.x_bot.post_thread(
                tweets=thread_data['tweets'],
                image_paths=image_paths
            )
            
        except Exception as e:
            print(f"Error creating thread: {e}")
        finally:
            self.x_bot.close()
    
    def _save_thread_preview(self, topic, thread_data):
        """Save thread to markdown file and create images directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thread_dir = f"threads/thread_{timestamp}"
        os.makedirs(f"{thread_dir}/images", exist_ok=True)
        
        filename = f"{thread_dir}/thread.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Thread: {topic}\n\n")
            f.write("## Configuration\n")
            f.write("- Status: DRAFT\n")
            f.write(f"- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Thread ID: {timestamp}\n\n")
            
            f.write("## Content\n")
            for i, (tweet, img_query) in enumerate(zip(
                thread_data['tweets'], 
                thread_data['image_queries']
            )):
                f.write(f"\n### Tweet {i+1}\n")
                f.write(f"```text\n{tweet}\n```\n")
                f.write(f"\n**Image Query:** {img_query}\n")
                f.write("**Custom Image URL:** \n")
        
        return thread_dir
    
    def _preview_and_edit_thread(self, thread_dir):
        """Show preview and allow user to edit"""
        print(f"\nThread preview saved to: {thread_dir}")
        print("Please review the thread content and image queries.")
        print("You can edit the file directly to make changes.")
        
        # Open directory in default file explorer
        webbrowser.open(thread_dir)
        
        return input("\nProceed with this thread? (y/n): ").lower() == 'y'
    
    def _load_thread_from_markdown(self, thread_dir):
        """Load potentially edited thread data from markdown"""
        tweets = []
        image_queries = []
        custom_urls = []
        
        filename = f"{thread_dir}/thread.md"
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the markdown content
        sections = content.split('### Tweet ')
        for section in sections[1:]:  # Skip header
            # Extract tweet content
            tweet_start = section.find('```text\n') + 8
            tweet_end = section.find('\n```', tweet_start)
            tweets.append(section[tweet_start:tweet_end].strip())
            
            # Extract image query
            query_start = section.find('**Image Query:**') + 15
            query_end = section.find('\n', query_start)
            image_queries.append(section[query_start:query_end].strip())
            
            # Extract custom URL if provided
            url_start = section.find('**Custom Image URL:**') + 19
            url_end = section.find('\n', url_start) if section.find('\n', url_start) != -1 else len(section)
            custom_url = section[url_start:url_end].strip()
            # Only add URL if it's not empty and not just markdown formatting
            if custom_url and not custom_url.startswith('**'):
                custom_urls.append(custom_url)
            else:
                custom_urls.append(None)
        
        return {
            'tweets': tweets,
            'image_queries': image_queries,
            'custom_urls': custom_urls,
            'thread_dir': thread_dir
        }
    
    def _handle_images(self, thread_data, browser):
        """Download images using either custom URLs or image queries"""
        self.thread_data = thread_data  # Store for use in _try_image_search
        finder = GoogleImageFinder(browser=browser)
        finder.start()
        final_paths = []
        
        try:
            for i, (query, custom_url) in enumerate(zip(
                thread_data['image_queries'], 
                thread_data['custom_urls']
            )):
                current_path = None
                
                # Try custom URL first if provided
                if custom_url and custom_url.strip():
                    print(f"\nUsing custom URL for tweet {i+1}")
                    images_dir = os.path.join(thread_data['thread_dir'], 'images')
                    current_path = finder.download_single_image(
                        url=custom_url,
                        filename_base=f"tweet_{i}",
                        output_dir=images_dir
                    )
                
                # Fall back to image search if no custom URL or download failed
                if not current_path:
                    print(f"\nSearching for image {i+1}: {query}")
                    current_path = self._try_image_search(finder, query, i)
                
                # Handle the result
                if current_path:
                    print(f"Downloaded image for tweet {i+1}: {current_path}")
                    if not self._confirm_image(i+1):
                        new_url = input("Enter alternative image URL (or press Enter to skip): ")
                        if new_url and new_url.strip():
                            new_path = finder.download_single_image(new_url, f"tweet_{i}")
                            if new_path:
                                current_path = new_path
                                print(f"Successfully updated image for tweet {i+1}")
                    final_paths.append(current_path)
                else:
                    print(f"Failed to get image for tweet {i+1}")
                    new_url = input("Enter alternative image URL (or press Enter to skip): ")
                    if new_url and new_url.strip():
                        new_path = finder.download_single_image(new_url, f"tweet_{i}")
                        if new_path:
                            final_paths.append(new_path)
                            print(f"Successfully added image for tweet {i+1}")
                
                time.sleep(2)
            
            return final_paths
                
        finally:
            finder.close()
    
    def _confirm_image(self, tweet_num):
        return input(f"\nUse this image for tweet {tweet_num}? (y/n): ").lower() == 'y'

    def _get_user_confirmation(self):
        """Get user confirmation to post"""
        return input("\nPost this thread? (y/n): ").lower() == 'y'

    def _get_retry_confirmation(self):
        return input("\nWould you like to try generating the thread again? (y/n): ").lower() == 'y'

    def _try_image_search(self, finder, query, index):
        """Try to find and download an image using the search query"""
        try:
            url = finder.search_image(query)
            if url and not url.startswith('data:'):
                # Use the thread-specific images directory
                images_dir = os.path.join(self.thread_data['thread_dir'], 'images')
                return finder.download_single_image(
                    url=url,
                    filename_base=f"tweet_{index}",
                    output_dir=images_dir
                )
        except Exception as e:
            print(f"Error during image search: {e}")
        return None

    def post_existing_thread(self, folder_name):
        """Post a thread from an existing folder"""
        try:
            # Construct the full path
            thread_dir = os.path.join("threads", folder_name)
            thread_file = os.path.join(thread_dir, "thread.md")
            
            # Verify the folder and file exist
            if not os.path.exists(thread_file):
                print(f"Error: Thread file not found at {thread_file}")
                return
            
            # Load thread data from markdown
            thread_data = self._load_thread_from_markdown(thread_dir)
            
            # Get list of image files
            image_dir = os.path.join(thread_dir, "images")
            if os.path.exists(image_dir):
                image_files = sorted([
                    os.path.join(image_dir, f) 
                    for f in os.listdir(image_dir) 
                    if f.startswith("tweet_")
                ])
            else:
                image_files = []
            
            # Start the browser session
            self.x_bot.start()
            
            # Post the thread
            print("Posting thread...")
            self.x_bot.post_thread(
                tweets=thread_data['tweets'],
                image_paths=image_files
            )
            
            print("Thread posted successfully!")
            
        except Exception as e:
            print(f"Error posting existing thread: {e}")
        finally:
            self.x_bot.close() 