"""
Anthropic Claude API provider implementation.

Supports Claude models including Claude 4, Claude Sonnet, Claude Haiku.
Handles text, image, and document inputs with batch processing.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime

from .cloud_ai import CloudAIProvider
from .ai_provider import Message, AIResponse, BatchJob, ContentBlock, ContentType, MessageRole


class AnthropicProvider(CloudAIProvider):
    """
    Anthropic Claude API provider implementation.
    
    Supports:
    - Claude 4, Claude Sonnet 3.5, Claude Haiku 3
    - Text, image, and document inputs
    - Streaming responses  
    - Batch processing
    - Extended context (up to 1M tokens)
    """
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            model_name: Claude model name
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        
        # Anthropic specific configuration
        self.anthropic_version = kwargs.get('anthropic_version', '2023-06-01')
        
        # Model capabilities
        self._vision_models = {
            'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307',
            'claude-3-5-sonnet-20241022', 'claude-3-5-sonnet-20240620', 
            'claude-4', 'claude-opus-4', 'claude-sonnet-4'
        }
        
        # Context windows
        self._context_limits = {
            'claude-3-haiku-20240307': 200_000,
            'claude-3-sonnet-20240229': 200_000, 
            'claude-3-opus-20240229': 200_000,
            'claude-3-5-sonnet-20241022': 200_000,
            'claude-3-5-sonnet-20240620': 200_000,
            'claude-sonnet-4': 1_000_000,  # Beta 1M context
            'claude-opus-4': 200_000
        }
        
        # Pricing (per 1K tokens, as of 2025)
        self._pricing = {
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
            'claude-3-5-sonnet-20240620': {'input': 0.003, 'output': 0.015},
        }
        
        # Initialize client
        self._client = None
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
            except ImportError:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        return self._client
    
    def _convert_messages(self, messages: List[Message]) -> Dict[str, Any]:
        """Convert internal messages to Anthropic format."""
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content if isinstance(msg.content, str) else msg.content[0].content
                continue
                
            claude_msg = {"role": msg.role.value}
            
            if isinstance(msg.content, str):
                claude_msg["content"] = msg.content
            else:
                # Handle multimodal content
                content_parts = []
                
                for block in msg.content:
                    if block.type == ContentType.TEXT:
                        content_parts.append({
                            "type": "text",
                            "text": block.content
                        })
                    elif block.type == ContentType.IMAGE_BASE64:
                        mime_type = block.metadata.get("mime_type", "image/jpeg")
                        content_parts.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": block.content
                            }
                        })
                    elif block.type == ContentType.IMAGE_URL:
                        # Note: Claude doesn't support image URLs directly
                        # This would need to be downloaded and converted to base64
                        logging.warning("Claude doesn't support image URLs - convert to base64")
                        continue
                
                claude_msg["content"] = content_parts
            
            claude_messages.append(claude_msg)
        
        return {
            "system": system_message,
            "messages": claude_messages
        }
    
    def _make_request(self, messages: List[Message], **kwargs) -> AIResponse:
        """Make Anthropic API request."""
        client = self._get_client()
        converted = self._convert_messages(messages)
        
        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": converted["messages"],
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        
        if converted["system"]:
            request_params["system"] = converted["system"]
        
        # Add optional parameters
        if 'temperature' in kwargs:
            request_params['temperature'] = kwargs['temperature']
        if 'top_p' in kwargs:
            request_params['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            request_params['top_k'] = kwargs['top_k']
        if 'stop_sequences' in kwargs:
            request_params['stop_sequences'] = kwargs['stop_sequences']
        
        try:
            response = client.messages.create(**request_params)
            
            # Extract text content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            return AIResponse(
                content=content,
                model=response.model,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                metadata={
                    'id': response.id,
                    'type': response.type,
                    'role': response.role
                }
            )
            
        except Exception as e:
            logging.error(f"Anthropic API request failed: {e}")
            raise
    
    def _make_stream_request(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """Make streaming Anthropic API request."""
        client = self._get_client()
        converted = self._convert_messages(messages)
        
        request_params = {
            "model": self.model_name,
            "messages": converted["messages"],
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True
        }
        
        if converted["system"]:
            request_params["system"] = converted["system"]
        
        # Add optional parameters
        for key in ['temperature', 'top_p', 'top_k', 'stop_sequences']:
            if key in kwargs:
                request_params[key] = kwargs[key]
        
        try:
            with client.messages.stream(**request_params) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield event.delta.text
                            
        except Exception as e:
            logging.error(f"Anthropic streaming request failed: {e}")
            raise
    
    def create_batch_job(self, messages_list: List[List[Message]], 
                        custom_ids: List[str], **kwargs) -> BatchJob:
        """Create Anthropic batch job."""
        client = self._get_client()
        
        # Prepare batch requests
        batch_requests = []
        for messages, custom_id in zip(messages_list, custom_ids):
            converted = self._convert_messages(messages)
            
            request = {
                "custom_id": custom_id,
                "params": {
                    "model": self.model_name,
                    "messages": converted["messages"],
                    "max_tokens": kwargs.get("max_tokens", 4096)
                }
            }
            
            if converted["system"]:
                request["params"]["system"] = converted["system"]
            
            # Add optional parameters
            for key in ['temperature', 'top_p', 'top_k']:
                if key in kwargs:
                    request["params"][key] = kwargs[key]
            
            batch_requests.append(request)
        
        try:
            # Create message batch
            batch_response = client.messages.batches.create(
                requests=batch_requests
            )
            
            return BatchJob(
                job_id=batch_response.id,
                status=batch_response.processing_status,
                messages_list=messages_list,
                custom_ids=custom_ids,
                created_at=batch_response.created_at,
                metadata={
                    'type': batch_response.type,
                    'request_counts': batch_response.request_counts.__dict__ if batch_response.request_counts else {}
                }
            )
            
        except Exception as e:
            logging.error(f"Failed to create Anthropic batch job: {e}")
            raise
    
    def get_batch_job(self, job_id: str) -> BatchJob:
        """Get Anthropic batch job status and results."""
        client = self._get_client()
        
        try:
            batch_response = client.messages.batches.retrieve(job_id)
            
            results = []
            if batch_response.processing_status == 'ended':
                # Get results
                results_response = client.messages.batches.results(job_id)
                
                for result in results_response:
                    if result.result and result.result.type == 'succeeded':
                        message = result.result.message
                        
                        # Extract text content
                        content = ""
                        if message.content:
                            for block in message.content:
                                if hasattr(block, 'text'):
                                    content += block.text
                        
                        response = AIResponse(
                            content=content,
                            model=message.model,
                            usage={
                                'input_tokens': message.usage.input_tokens,
                                'output_tokens': message.usage.output_tokens,
                                'total_tokens': message.usage.input_tokens + message.usage.output_tokens
                            },
                            finish_reason=message.stop_reason,
                            metadata={'custom_id': result.custom_id}
                        )
                        results.append(response)
            
            return BatchJob(
                job_id=job_id,
                status=batch_response.processing_status,
                messages_list=[],  # Not stored in response
                custom_ids=[],     # Not stored in response  
                created_at=batch_response.created_at,
                completed_at=batch_response.ended_at,
                results=results,
                metadata={
                    'type': batch_response.type,
                    'request_counts': batch_response.request_counts.__dict__ if batch_response.request_counts else {},
                    'expires_at': batch_response.expires_at
                }
            )
            
        except Exception as e:
            logging.error(f"Failed to get batch job {job_id}: {e}")
            raise
    
    def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel Anthropic batch job."""
        client = self._get_client()
        
        try:
            client.messages.batches.cancel(job_id)
            return True
        except Exception as e:
            logging.error(f"Failed to cancel batch job {job_id}: {e}")
            return False
    
    def supports_images(self) -> bool:
        """Check if current model supports images."""
        return self.model_name in self._vision_models
    
    def get_context_limit(self) -> int:
        """Get context window size for current model."""
        return self._context_limits.get(self.model_name, 200_000)
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage."""
        if self.model_name not in self._pricing:
            return 0.0
        
        pricing = self._pricing[self.model_name]
        input_cost = usage.get('input_tokens', 0) * pricing['input'] / 1000
        output_cost = usage.get('output_tokens', 0) * pricing['output'] / 1000
        
        return input_cost + output_cost