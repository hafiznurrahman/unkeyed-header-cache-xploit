### main.py ###
import sys
import asyncio
from utils.console import console
from utils.helpers import load_json
from utils.logger import get_logging
from utils.uhcx_icon import uhcx_icon
from utils.helpers import clear_terminal
from utils.http_client import HTTPClient
from utils.config_manager import AsyncConfigManager
from engine.domain_check import domain_check
from engine.crawler import crawler
#from engine.executor import executor

logger = get_logging()

async def main():
    config = await AsyncConfigManager.get_instance("config/settings.yaml")
    http_client_config = config.get("http-client_config", default={})
    
    initial_allow_redirect = http_client_config.get("allow_redirects", False)
    initial_connector_limit = http_client_config.get("connector_limit", 100)
    initial_timeout = http_client_config.get("timeout", 10)
    initial_user_agent = http_client_config.get("user_agent", {})
    initial_dns_nameservers = http_client_config.get("dns_nameservers", [])
    initial_cache_buster_name = http_client_config.get("cache_buster_name", "uhcxispoisoning")
    
    global_http_client = HTTPClient(
        headers=initial_user_agent,
        follow_redirects=initial_allow_redirect,
        timeout=initial_timeout,
        limit=initial_connector_limit,
        nameservers=initial_dns_nameservers,
        cache_buster_name=initial_cache_buster_name
    )
    
    try:
        #await global_http_client._get_session()
        # Bersihkan terminal dan tampilkan logo
        clear_terminal()
        uhcx_icon()
        
        # --- Tahap 1: Cek Cacheability Domain Awal ---
        console.print("[bold red][+] Checking Domains...  [/]\n")
        cacheable_base_urls = await domain_check(global_http_client, config)
        
        # --- Tahap 2: Crawling URL dari Domain yang Cacheable ---
        if len(cacheable_base_urls):
            console.print("\n[bold red][+] Crawling Domains...  [/]\n")
            urls_crawled = await crawler(global_http_client, cacheable_base_urls, config)
            
        # --- Tahap 3: Eksekusi URL dari hasil crawling ---.
        console.print("\n[bold red][+] Exploiting URLs...  [/]\n")
        
    except asyncio.CancelledError:
        logger.warning("Program terminated by user (CTRL + C).")
        raise
    except Exception as e:
        logger.exception(f"Error during execution: {e}")
    finally:
        await global_http_client.close()

# Jalankan event loop utama
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt detected. Exiting gracefully.")
    except Exception as e:
        logger.error(f"An unexpected error has occurred: {e}", exc_info=True)