from ai_provider import AIProvider, PerplexityProvider
from typing import Dict, List

class ThreadGenerator:
    def __init__(self, ai_provider: AIProvider = None):
        """Initialize with an AI provider (defaults to Perplexity)"""
        self.ai_provider = ai_provider or PerplexityProvider()
    
    def generate_thread(self, topic: str, num_tweets: int = 10) -> Dict[str, List[str]]:
        """Generate a thread about a topic"""
        try:
            self.ai_provider.start()
            
            prompt = self._create_prompt(topic, num_tweets)
            response = self.ai_provider.generate_completion(prompt)
            
            return self._parse_thread(response)
            
        finally:
            self.ai_provider.close()
    
    def _create_prompt(self, topic: str, num_tweets: int) -> str:
        """Create the prompt for the AI provider"""
        return f"""Create an engaging Twitter thread about {topic} with {num_tweets} tweets.
                  Requirements:
                  - Each tweet should be numbered (1/{num_tweets})
                  - Each tweet must include an image description in [IMG: description] format. The image description should be of an image that is 
                  likely to exist on the internet. We can not afford to photoshop images. If its regarding a particular person then put his name and surname as well
                  - Keep tweets within character limit
                  - The first tweet should be a hook, perhaps mentioning the most interesting fact about the topic or a questions or a statement that will make the reader want to read the rest of the thread
                  - Make the thread informative and engaging
                  - If there is any factual information information make sure it is accurate
                  - If there is an interesting fact or story about the topic we should mention it
                  - Use emojis appropriately
                  - End with a call to action
                  - If there is an upcoming event or occasion regarding this topic that is popular then mention it
                  """
    
    def _parse_thread(self, response: str) -> Dict[str, List[str]]:
        """Process a single tweet's lines into tweet text and image query"""
        # Print the raw response first
        print("\n=== Raw AI Response ===")
        print(response)
        print("=====================\n")
        
        tweets = []
        image_queries = []
        
        lines = response.split('\n')
        current_tweet = []
        expected_count = None
        
        # Print each line as we process it
        for line in lines:
            if not line.strip():
                continue
            
            # Extract expected tweet count from first tweet
            if not expected_count and '1/' in line:
                try:
                    expected_count = int(line.split('/')[1].split()[0])
                    print(f"Expected tweet count: {expected_count}")
                except:
                    expected_count = 10  # Default
            
            # Check if this is a new tweet
            if any(f"{i}/" in line.strip() for i in range(1, 11)):
                if current_tweet:
                    self._process_tweet(current_tweet, tweets, image_queries)
                current_tweet = [line]
                print(f"Found tweet marker: {line}")
            else:
                current_tweet.append(line)
        
        # Process the last tweet
        if current_tweet:
            self._process_tweet(current_tweet, tweets, image_queries)
        
        # Print final count
        print(f"\nProcessed {len(tweets)} tweets")
        
        # Verify we got all expected tweets
        if expected_count and len(tweets) < expected_count:
            print(f"Warning: Expected {expected_count} tweets but only got {len(tweets)}")
            return None
        
        return {
            'tweets': tweets,
            'image_queries': image_queries
        }
    
    def _process_tweet(self, tweet_lines: List[str], tweets: List[str], image_queries: List[str]):
        """Process a single tweet's lines into tweet text and image query"""
        tweet_text = ' '.join(tweet_lines)
        
        # Extract image description
        img_start = tweet_text.find('[IMG:')
        if img_start != -1:
            img_end = tweet_text.find(']', img_start)
            image_query = tweet_text[img_start+5:img_end].strip()
            tweet_text = tweet_text[:img_start].strip()
            
            tweets.append(tweet_text)
            image_queries.append(image_query) 