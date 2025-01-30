from ai_provider import AIProvider, PerplexityProvider
from typing import Dict, List

class ThreadGenerator:
    def __init__(self, ai_provider: AIProvider = None):
        """Initialize with an AI provider (defaults to Perplexity)"""
        self.ai_provider = ai_provider or PerplexityProvider()
    
    def generate_thread(self, topic: str, num_tweets: int = 7) -> Dict[str, List[str]]:
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
                  - Each tweet must include an image description in [IMG: description] format
                  - Keep tweets within character limit
                  - Make the thread informative and engaging
                  - Use emojis appropriately
                  - End with a call to action"""
    
    def _parse_thread(self, response: str) -> Dict[str, List[str]]:
        tweets = []
        image_queries = []
        
        lines = response.split('\n')
        current_tweet = []
        expected_count = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # Extract expected tweet count from first tweet
            if not expected_count and '1/' in line:
                try:
                    expected_count = int(line.split('/')[1].split()[0])
                    print(f"Expected tweet count: {expected_count}")
                except:
                    expected_count = 7  # Default
            
            # Check if this is a new tweet
            if any(f"{i}/" in line.strip() for i in range(1, 10)):
                if current_tweet:
                    self._process_tweet(current_tweet, tweets, image_queries)
                current_tweet = [line]
            else:
                current_tweet.append(line)
        
        # Process the last tweet
        if current_tweet:
            self._process_tweet(current_tweet, tweets, image_queries)
        
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