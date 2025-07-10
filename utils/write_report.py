# utils/file_writer.py (misal)
import aiofiles
import asyncio

write_lock = asyncio.Lock()

async def safe_write_report(filename: str, content: str):
    async with write_lock:
        async with aiofiles.open(filename, mode="a") as f:
            await f.write(content)
