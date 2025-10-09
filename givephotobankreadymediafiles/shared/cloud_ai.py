"""
Cloud AI provider base class.

Abstract base for cloud-based AI services like OpenAI, Anthropic, Google, etc.
Handles common cloud AI patterns like API keys, rate limiting, retries.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Iterator
from abc import abstractmethod

from .ai_provider import AIProvider, Message, AIResponse, BatchJob


class CloudAIProvider(AIProvider):
    """
    Base class for cloud-based AI providers.
    
    Handles:
    - API authentication
    - Rate limiting  
    - Request retries
    - Error handling
    - Usage tracking
    """
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, **kwargs):
        """
        Initialize cloud AI provider.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for authentication
            base_url: Base URL for API endpoints
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_delay = kwargs.get('retry_delay', 1)
        self.timeout = kwargs.get('timeout', 240)
        
        # Rate limiting
        self.requests_per_minute = kwargs.get('requests_per_minute', 60)
        self.last_request_time = 0
        self.request_interval = 60.0 / self.requests_per_minute
        
        # Usage tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _retry_on_failure(self, func, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logging.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logging.error(f"All {self.max_retries + 1} attempts failed")
        
        raise last_exception
    
    def _update_usage_stats(self, response: AIResponse):
        """Update usage statistics."""
        self.total_requests += 1
        if 'total_tokens' in response.usage:
            self.total_tokens += response.usage['total_tokens']
        
        # Calculate cost if pricing info available
        if hasattr(self, '_calculate_cost'):
            cost = self._calculate_cost(response.usage)
            self.total_cost += cost
    
    @abstractmethod
    def _make_request(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Make the actual API request.
        
        Args:
            messages: List of messages
            **kwargs: Request parameters
            
        Returns:
            AIResponse
        """
        pass
    
    @abstractmethod
    def _make_stream_request(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Make streaming API request.
        
        Args:
            messages: List of messages
            **kwargs: Request parameters
            
        Yields:
            Text chunks
        """
        pass
    
    def generate_text(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Generate text using cloud API with rate limiting and retries.
        
        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters
            
        Returns:
            AIResponse with generated text
        """
        self._wait_for_rate_limit()
        
        response = self._retry_on_failure(self._make_request, messages, **kwargs)
        self._update_usage_stats(response)
        
        return response
    
    def generate_text_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Generate streaming text using cloud API.
        
        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters
            
        Yields:
            Text chunks
        """
        self._wait_for_rate_limit()
        
        for chunk in self._retry_on_failure(self._make_stream_request, messages, **kwargs):
            yield chunk
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model_name
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0