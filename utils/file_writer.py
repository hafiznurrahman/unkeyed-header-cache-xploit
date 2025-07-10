### utils/file_writer.py ###
import asyncio
import aiofiles
from pybloom_live import BloomFilter

class URLWriter:
    def __init__(self, filepath: str, bloom_capacity=1_000_000):
        self.filepath = filepath
        self.bloom = BloomFilter(capacity=bloom_capacity, error_rate=0.001)
        self._lock = asyncio.Lock()
    
    def get_count(self):
        return len(self.bloom)

    async def add(self, url: str) -> bool:
        async with self._lock:
            if url in self.bloom:
                return False 
            self.bloom.add(url)
            async with aiofiles.open(self.filepath, "a") as f:
                await f.write(url.strip() + "\n")
            return True
    