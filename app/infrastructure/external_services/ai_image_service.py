"""AI Image Generation Service - Multi-Provider Support

Supports multiple AI image generation providers:
1. Replicate (Stable Diffusion, FLUX, etc.)
2. OpenAI (DALL-E)
3. Stability AI (Stable Diffusion)
4. Custom API (tu propio servicio de IA)

Configuration via .env:
    AI_IMAGE_PROVIDER=replicate  # o openai, stability, custom
    REPLICATE_API_KEY=your_key
    OPENAI_API_KEY=your_key
    STABILITY_API_KEY=your_key
    CUSTOM_IMAGE_API_URL=http://tu-servicio:5001/generate
"""

from typing import List, Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceException


class AIImageService:
    """AI Image Generation Service with multi-provider support"""
    
    def __init__(self):
        self.provider = settings.AI_IMAGE_PROVIDER.lower()
    
    async def generate_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        character_images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI image from text prompt
        
        Automatically routes to the configured provider
        
        Args:
            prompt: Text description of the image
            style: Visual style (e.g., "anime", "realistic", "cartoon")
            aspect_ratio: Image aspect ratio (e.g., "1:1", "16:9", "9:16")
            negative_prompt: Things to avoid in the image
            character_images: Reference images for character consistency
            
        Returns:
            Generated image data with URL and generation ID
        """
        
        # Route to appropriate provider
        if self.provider == "replicate":
            return await self._generate_replicate(prompt, style, aspect_ratio, negative_prompt, character_images)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, style, aspect_ratio)
        elif self.provider == "stability":
            return await self._generate_stability(prompt, style, aspect_ratio, negative_prompt)
        elif self.provider == "custom":
            return await self._generate_custom(prompt, style, aspect_ratio, negative_prompt, character_images)
        else:
            # Fallback to mock data if no provider configured
            return await self._generate_mock(prompt, style, aspect_ratio)


# Singleton instance
ai_image_service = AIImageService()
