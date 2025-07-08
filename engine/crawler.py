### engine/crawler.py ###
import asyncio
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from utils.http_client import HTTPClient
from utils.logger import get_logging
from utils.helpers import save_json
from utils.progress_bar import get_progress_dynamic
from utils.helpers import decode_double_encoding

logger = get_logging()

STATIC_EXTS = {
    ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".html", ".htm", ".xml", ".json",
    ".mp4", ".mp3", ".wav", ".ogg", ".flv", ".swf", ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".zip", ".rar", ".gz",
    ".tar", ".bmp", ".tiff", ".tif", ".webp", ".avif", ".mov", ".avi", ".mkv", ".webm"
}

def is_static(url: str) -> bool:
    parsed_url = urlparse(url)
    just_get_path = parsed_url.path
        
    return any(just_get_path.lower().endswith(ext) for ext in STATIC_EXTS)

def normalize_url(base: str, raw: str) -> str | None:
    try:
        absolute = urljoin(base, raw)
        decoded = decode_double_encoding(absolute)
        parsed = urlparse(decoded)
        
        clean_url = parsed._replace(fragment="").geturl()
        if not absolute.startswith(("http://", "https://")):
            return None
        return clean_url
    except:
        return None

async def extract_links(base_url: str, html: str, same_domain: bool, get_static_files: bool) -> set:
    soup = BeautifulSoup(html, "lxml")
    links = set()

    for tag in soup.find_all(["a", "link", "script", "img"]):
        attr = "href" if tag.name in ["a", "link"] else "src"
        raw = tag.get(attr)
        if not raw:
            continue

        url = normalize_url(base_url, raw)
        if not url:
            continue

        if same_domain and urlparse(url).netloc != urlparse(base_url).netloc:
            continue

        if not get_static_files and is_static(url):
            continue

        links.add(url)

    return links

async def crawl_url(
    semaphore: asyncio.Semaphore,
    http_client: HTTPClient,
    url: str,
    config: dict,
    seen_urls: set,
    queue: asyncio.Queue,
    progress,
    task_id: int,
    current_depth: int
):
    async with semaphore:
        crawler_conf = config.get("crawler_config", default={})
        user_agent = crawler_conf.get("user_agent", {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 UHCX-Crawler/0.1"})
        allow_redirects = crawler_conf.get("allow_redirects", False)
        same_domain = crawler_conf.get("same_domain", True)
        get_static_files = crawler_conf.get("get_static_files", False)
        max_deep = crawler_conf.get("max_deep", 1)

        try:
            response = await http_client.get(
                url,
                headers=user_agent,
                follow_redirects=allow_redirects,
                return_content=True,
                return_headers=False,
                use_cache_buster=False
            )
            html = response.get("content", "")
            links = await extract_links(url, html, same_domain, get_static_files)

            new_links = links - seen_urls
            seen_urls.update(new_links)

            if current_depth < max_deep:
                for link in new_links:
                    await queue.put((link, current_depth + 1))

            logger.info(f"[Depth {current_depth}] {url} → {len(links)} links")
        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
        finally:
            progress.update(task_id, advance=1)

async def crawler(http_client: HTTPClient, start_urls: list, config: dict) -> list:
    global_conf = config.get("global_config", default={})
    crawler_conf = config.get("crawler_config", default={})
    
    max_concurrent = global_conf.get("concurrent", 20)
    output_file = global_conf.get("indexed_url_file_path", "data/meta/urls_crawled.json")
    max_deep = crawler_conf.get("max_deep", 1)

    semaphore = asyncio.Semaphore(max_concurrent)
    progress = get_progress_dynamic()
    queue = asyncio.Queue()
    seen_urls = set(start_urls)

    for url in start_urls:
        await queue.put((url, 1))

    logger.info(f"Started deep crawling on {len(start_urls)} domains, max depth {max_deep}...")

    with progress:
        task_id = progress.add_task("[yellow]Crawling...")

        workers = []

        async def worker():
            while True:
                try:
                    url, depth = await queue.get()
                except asyncio.CancelledError:
                    break
                await crawl_url(semaphore, http_client, url, config, seen_urls, queue, progress, task_id, depth)
                queue.task_done()

        for _ in range(max_concurrent):
            workers.append(asyncio.create_task(worker()))

        await queue.join()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    logger.info(f"Total unique URLs crawled: {len(seen_urls)}")
    await save_json(output_file, sorted(seen_urls))
    return sorted(seen_urls)
