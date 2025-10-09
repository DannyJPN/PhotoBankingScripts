"""
Local AI provider base class.

Abstract base for local AI models like Ollama, Hugging Face Transformers, etc.
Handles local model loading, GPU management, and local inference.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Iterator
from abc import abstractmethod

from .ai_provider import AIProvider, Message, AIResponse, BatchJob


class LocalAIProvider(AIProvider):
    """
    Base class for local AI model providers.
    
    Handles:
    - Model loading and unloading
    - GPU/CPU resource management
    - Local model caching
    - Memory optimization
    - Local batch processing
    """
    
    def __init__(self, model_name: str, model_path: Optional[str] = None, **kwargs):
        """
        Initialize local AI provider.
        
        Args:
            model_name: Name/identifier of the model
            model_path: Path to local model files
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.model_path = model_path or self._get_default_model_path()
        
        # Resource management
        self.device = kwargs.get('device', 'auto')  # 'cpu', 'cuda', 'mps', 'auto'
        self.max_memory = kwargs.get('max_memory', None)
        self.load_in_8bit = kwargs.get('load_in_8bit', False)
        self.load_in_4bit = kwargs.get('load_in_4bit', False)
        
        # Generation parameters
        self.max_new_tokens = kwargs.get('max_new_tokens', 512)
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 0.9)
        self.do_sample = kwargs.get('do_sample', True)
        
        # Model state
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        # Usage stats
        self.total_generations = 0
        self.total_tokens_generated = 0
    
    def _get_default_model_path(self) -> str:
        """Get default path for model storage."""
        return os.path.join(os.path.expanduser("~"), ".cache", "local_ai_models", self.model_name)
    
    def _detect_device(self) -> str:
        """Auto-detect best available device."""
        if self.device != 'auto':
            return self.device
            
        try:
            import torch
            if torch.cuda.is_available():
                return 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'
        except ImportError:
            pass
            
        return 'cpu'
    
    @abstractmethod
    def _load_model(self):
        """Load the model and tokenizer."""
        pass
    
    @abstractmethod
    def _unload_model(self):
        """Unload the model to free memory."""
        pass
    
    @abstractmethod
    def _generate_response(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Generate response using loaded model.
        
        Args:
            messages: List of messages
            **kwargs: Generation parameters
            
        Returns:
            AIResponse
        """
        pass
    
    def load_model(self):
        """Load model if not already loaded."""
        if not self.is_loaded:
            logging.info(f"Loading local model: {self.model_name}")
            self._load_model()
            self.is_loaded = True
            logging.info(f"Model loaded successfully on device: {self._detect_device()}")
    
    def unload_model(self):
        """Unload model to free resources."""
        if self.is_loaded:
            logging.info(f"Unloading model: {self.model_name}")
            self._unload_model()
            self.is_loaded = False
            self.model = None
            self.tokenizer = None
    
    def generate_text(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Generate text using local model.
        
        Args:
            messages: List of conversation messages
            **kwargs: Generation parameters
            
        Returns:
            AIResponse with generated text
        """
        # Ensure model is loaded
        self.load_model()
        
        # Merge generation parameters
        gen_kwargs = {
            'max_new_tokens': self.max_new_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'do_sample': self.do_sample
        }
        gen_kwargs.update(kwargs)
        
        response = self._generate_response(messages, **gen_kwargs)
        
        # Update stats
        self.total_generations += 1
        if 'total_tokens' in response.usage:
            self.total_tokens_generated += response.usage['total_tokens']
        
        return response
    
    def generate_text_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Generate streaming text - default implementation yields complete response.
        
        Args:
            messages: List of conversation messages
            **kwargs: Generation parameters
            
        Yields:
            Text chunks
        """
        # Default implementation - subclasses can override for true streaming
        response = self.generate_text(messages, **kwargs)
        yield response.content
    
    def create_batch_job(self, messages_list: List[List[Message]], 
                        custom_ids: List[str], **kwargs) -> BatchJob:
        """
        Create local batch job - processes immediately.
        
        Args:
            messages_list: List of message conversations
            custom_ids: Custom identifiers
            **kwargs: Generation parameters
            
        Returns:
            Completed BatchJob
        """
        import uuid
        from datetime import datetime
        
        job_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Process all requests
        results = []
        for messages in messages_list:
            try:
                response = self.generate_text(messages, **kwargs)
                results.append(response)
            except Exception as e:
                # Create error response
                error_response = AIResponse(
                    content=f"Error: {str(e)}",
                    model=self.model_name,
                    finish_reason="error"
                )
                results.append(error_response)
        
        return BatchJob(
            job_id=job_id,
            status="completed",
            messages_list=messages_list,
            custom_ids=custom_ids,
            created_at=created_at,
            completed_at=datetime.now().isoformat(),
            results=results
        )
    
    def get_batch_job(self, job_id: str) -> BatchJob:
        """Local models complete batch jobs immediately."""
        # For local models, we don't store job history
        # This would need to be implemented if job persistence is needed
        raise NotImplementedError("Local batch job retrieval not implemented")
    
    def cancel_batch_job(self, job_id: str) -> bool:
        """Local batch jobs can't be cancelled as they complete immediately."""
        return False
    
    def supports_batch(self) -> bool:
        """Local models support synchronous batch processing."""
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the local model."""
        info = super().get_model_info()
        info.update({
            "type": "local",
            "path": self.model_path,
            "device": self._detect_device(),
            "is_loaded": self.is_loaded,
            "memory_usage": self._get_memory_usage()
        })
        return info
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage."""
        memory_info = {"available": True}
        
        try:
            import psutil
            process = psutil.Process()
            memory_info["ram_usage_mb"] = process.memory_info().rss / 1024 / 1024
        except ImportError:
            memory_info["ram_usage_mb"] = "unknown"
        
        try:
            import torch
            if torch.cuda.is_available():
                memory_info["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1024 / 1024
                memory_info["gpu_memory_cached"] = torch.cuda.memory_reserved() / 1024 / 1024
        except ImportError:
            pass
            
        return memory_info
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_generations": self.total_generations,
            "total_tokens_generated": self.total_tokens_generated,
            "model": self.model_name,
            "device": self._detect_device()
        }
    
    def __del__(self):
        """Ensure model is unloaded when provider is destroyed."""
        if hasattr(self, 'is_loaded') and self.is_loaded:
            try:
                self.unload_model()
            except Exception:
                pass  # Ignore errors during cleanup