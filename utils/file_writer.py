### utils/file_writer.py ###
import aiofiles
from pybloom_live import BloomFilter

class URLWriter:
    def __init__(self, filepath: str, bloom_capacity=1_000_000):
        self.filepath = filepath
        self.bloom = BloomFilter(capacity=bloom_capacity, error_rate=0.001)

    async def add(self, url: str) -> bool:
        """Return True jika URL baru dan berhasil ditulis."""
        if url in self.bloom:
            return False  # Sudah ada, skip
        self.bloom.add(url)
        async with aiofiles.open(self.filepath, "a") as f:
            await f.write(url.strip() + "\n")
        return True
