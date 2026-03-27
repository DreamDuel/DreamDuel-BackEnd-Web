import asyncio
from app.infrastructure.external_services.comfyui_service import comfyui_service
from app.core.config import settings

async def main():
    print(f"Testing connection to ComfyUI at: {settings.COMFYUI_API_URL}")
    print("Sending prompt...")
    
    try:
        result = await comfyui_service.generate_image(
            prompt="A majestic cyberpunk city skyline at night, glowing neon signs, ultra detailed, 8k resolution",
            negative_prompt="blurry, low quality, dark",
            image_paths=["app/uploads/images/test_face.png"]
        )
        print("\nSuccess! Generation result:")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
