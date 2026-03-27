import json
import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)

class ComfyUIService:
    """Service to interact with ComfyUI API."""

    def __init__(self):
        # La URL base de la API de ComfyUI (ej: http://127.0.0.1:8188)
        self.base_url = os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188")
        self.clientid = "dreamduel-backend-1234"
        self.workflow_dir = Path(__file__).parent / "workflows"

    async def _queue_prompt(self, workflow: Dict) -> Dict:
        """Sends the workflow to ComfyUI to be executed."""
        try:
            import requests # Fallback due to Windows httpx localhost bug
            data = {"prompt": workflow, "client_id": self.clientid}
            
            def make_request():
                response = requests.post(f"{self.base_url}/prompt", json=data, timeout=10.0)
                response.raise_for_status()
                return response.json()
                
            return await asyncio.to_thread(make_request)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with ComfyUI API: {str(e)}")
            raise ExternalServiceException(f"Failed to trigger ComfyUI generation: {str(e)}")

    async def _get_history(self, prompt_id: str) -> Dict:
        """Fetches the history of a specific prompt ID."""
        try:
            import requests
            def fetch_history():
                response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10.0)
                response.raise_for_status()
                return response.json()
                
            history_data = await asyncio.to_thread(fetch_history)
            if prompt_id in history_data:
                return history_data[prompt_id]
            return {} # Prompt still running or not found
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ComfyUI history: {str(e)}")
            raise ExternalServiceException(f"Failed to fetch ComfyUI generation history: {str(e)}")

    async def poll_for_completion(self, prompt_id: str, max_retries: int = 300, delay_seconds: int = 2) -> Dict:
        """Polls ComfyUI history until the image generation is complete."""
        for _ in range(max_retries):
            history = await self._get_history(prompt_id)
            if history and "outputs" in history:
                return history
            
            await asyncio.sleep(delay_seconds)
            
        raise ExternalServiceException("ComfyUI generation timeout")

    def _load_workflow(self, filename: str) -> Dict:
        """Loads a workflow JSON file."""
        filepath = self.workflow_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Workflow file not found: {filepath}")
        
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
            try:
                text = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw_bytes.decode("utf-16", errors="ignore")
            # Remove any unwanted leading characters that break JSON parsing
            text = text.strip('\ufeff ')
            return json.loads(text)

    async def upload_image_to_comfyui(self, local_file_path: str) -> str:
        """
        Uploads an image from the local server to ComfyUI's internal storage
        Returns the filename assigned by ComfyUI.
        """
        path = Path(local_file_path)
        if not path.exists():
            raise FileNotFoundError(f"Local image not found: {local_file_path}")
            
        try:
            import requests
            def do_upload():
                with open(path, "rb") as f:
                    files = {"image": (path.name, f, "image/png")}
                    data = {"overwrite": "true"}
                    response = requests.post(f"{self.base_url}/upload/image", files=files, data=data, timeout=30.0)
                    response.raise_for_status()
                    return response.json()
            
            result = await asyncio.to_thread(do_upload)
            
            # Immediately delete the local copy to save space since ComfyUI now has it
            try:
                path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete local temporary image {path}: {str(e)}")
                
            return result.get("name")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading image to ComfyUI: {str(e)}")
            raise ExternalServiceException(f"Failed to upload image to ComfyUI: {str(e)}")

    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes the main workflow (api-modelo-comfyv1.json).
        """
        # Load the base workflow
        workflow = self._load_workflow("api-modelo-comfyv1.json")
        
        # Modify the nodes dynamically
        # 6: CLIPTextEncode (Positive Prompt)
        if "6" in workflow and "inputs" in workflow["6"]:
             # Append the user prompt to the base positive prompt from the workflow
             base_prompt = workflow["6"]["inputs"]["text"]
             workflow["6"]["inputs"]["text"] = f"{prompt}, {base_prompt}"
        
        # 7: CLIPTextEncode (Negative Prompt)
        if negative_prompt and "7" in workflow and "inputs" in workflow["7"]:
             base_neg = workflow["7"]["inputs"]["text"]
             workflow["7"]["inputs"]["text"] = f"{negative_prompt}, {base_neg}"
        
        # 3: KSampler (Randomize seed)
        import random
        if "3" in workflow and "inputs" in workflow["3"]:
            workflow["3"]["inputs"]["seed"] = random.randint(1, 2**63 - 1)

        # Handle Image uploads (Nodes 10 & 17)
        if image_paths and len(image_paths) > 0:
            # Clean all paths first by stripping leading slash
            cleaned_paths = [p[1:] if p.startswith('/') else p for p in image_paths]
            
            # Upload the first image to ComfyUI
            first_image_path = cleaned_paths[0]
            comfy_filename = await self.upload_image_to_comfyui(first_image_path)
            
            # 10: Input Image (Base image for IPAdapter)
            if "10" in workflow and "inputs" in workflow["10"]:
                workflow["10"]["inputs"]["image"] = comfy_filename
                
            # 17: Load Image (Face swap source)
            # If the user provided a second image, use it for the face, otherwise use the first one
            face_image_path = cleaned_paths[1] if len(cleaned_paths) > 1 else cleaned_paths[0]
            if face_image_path != first_image_path:
                face_comfy_filename = await self.upload_image_to_comfyui(face_image_path)
            else:
                face_comfy_filename = comfy_filename
                
            if "17" in workflow and "inputs" in workflow["17"]:
                workflow["17"]["inputs"]["image"] = face_comfy_filename
        
        # Send to ComfyUI
        queue_response = await self._queue_prompt(workflow)
        prompt_id = queue_response.get("prompt_id")
        
        if not prompt_id:
            raise ExternalServiceException("Invalid response from ComfyUI API: missing prompt_id")
            
        # Poll for completion
        history = await self.poll_for_completion(prompt_id)
        
        # Extract the resulting images (Node 9 is SaveImage)
        outputs = history.get("outputs", {})
        
        generated_images = []
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image_info in node_output["images"]:
                     # The filename relative to the ComfyUI output directory
                     filename = image_info["filename"]
                     # Constructing a generic URL to fetch it.
                     # In a real scenario, this would point to a public URL or download directly.
                     image_url = f"{self.base_url}/view?filename={filename}&type={image_info['type']}&subfolder={image_info['subfolder']}"
                     generated_images.append(image_url)

        return {
            "status": "success",
            "provider": "comfyui",
            "generation_id": prompt_id,
            "images": generated_images
        }

    async def delete_comfyui_image(self, filename: str) -> bool:
        """
        Attempts to delete an image generated by ComfyUI by accessing the mapped output folder.
        """
        output_dir = getattr(settings, "COMFYUI_OUTPUT_PATH", None)
        if not output_dir:
            logger.warning(f"Delete requested for {filename} but COMFYUI_OUTPUT_PATH is not configured in .env")
            return False
            
        file_path = Path(output_dir) / filename
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Successfully deleted ComfyUI output image: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete ComfyUI output {file_path}: {str(e)}")
                return False
        return True

comfyui_service = ComfyUIService()
