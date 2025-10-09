"""
Neural Network provider base class.

Abstract base for custom neural networks and deep learning models.
Handles PyTorch, TensorFlow, and other ML framework models.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Iterator, Union
from abc import abstractmethod

from .ai_provider import AIProvider, Message, AIResponse, BatchJob, ContentBlock, ContentType


class NeuralNetworkProvider(AIProvider):
    """
    Base class for neural network-based providers.
    
    Handles:
    - Custom model architectures
    - Training and inference modes
    - GPU/CPU computation
    - Batch processing optimization
    - Model checkpointing
    - Custom preprocessing/postprocessing
    """
    
    def __init__(self, model_name: str, model_config: Dict[str, Any], **kwargs):
        """
        Initialize neural network provider.
        
        Args:
            model_name: Name of the neural network
            model_config: Configuration for model architecture
            **kwargs: Additional parameters
        """
        super().__init__(model_name, **kwargs)
        self.model_config = model_config
        
        # Framework selection
        self.framework = kwargs.get('framework', 'pytorch')  # 'pytorch', 'tensorflow', 'onnx'
        
        # Model paths
        self.checkpoint_path = kwargs.get('checkpoint_path')
        self.config_path = kwargs.get('config_path')
        
        # Hardware configuration
        self.device = kwargs.get('device', 'auto')
        self.use_mixed_precision = kwargs.get('use_mixed_precision', False)
        self.batch_size = kwargs.get('batch_size', 1)
        
        # Model state
        self.model = None
        self.is_loaded = False
        self.is_training = kwargs.get('training_mode', False)
        
        # Preprocessing/postprocessing
        self.tokenizer = None
        self.image_processor = None
        self.text_processor = None
        
        # Performance tracking
        self.total_inferences = 0
        self.total_training_steps = 0
        self.average_inference_time = 0.0
    
    def _detect_framework_device(self) -> str:
        """Auto-detect best device for the framework."""
        if self.device != 'auto':
            return self.device
        
        if self.framework == 'pytorch':
            try:
                import torch
                if torch.cuda.is_available():
                    return 'cuda'
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return 'mps'
            except ImportError:
                pass
                
        elif self.framework == 'tensorflow':
            try:
                import tensorflow as tf
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    return 'gpu'
            except ImportError:
                pass
        
        return 'cpu'
    
    @abstractmethod
    def _build_model(self) -> Any:
        """
        Build the neural network model.
        
        Returns:
            Model object (framework-specific)
        """
        pass
    
    @abstractmethod
    def _load_checkpoint(self, checkpoint_path: str):
        """
        Load model from checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
        """
        pass
    
    @abstractmethod
    def _save_checkpoint(self, checkpoint_path: str):
        """
        Save model checkpoint.
        
        Args:
            checkpoint_path: Path to save checkpoint
        """
        pass
    
    @abstractmethod
    def _preprocess_messages(self, messages: List[Message]) -> Any:
        """
        Preprocess messages for model input.
        
        Args:
            messages: Raw messages
            
        Returns:
            Preprocessed data (framework-specific)
        """
        pass
    
    @abstractmethod
    def _postprocess_output(self, model_output: Any) -> str:
        """
        Postprocess model output to text.
        
        Args:
            model_output: Raw model output
            
        Returns:
            Processed text response
        """
        pass
    
    @abstractmethod
    def _forward_pass(self, input_data: Any, **kwargs) -> Any:
        """
        Perform forward pass through the model.
        
        Args:
            input_data: Preprocessed input
            **kwargs: Generation parameters
            
        Returns:
            Raw model output
        """
        pass
    
    def load_model(self):
        """Load and initialize the neural network."""
        if self.is_loaded:
            return
            
        logging.info(f"Loading neural network: {self.model_name}")
        
        # Build model architecture
        self.model = self._build_model()
        
        # Load checkpoint if available
        if self.checkpoint_path and os.path.exists(self.checkpoint_path):
            logging.info(f"Loading checkpoint: {self.checkpoint_path}")
            self._load_checkpoint(self.checkpoint_path)
        
        # Move to device
        device = self._detect_framework_device()
        self._move_to_device(device)
        
        # Set to evaluation mode by default
        if not self.is_training:
            self._set_eval_mode()
        
        self.is_loaded = True
        logging.info(f"Neural network loaded on device: {device}")
    
    def _move_to_device(self, device: str):
        """Move model to specified device (framework-specific)."""
        if self.framework == 'pytorch':
            try:
                import torch
                if device == 'cuda' and torch.cuda.is_available():
                    self.model = self.model.cuda()
                elif device == 'mps' and hasattr(torch.backends, 'mps'):
                    self.model = self.model.to('mps')
                else:
                    self.model = self.model.cpu()
            except ImportError:
                pass
        elif self.framework == 'tensorflow':
            # TensorFlow handles device placement automatically
            pass
    
    def _set_eval_mode(self):
        """Set model to evaluation mode."""
        if self.framework == 'pytorch':
            try:
                self.model.eval()
            except AttributeError:
                pass
        elif self.framework == 'tensorflow':
            # TensorFlow models don't have explicit eval mode
            pass
    
    def generate_text(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Generate text using neural network.
        
        Args:
            messages: List of conversation messages
            **kwargs: Generation parameters
            
        Returns:
            AIResponse with generated text
        """
        import time
        
        # Ensure model is loaded
        self.load_model()
        
        start_time = time.time()
        
        # Preprocess input
        input_data = self._preprocess_messages(messages)
        
        # Forward pass
        with self._inference_context():
            model_output = self._forward_pass(input_data, **kwargs)
        
        # Postprocess output
        response_text = self._postprocess_output(model_output)
        
        # Calculate timing
        inference_time = time.time() - start_time
        self._update_performance_stats(inference_time)
        
        return AIResponse(
            content=response_text,
            model=self.model_name,
            usage={"inference_time": inference_time},
            metadata={
                "framework": self.framework,
                "device": self._detect_framework_device()
            }
        )
    
    def _inference_context(self):
        """Context manager for inference (framework-specific)."""
        if self.framework == 'pytorch':
            try:
                import torch
                return torch.no_grad()
            except ImportError:
                pass
                
        # Default: no-op context manager
        from contextlib import nullcontext
        return nullcontext()
    
    def generate_text_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Generate streaming text - default yields complete response.
        Override for true streaming generation.
        """
        response = self.generate_text(messages, **kwargs)
        yield response.content
    
    def create_batch_job(self, messages_list: List[List[Message]], 
                        custom_ids: List[str], **kwargs) -> BatchJob:
        """
        Process batch of requests with optimized batching.
        
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
        
        # Ensure model is loaded
        self.load_model()
        
        # Process in batches for efficiency
        results = []
        batch_size = kwargs.get('batch_size', self.batch_size)
        
        for i in range(0, len(messages_list), batch_size):
            batch = messages_list[i:i + batch_size]
            
            # Process batch
            batch_results = self._process_batch(batch, **kwargs)
            results.extend(batch_results)
        
        return BatchJob(
            job_id=job_id,
            status="completed",
            messages_list=messages_list,
            custom_ids=custom_ids,
            created_at=created_at,
            completed_at=datetime.now().isoformat(),
            results=results
        )
    
    def _process_batch(self, messages_batch: List[List[Message]], **kwargs) -> List[AIResponse]:
        """
        Process a batch of messages efficiently.
        
        Args:
            messages_batch: Batch of message lists
            **kwargs: Generation parameters
            
        Returns:
            List of AIResponse objects
        """
        # Default implementation: process individually
        # Subclasses can override for true batch processing
        results = []
        for messages in messages_batch:
            try:
                response = self.generate_text(messages, **kwargs)
                results.append(response)
            except Exception as e:
                error_response = AIResponse(
                    content=f"Error: {str(e)}",
                    model=self.model_name,
                    finish_reason="error"
                )
                results.append(error_response)
        return results
    
    def get_batch_job(self, job_id: str) -> BatchJob:
        """Neural networks process batches immediately."""
        raise NotImplementedError("Batch job retrieval not implemented for neural networks")
    
    def cancel_batch_job(self, job_id: str) -> bool:
        """Neural network batch jobs complete immediately."""
        return False
    
    def save_model(self, save_path: str):
        """Save current model state."""
        if not self.is_loaded:
            raise RuntimeError("Model must be loaded before saving")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        self._save_checkpoint(save_path)
        logging.info(f"Model saved to: {save_path}")
    
    def _update_performance_stats(self, inference_time: float):
        """Update performance tracking."""
        self.total_inferences += 1
        
        # Update rolling average
        if self.total_inferences == 1:
            self.average_inference_time = inference_time
        else:
            alpha = 0.1  # Smoothing factor
            self.average_inference_time = (
                alpha * inference_time + 
                (1 - alpha) * self.average_inference_time
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get neural network model information."""
        info = super().get_model_info()
        info.update({
            "type": "neural_network",
            "framework": self.framework,
            "device": self._detect_framework_device(),
            "is_loaded": self.is_loaded,
            "is_training": self.is_training,
            "checkpoint_path": self.checkpoint_path,
            "model_config": self.model_config,
            "performance": {
                "total_inferences": self.total_inferences,
                "average_inference_time": self.average_inference_time
            }
        })
        return info
    
    def supports_images(self) -> bool:
        """Check if this neural network supports image inputs."""
        # Default: depends on model configuration
        return self.model_config.get('supports_images', False)
    
    def supports_streaming(self) -> bool:
        """Most neural networks don't support true streaming."""
        return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_inferences": self.total_inferences,
            "total_training_steps": self.total_training_steps,
            "average_inference_time": self.average_inference_time,
            "model": self.model_name,
            "framework": self.framework
        }