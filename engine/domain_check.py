### engine/domain_check.py ###
import os
import aiofiles
import asyncio
from utils.logger import get_logging
from utils.helpers import save_json
from utils.http_client import HTTPClient
from utils.progress_bar import get_progress_default
from engine.cacheable import is_cacheable

logger = get_logging()

async def read_domains(file_path: str) -> list[str]:
    domains = []
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write('# Add domains below\n')
        return []
    
    async with aiofiles.open(file_path, mode='r') as f:
        async for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            domains.append(line)

    return list(set(domains))

async def safe_is_cacheable(domain: str, client: HTTPClient, progress, task_id, semaphore: asyncio.Semaphore, headers: dict, follow_redirects: bool):
    try:
        async with semaphore:
            return await is_cacheable(domain, client, headers, follow_redirects)
    except Exception as e:
        logger.warning(f"[{domain}] error: {e}")
    finally:
        progress.advance(task_id)

async def domain_check(http_client: HTTPClient, config: dict) -> list[str]:
    global_config = config.get("global_config", default={})
    domain_check_config = config.get("domain-check_config", default={})
    
    
    CONCURRENT_REQUESTS = global_config.get("concurrent", 20)
    domain_path = global_config.get("domain_list_file_path", "domains.txt")
    output_file = global_config.get("cacheable_url_file_path", "data/meta/urls_cacheable.json")
    
    user_agent = domain_check_config.get("user_agent", {})
    allow_redirects = domain_check_config.get("allow_redirects", True)
    
    domains = await read_domains(domain_path)
    if not domains:
        logger.warning(f"No domains found. Please add domains to '{domain_path}'.")
        return []

    logger.info(f"Checking {len(domains)} domains..")
    
    progress = get_progress_default()
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    cacheable_base_urls = []
    errors_count = 0

    try:
        with progress:
            task_id = progress.add_task("[yellow]Processing domains...", total=len(domains))
            tasks = [asyncio.create_task(safe_is_cacheable(domain, http_client, progress, task_id, semaphore, user_agent, allow_redirects)) for domain in domains]
            for future in asyncio.as_completed(tasks):
                result = await future
                if result:
                    cacheable_base_urls.append(result)
                else:
                    errors_count += 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")

    cacheable_base_urls = sorted(set(cacheable_base_urls))
    await save_json(output_file, cacheable_base_urls)
    
    logger.info(f"Found {len(cacheable_base_urls)} cacheable domains. Error/Not Cacheable: {errors_count}")
    logger.info(f"Saved to '{output_file}'")

    return cacheable_base_urls
