### main.py ###
import os
import json
import asyncio
import aiofiles
from utils.console import console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from utils.uhcx_icon import uhcx_icon
from utils.logger import get_logging
from utils.http_client import HTTPClient
from utils.progress_bar import get_progress
from utils.helpers import clear_terminal, save_json
from engine.cacheable import is_cacheable
#from engine.crawler import Crawler
#from engine.executor import Executor

logger = get_logging()

# Batasi jumlah request bersamaan (concurrent) agar tidak membebani koneksi
CONCURRENT_REQUESTS = 20
sem = asyncio.Semaphore(CONCURRENT_REQUESTS)

# Membaca daftar domain dari file teks
async def read_domains(file_path: str) -> set[str]:
    domains = []
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        # Buat file kosong dengan komentar jika belum ada
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write('# Add domains below\n')
        return []

    logger.info(f"Reading file '{file_path}'")
    async with aiofiles.open(file_path, mode='r') as f:
        async for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()

            if line:
                domains.append(line) # Use append for list directly

    # Use set for uniqueness then convert back to list
    return list(set(domains))

# Wrapper aman untuk is_cacheable (dengan semaphore)
async def safe_is_cacheable(domain: str, client: HTTPClient, progress: Progress, task_id):
    result = None
    try:
        async with sem:
            result = await is_cacheable(domain, client)
    except Exception as e:
        logger.warning(f"[{domain}] error: {e}")
    finally:
        # Pastikan progress selalu diperbarui, bahkan jika ada error
        progress.advance(task_id)
    return result

# Fungsi utama program
async def run_full_pipeline():
    try:
        # Bersihkan terminal dan tampilkan logo
        clear_terminal()
        uhcx_icon()
        
        # --- Tahap 1: Cek Cacheability Domain Awal ---
       
        # Baca domain dari file
        domain_path = "domains.txt"
        domains = await read_domains(domain_path)

        if not domains:
            logger.warning("No domains found. Please add domains to 'domains.txt'.")
            return

        total_domains = len(domains)
        logger.info(f"Checking {total_domains} domains...")

        # Inisialisasi HTTP client dengan header khusus
        client = HTTPClient(
            headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 UHCX/0.1"},
            follow_redirects=True
        )

        cacheable_base_urls = []
        errors_count = 0
        processed_count = 0

        # Gunakan progress bar dari rich untuk memantau proses
        progress = get_progress()

        try:
            with progress:
                task_id = progress.add_task("[yellow]Processing domains...", total=total_domains)
                tasks = []
                for domain in domains:
                    task = asyncio.create_task(safe_is_cacheable(domain, client, progress, task_id))
                    tasks.append(task)

                for future in asyncio.as_completed(tasks):
                    result = await future
                    processed_count += 1
                    if result:
                        cacheable_base_urls.append(result)
                    else:
                        errors_count += 1
            
            # Simpan hasil ke file JSON
            output_file_path = "data/meta/urls_cacheable.json"
            await save_json(output_file_path, cacheable_base_urls)

            logger.info(f"Done processing {total_domains} domains.")
            logger.info(f"Found {len(cacheable_base_urls)} cacheable domains.")
            logger.info(f"{errors_count} domains encountered errors or were not cacheable.")
            logger.info(f"Results saved to '{output_file_path}'")
        
        finally:
            # Tutup koneksi session HTTP
            await client.close()
            
        # --- Tahap 1: SELESAI ---
        
        # --- Tahap 2: Crawling URL dari Domain yang Cacheable ---
        
        # --- Tahap 2: SELESAI ---
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")

# Jalankan event loop utama
if __name__ == "__main__":
    asyncio.run(run_full_pipeline())