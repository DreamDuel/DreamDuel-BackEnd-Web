import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Service to interact with ComfyUI running in Modal serverless."""

    def __init__(self):
        # Single serverless endpoint exposed by Modal (no /prompt, /upload/image, /history)
        self.base_url = (settings.MODAL_COMFYUI_URL or "").rstrip("/")

    @staticmethod
    def _normalize_local_path(path: str) -> Path:
        normalized = path[1:] if path.startswith("/") else path
        return Path(normalized)

    @staticmethod
    def _read_image_as_base64(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Local image not found: {path}")
        return base64.b64encode(path.read_bytes()).decode("ascii")

    @staticmethod
    def _ensure_data_url(image: str) -> str:
        """
        Modal returns raw base64 in images[0]. Browsers need a data URL for src=.
        Leaves http(s) URLs and existing data URLs unchanged.
        """
        s = (image or "").strip()
        if not s:
            return s
        s = "".join(s.split())
        lower = s.lower()
        if lower.startswith("data:image/"):
            return s
        if s.startswith("http://") or s.startswith("https://"):
            return s
        return f"data:image/png;base64,{s}"

    @staticmethod
    def _extract_images_from_modal_response(payload: Dict[str, Any]) -> List[str]:
        images = payload.get("images")
        if isinstance(images, list) and images:
            return [str(item) for item in images if item]

        image_url = payload.get("imageUrl") or payload.get("image_url")
        if image_url:
            return [str(image_url)]

        output = payload.get("output")
        if isinstance(output, list):
            return [str(item) for item in output if item]
        if isinstance(output, str) and output:
            return [output]

        return []

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sends prompt + base image(s) directly to Modal endpoint with one HTTP POST.
        """
        if not self.base_url:
            raise ExternalServiceException("MODAL_COMFYUI_URL is not configured")

        base_image_b64 = None
        extra_images_b64: List[str] = []
        if image_paths:
            normalized_paths = [self._normalize_local_path(p) for p in image_paths]
            base_image_b64 = self._read_image_as_base64(normalized_paths[0])
            if len(normalized_paths) > 1:
                extra_images_b64 = [
                    self._read_image_as_base64(path) for path in normalized_paths[1:]
                ]

        request_payload: Dict[str, Any] = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "base_image": base_image_b64,
            "extra_images": extra_images_b64,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.base_url, json=request_payload)
                response.raise_for_status()
                payload = response.json()
        except httpx.RequestError as e:
            logger.error(f"Error communicating with Modal ComfyUI endpoint: {str(e)}")
            raise ExternalServiceException(
                f"Failed to connect to Modal ComfyUI endpoint: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Modal ComfyUI returned HTTP {e.response.status_code}: {e.response.text}"
            )
            raise ExternalServiceException(
                f"Modal ComfyUI request failed with status {e.response.status_code}"
            )

        generated_images = self._extract_images_from_modal_response(payload)
        if not generated_images:
            raise ExternalServiceException(
                "Invalid response from Modal ComfyUI: no images found"
            )

        generation_id = (
            payload.get("generation_id")
            or payload.get("id")
            or payload.get("request_id")
            or str(uuid4())
        )

        normalized_images = [self._ensure_data_url(img) for img in generated_images]

        return {
            "status": "success",
            "provider": "comfyui",
            "generation_id": generation_id,
            "images": normalized_images,
        }

    async def delete_comfyui_image(self, filename: str) -> bool:
        """No-op: generations are in-memory / base64; nothing to delete by filename."""
        return True


comfyui_service = ComfyUIService()
