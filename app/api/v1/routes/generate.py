"""AI Generation routes - Guest checkout support"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from datetime import datetime, timedelta
import io

from app.api.v1.schemas.generate import (
    GenerateImageRequest, GenerateImageResponse,
    GenerationStatusResponse
)
from app.infrastructure.external_services.ai_image_service import ai_image_service
from app.infrastructure.external_services.comfyui_service import comfyui_service
from app.infrastructure.external_services.gumroad_service import gumroad_service

router = APIRouter()


@router.post("", response_model=GenerateImageResponse)
async def generate_image_guest(
    data: GenerateImageRequest
):
    """
    Generate an AI image (STATELESS)
    
    Logic:
    - No login or database required
    - Proxies the generation request to ComfyUI
    """
    
    print(f"✅ Generating statelessly for session: {data.sessionId}")
    print(f"📥 PAYLOAD RECEIVED FROM FRONTEND:")
    print(f"   - Prompt: '{data.prompt}'")
    print(f"   - Images: {data.characterImages}")
    print(f"   - License Key: {data.licenseKey}")
    
    # 1. Verify Gumroad License Key
    print("⏳ Verifying Gumroad License Key...")
    await gumroad_service.verify_license(data.licenseKey)
    print("✅ License key verified and use counted.")
    
    # 2. Generate image with AI service
    result = await ai_image_service.generate_image(
        prompt=data.prompt,
        style=data.style,
        aspect_ratio=data.aspectRatio,
        negative_prompt=data.negativePrompt,
        character_images=data.characterImages
    )
    
    print(f"✅ Image generated successfully, url={result['imageUrl']}")
    
    # Return image URL
    return GenerateImageResponse(**result)

@router.delete("/{filename}", status_code=status.HTTP_200_OK)
async def delete_generated_image(filename: str):
    """
    Legacy route: kept for older clients. Images are base64/data URLs from Modal;
    there is no server-side file to remove. Always succeeds.
    """
    if filename:
        await comfyui_service.delete_comfyui_image(filename)
    return {"message": "Image deleted successfully", "success": True}


@router.get("/download", status_code=status.HTTP_200_OK)
async def proxy_download_image(url: str = Query(..., description="ComfyUI image URL to proxy")):
    """
    Proxy endpoint to download an image from ComfyUI.
    The frontend cannot fetch ComfyUI images directly due to CORS,
    so this endpoint fetches the image server-side and streams it back.
    """
    import requests as sync_requests
    import asyncio

    try:
        def fetch_image():
            resp = sync_requests.get(url, timeout=30.0)
            resp.raise_for_status()
            return resp.content, resp.headers.get("content-type", "image/png")

        image_bytes, content_type = await asyncio.to_thread(fetch_image)

        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=dreamduel-{int(datetime.now().timestamp())}.png",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        print(f"❌ Error proxying image download: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to download image from source: {str(e)}")
