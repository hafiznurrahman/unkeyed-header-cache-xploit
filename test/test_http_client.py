import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.http_client import HTTPClient

async def main():
    client = HTTPClient(
        headers={"User-Agent": "uhcxploit/1.0"},
        follow_redirects=False
    )

    try:
        url = "https://17ef1326.poison.digi.ninja:2443"
        result = await client.get(url, use_cache_buster=True, return_headers=True, return_content=False)
        print("[+] Result:")
        print(result)
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
