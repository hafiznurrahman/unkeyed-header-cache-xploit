import asyncio
from utils.http_client import HTTPClient
from utils.progress_bar import get_progress_default
from utils.helpers import decode_double_encoding, load_json
from engine.cacheable import is_cacheable
from utils.logger import get_logging

logger = get_logging()

async def executor(http_client: HTTPClient, list_urls: list, config: dict, payloads: dict):
    global_conf = config.get("global_config", default={})
    executor_conf = config.get("executor_config", default={})
    single_payload_conf = payloads.get("single_header", default={})
    multiple_payload_conf = payloads.get("multiple_header", default={})
    
    max_concurrent = global_conf.get("concurrent", 50)
    indexed_url_file_path = global_conf.get("indexed_url_file_path", "data/meta/urls_crawled.json")
    base_dir = global_conf.get("target_result_directory_path", "data/results")
    user_agent = executor_conf.get("user_agent", {})
    allow_redirects = False

    semaphore = asyncio.Semaphore(max_concurrent)
    progress = get_progress_default()
    
    result_set = set()

    async def handle_url(url: str):
        async with semaphore:
            try:
                is_cacheable_result = await is_cacheable(url, http_client, user_agent, allow_redirects)
                return is_cacheable_result
            except Exception as e:
                logger.warning(f"Failed to check cacheable: {url} -> {e}")
                return None

    with progress:
        task_id = progress.add_task("[yellow]Checking cacheable URLs...", total=len(list_urls))
        tasks = [
            asyncio.create_task(handle_url(url)) for url in list_urls
        ]

        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                result_set.add(result)
            progress.update(task_id, advance=1)

    # TODO: lanjutkan proses dengan result_set seperti simpan hasil, lanjut exploit, dsb.
    return list(result_set)
