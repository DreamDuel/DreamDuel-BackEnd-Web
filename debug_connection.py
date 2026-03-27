import asyncio
import httpx
from urllib import request

print("--- TESTING URLLIB ---")
try:
    response = request.urlopen("http://127.0.0.1:8000/system_stats", timeout=5)
    print("URLLIB SUCCESS:")
    print(response.read().decode('utf-8')[:100])
except Exception as e:
    print(f"URLLIB ERROR: {e}")

print("\n--- TESTING HTTPX ---")
async def main():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:8000/system_stats")
            print("HTTPX SUCCESS:")
            print(response.text[:100])
    except Exception as e:
        print(f"HTTPX ERROR TYPE: {type(e).__name__}")
        print(f"HTTPX ERROR DETAILS: {e}")

if __name__ == "__main__":
    asyncio.run(main())
