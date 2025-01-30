from abc import ABC, abstractmethod
from typing import Dict, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_completion(self, prompt: str) -> str:
        """Generate completion from prompt"""
        pass

class PerplexityProvider(AIProvider):
    """Perplexity implementation using official API"""
    
    def __init__(self):
        self.api_key = os.getenv("PPLX_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key, 
            base_url="https://api.perplexity.ai"
        )
    
    def start(self):
        """No-op for API-based provider"""
        pass
    
    def close(self):
        """No-op for API-based provider"""
        pass
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using Perplexity API"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates engaging Twitter threads."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=messages,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating completion: {e}")
            return ""

class AnthropicProvider(AIProvider):
    """Anthropic Claude implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize Anthropic client here
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using Anthropic Claude"""
        # Implement Anthropic API call
        pass

class OpenAIProvider(AIProvider):
    """OpenAI implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize OpenAI client here
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using OpenAI"""
        # Implement OpenAI API call
        pass 