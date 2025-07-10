### engine/check_url.py ###
import os
import aiofiles
import asyncio
from utils.helpers import without_param_fragment
from utils.logger import get_logging
from utils.http_client import HTTPClient
from utils.progress_bar import get_progress_default
from utils.read_line_by_line import read_line_by_line
from engine.cacheable import is_cacheable
from utils.file_writer import URLWriter

logger = get_logging()

async def safe_is_cacheable(url: str, client: HTTPClient, progress, task_id, semaphore: asyncio.Semaphore, headers: dict, follow_redirects: bool):
    """
    STEP 2: cek apakah mendapatkan response fresh dan mendukung cache
    """
    try:
        async with semaphore:
            return await is_cacheable(url, client, headers, follow_redirects)
    except Exception as e:
        logger.warning(f"[{url}] error: {e}")
    finally:
        progress.advance(task_id)

async def check_url(
    http_client: HTTPClient,
    concurrent_requests: int,
    config: dict,
    input_file: str,
    output_file: str
):
    """
    STEP 1: mendapatkan url line by line dan disimpan ke dalam list []
    STEP 3: hasil dari step 2 disimoan ke dalam file .txt
    """
    user_agent = config.get("user_agent", {})
    allow_redirects = config.get("allow_redirects", True)
    url_writer = URLWriter(output_file)
    
    urls = await read_line_by_line(input_file)
    if not urls:
        logger.warning(f"No content found in '{input_file}'")
        return []

    logger.info(f"Checking {len(urls)} urls..")
    
    semaphore = asyncio.Semaphore(concurrent_requests)
    progress = get_progress_default()
    errors_count = 0

    try:
        with progress:
            task_id = progress.add_task("[yellow]Checking process...", total=len(urls))
            tasks = [asyncio.create_task(safe_is_cacheable(url, http_client, progress, task_id, semaphore, user_agent, allow_redirects)) for url in urls]
            for future in asyncio.as_completed(tasks):
                result = await future
                if result:
                    await url_writer.add(without_param_fragment(result))
                else:
                    errors_count += 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")

    logger.info(f"Found {len(urls) - errors_count} cacheable urls. Error/Not Cacheable: {errors_count}")
    logger.info(f"Saved to '{output_file}'")

    return url_writer.get_count() > 0