### utils/read_line_by_line.py ###
import os
import asyncio
import aiofiles
from utils.logger import get_logging

logger = get_logging()

async def read_line_by_line(file_path: str) -> list[str]:
    targets = []
    if not os.path.exists(file_path):
        logger.info(f"File not found: {file_path}")
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write('# Add targets below\n')
        return []
    
    async with aiofiles.open(file_path, mode='r') as f:
        async for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            targets.append(line)

    return list(set(targets))