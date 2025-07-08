### utils/http_client.py ###
import aiohttp
import urllib.parse
from aiohttp.resolver import AsyncResolver
from aiohttp import TCPConnector
from .logger import get_logging
from .cache_buster import cache_buster_value
from utils.console import console

class HTTPClient:
    logger = get_logging()

    def __init__(
        self,
        headers: dict = None,
        follow_redirects: bool = False,
        timeout: int = 10,
        limit: int = 100,
        nameservers: list[str] = None,
        cache_buster_name: str = "uhcxispoisoning"
    ):
        self.headers = headers or {}
        self.follow_redirects = follow_redirects
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.limit = limit
        self.nameservers = nameservers or ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        self.cache_buster_name = cache_buster_name
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # Use AsyncResolver with a public DNS server to improve DNS resolution reliability
            # and bypass issues with unresponsive local system DNS resolvers.
            resolver = AsyncResolver(nameservers=self.nameservers)
            connector = TCPConnector(
                limit=self.limit,
                resolver=resolver
            )
        
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.timeout,
                connector=connector
            )
        return self._session

    async def get(self, url: str, headers: dict = None, follow_redirects: bool = None, use_cache_buster: bool = False, return_headers: bool = False, return_content: bool = False) -> dict:
        """
        GET request (default):
            url                 -> string      (required)
            headers             -> dict {}     (options)
            follow_redirects    -> False       (options)
            use_cache_buster    -> False       (options)
            return_headers      -> False       (options)
            return_content      -> False       (options)
        """
        
        if not url.startswith(('http://','https://')):
            url = f"https://{url}"
            
        if use_cache_buster:
            buster_value = cache_buster_value()
            params = {self.cache_buster_name: buster_value}
            url_parts = list(urllib.parse.urlparse(url))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.parse.urlencode(query)
            url = urllib.parse.urlunparse(url_parts)

        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        current_follow_redirects = self.follow_redirects if follow_redirects is None else follow_redirects

        session = await self._get_session()
        try:
            self.logger.debug(f"GET {url}")
            async with session.get(
                url,
                headers=request_headers,
                allow_redirects=current_follow_redirects
            ) as response:
                result = {
                    "status": response.status,
                    "url": str(response.url),
                }
                if return_headers:
                    headers = response.headers
                    headers = {k.lower(): v for k, v in headers.items()}
                    result["headers"] = dict(headers)
    
                if return_content:
                    try:
                        content = await response.text()
                        result["content"] = content
                    except Exception as e:
                        self.logger.warning(f"Failed to read content {url}: {e}")
                        result["content"] = None
                else:
                    await response.release()
    
                return result
                
        except aiohttp.ClientError as e:
            self.logger.debug(f"GET {url} failed: {e}")
            raise

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self.logger.debug("aiohttp session closed.")