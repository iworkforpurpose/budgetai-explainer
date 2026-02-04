"""
Groq LLM Client
Uses Groq API with Llama 3.1 8B (100% free)
"""
from typing import List, Dict, Optional
import time
from groq import Groq

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class GroqClient:
    """
    Groq API client for LLM responses
    Free tier: 30 RPM, 131k context, 560 tokens/sec
    """
    
    def __init__(self):
        """Initialize Groq client"""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        logger.info(
            "Initialized GroqClient",
            extra=log_extra(model=self.model, temperature=self.temperature)
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            content = response.choices[0].message.content
            
            logger.info(
                "Chat completion generated",
                extra=log_extra(
                    tokens_used=response.usage.total_tokens,
                    response_length=len(content)
                )
            )
            
            return content
        
        except Exception as e:
            error_msg = str(e)
            
            # Handle rate limiting
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                logger.warning("Rate limit hit, waiting 2 seconds...")
                time.sleep(2)
                # Retry once
                try:
                    return self.chat_completion(messages, temperature, max_tokens)
                except Exception as retry_error:
                    logger.error(f"Retry failed: {str(retry_error)}")
                    return self._fallback_response()
            
            logger.error(
                f"Chat completion failed: {error_msg}",
                exc_info=True
            )
            return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """Return fallback response when LLM fails"""
        return (
            "I apologize, but I'm currently unable to generate a response. "
            "This might be due to high demand or a temporary issue. "
            "Please try again in a moment."
        )


# Singleton instance
_groq_client = None

def get_groq_client() -> GroqClient:
    """Get singleton Groq client instance"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
