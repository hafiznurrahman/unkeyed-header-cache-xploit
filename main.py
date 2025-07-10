### main.py ###
import os
import sys
import asyncio
from utils.console import console_no_record
from utils.helpers import load_json
from utils.logger import get_logging
from utils.uhcx_icon import uhcx_icon
from utils.helpers import clear_terminal
from utils.http_client import HTTPClient
from utils.config_manager import AsyncConfigManager
from engine.check_url import check_url
from engine.crawler import crawler
from engine.executor import executor

logger = get_logging()

async def main():
    # ——— load configurasi ———
    config_settings = await AsyncConfigManager.get_instance("config/settings.yaml")
    config_payloads = await AsyncConfigManager.get_instance("config/payloads.yaml")
    
    # ——— configurasi global ———
    global_config = config_settings.get("global_config", default={})
    concurrent = global_config.get("concurrent", 50)
    domain_list_file_path = global_config.get("domain_list_file_path","domains.txt")
    cacheable_domain_file_path = global_config.get("cacheable_domain_file_path","data/workflow/domains_cacheable.txt")
    indexed_url_file_path = global_config.get("indexed_url_file_path", "data/workflow/urls_crawled.txt")
    cacheable_url_file_path = global_config.get("cacheable_url_file_path","data/workflow/domains_cacheable.txt")
    assessment_result_file_path = global_config.get("assessment_result_file_path", "data/workflow/vulnerable_targets.txt")
    
    # ——— configurasi http client ———
    http_client_config = config_settings.get("http-client_config", default={})
    initial_allow_redirect = http_client_config.get("allow_redirects", False)
    initial_connector_limit = http_client_config.get("connector_limit", 100)
    initial_timeout = http_client_config.get("timeout", 10)
    initial_user_agent = http_client_config.get("user_agent", {})
    initial_dns_nameservers = http_client_config.get("dns_nameservers", [])
    initial_cache_buster_name = http_client_config.get("cache_buster_name", "uhcxispoisoning")
    
    # ——— configurasi domain check ———
    domain_check_config = config_settings.get("domain-check_config", default={})
    
    # ——— configurasi crawler ———
    crawler_config = config_settings.get("crawler_config", default={})
    
    # ——— configurasi executor ———
    executor_config = config_settings.get("executor_config", default={})
    
    # ——— inisialisasi http client secara global ———
    global_http_client = HTTPClient(
        headers=initial_user_agent,
        follow_redirects=initial_allow_redirect,
        timeout=initial_timeout,
        limit=initial_connector_limit,
        nameservers=initial_dns_nameservers,
        cache_buster_name=initial_cache_buster_name
    )
    
    try:
        # ——— Bersihkan terminal dan tampilkan logo ———
        clear_terminal()
        uhcx_icon()
        
        # hapus semua file .txt di dalam folder
        folder_path = "data/workflow/"
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                os.remove(os.path.join(folder_path, filename))

        # --- Tahap 1: Cek Cacheability Domain Awal ---
        console_no_record.print("[bold red][+] Checking Domains...  [/]\n")
        phase_1 = await check_url(
            global_http_client,
            concurrent,
            domain_check_config,
            domain_list_file_path,
            cacheable_domain_file_path
        )
        
        # --- Tahap 2: Crawling URL dari Domain yang Cacheable ---
        if phase_1:
            console_no_record.print("\n[bold red][+] Crawling Domains...  [/]\n")
            phase_2 = await crawler(
                global_http_client,
                concurrent,
                crawler_config,
                cacheable_domain_file_path, 
                indexed_url_file_path
            )
            
        # --- Tahap 3: Check cacheability urls dari hasil crawling ---
            if phase_2:
                console_no_record.print("[bold red][+] Checking Urls...  [/]\n")
                phase_3 = await check_url(
                    global_http_client,
                    concurrent,
                    domain_check_config,
                    indexed_url_file_path,
                    cacheable_url_file_path
                )
            
        # --- Tahap 4: Eksekusi URL dari hasil crawling ---
                if phase_3:
                    console_no_record.print("\n[bold red][+] Exploiting URLs...  [/]\n")
                    finish = await executor(
                        global_http_client,
                        concurrent,
                        config_payloads,
                        executor_config,
                        cacheable_url_file_path,
                        assessment_result_file_path
                    )
        
    except asyncio.CancelledError:
        print() # new line
        logger.warning("Program terminated by user (CTRL + C).")
        raise
    except Exception as e:
        logger.exception(f"Error during execution: {e}")
    finally:
        await global_http_client.close()

# ——— Jalankan event loop utama ———
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt detected. Exiting gracefully.")
    except Exception as e:
        logger.error(f"An unexpected error has occurred: {e}", exc_info=True)