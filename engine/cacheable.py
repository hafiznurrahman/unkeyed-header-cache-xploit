### engine/cacheable.py ###
import re
import pytz
import asyncio
from utils.http_client import HTTPClient
from utils.logger import get_logging
from datetime import datetime
from dateutil import parser
from urllib.parse import urlparse, urlunparse
from utils.helpers import decode_double_encoding

logger = get_logging()

CACHE_CRITERIA = {
    "positive": {
        "cache_control_public": {"keywords": ["public"], "negate_keywords": ["no-store", "private", "no-cache", "max-age=0"], "points": 2, "header": "cache-control"},
        "cdn_cache_control_public": {"keywords": ["public"], "negate_keywords": ["no-store", "private", "no-cache", "max-age=0"], "points": 2, "header": "cdn-cache-control"},
        "cache_control_max_age_positive": {"regex": r"max-age=(\d+)", "min_value": 1, "points": 1, "header": "cache-control"},
        "cache_control_s_maxage_positive": {"regex": r"s-maxage=(\d+)", "min_value": 1, "points": 1, "header": "cache-control"},
        "age_zero": {"value": 0, "points": 2, "header": "age"},
        "expires_future": {"points": 1}, # Logika diimplementasikan secara terpisah
        "cache_miss_status": {"keywords": ["miss", "tcp_miss"], "points": 1, "headers": ['cf-cache-status', 'x-cache', 'x-proxy-cache', 'cdn-cache', 'server-timing', 'x-drupal-cache', 'surrogate-control', 'akamai-grn', 'x-fastly-request-id', 'x-varnish']},
    },
    "negative": {
        "cache_control_no_cache": {"keywords": ["no-store", "private", "no-cache"], "points": -12, "header": "cache-control"},
        "cdn_cache_control_no_cache": {"keywords": ["no-store", "private", "no-cache"], "points": -12, "header": "cdn-cache-control"},
        "cache_control_max_age_zero": {"regex": r"max-age=(\d+)", "value": 0, "points": -8, "header": "cache-control"},
        "cache_control_s_maxage_zero": {"regex": r"s-maxage=(\d+)", "value": 0, "points": -2, "header": "cache-control"},
        "pragma_no_cache": {"keywords": ["no-cache"], "points": -4},
        "age_non_zero": {"min_value": 1, "points": -4, "header": "age"},
        "expires_past": {"points": -4}, # Logika diimplementasikan secara terpisah
        "cache_hit_status": {"keywords": ["dynamic", "immutable", "bypass", "hit", "tcp_hit"], "points": -20, "headers": ['cf-cache-status', 'x-cache', 'x-proxy-cache', 'cdn-cache', 'server-timing', 'x-drupal-cache', 'surrogate-control', 'akamai-grn', 'x-fastly-request-id', 'x-varnish']},
    }
}

async def calculate_cacheability_score(response_headers: dict) -> tuple[int, list[str]]:
    """
    Menghitung skor cacheability berdasarkan header respons.
    Mengembalikan skor total dari point positive dan negative.
    """
    points = 0
    reasons = []

    # Truncate potentially very long headers for logging/storage early
    headers_to_truncate = [
        'content-security-policy',
        'x-webkit-csp',
        'x-content-security-policy',
        'permissions-policy',
        'feature-policy'
    ]

    for h in headers_to_truncate:
        if h in response_headers:
            response_headers[h] = '...(truncated)'


    for category in ["positive", "negative"]:
        for name, criteria in CACHE_CRITERIA[category].items():
            header_value = ""
            
            # Mendapatkan nilai header yang relevan
            if "header" in criteria:
                header_value = response_headers.get(criteria["header"], '').lower()
            if "headers" in criteria: # Untuk kasus multiple headers (e.g., cache_hit_status)
                for h_name in criteria["headers"]:
                    if h_name in response_headers:
                        header_value = response_headers.get(h_name, '').lower()
                        # Jika ada match, tidak perlu cek header lain di group yang sama
                        if "keywords" in criteria and any(k in header_value for k in criteria["keywords"]):
                            break
                        if "value" in criteria or "min_value" in criteria or "regex" in criteria:
                            break # Assume we found a relevant header for numerical/regex checks
                
            # Logika berdasarkan jenis kriteria
            if "keywords" in criteria:
                # Kriteria berbasis kata kunci (misal: cache-control public, no-cache, pragma)
                if "negate_keywords" in criteria: # Untuk 'cache_control_public'
                    if all(k in header_value for k in criteria["keywords"]) and \
                       not any(nk in header_value for nk in criteria["negate_keywords"]):
                        points += criteria["points"]
                        reasons.append(f"[{category}] +{criteria['points']} for {name} ({criteria.get('header', 'Multiple Headers')}): {header_value}")
                else: # Untuk kriteria keyword lainnya (no-cache, miss, hit)
                    if any(k in header_value for k in criteria["keywords"]):
                        points += criteria["points"]
                        reasons.append(f"[{category}] {criteria['points']} for {name} ({criteria.get('header', 'Multiple Headers')}): {header_value}")

            if "regex" in criteria:
                # Kriteria berbasis regex (misal: max-age, s-maxage)
                if (match := re.search(criteria["regex"], header_value)):
                    try:
                        num_value = int(match.group(1))
                        if "min_value" in criteria and num_value >= criteria["min_value"]:
                            points += criteria["points"]
                            reasons.append(f"[{category}] +{criteria['points']} for {name} ({criteria.get('header', 'Cache-Control')}): {match.group(0)}")
                        if "value" in criteria and num_value == criteria["value"]:
                            points += criteria["points"]
                            reasons.append(f"[{category}] {criteria['points']} for {name} ({criteria.get('header', 'Cache-Control')}): {match.group(0)}")
                    except ValueError:
                        logger.debug(f"Invalid numeric value for {name} header: {match.group(1)}")

            if name in ["age_zero", "age_non_zero"]:
                # Kriteria berbasis nilai numerik (misal: Age)
                age_header_val = response_headers.get('age')
                if age_header_val:
                    try:
                        age_val = int(age_header_val)
                        if name == "age_zero" and age_val == criteria["value"]:
                            points += criteria["points"]
                            reasons.append(f"[{category}] +{criteria['points']} for Age: {age_header_val} (zero)")
                        if name == "age_non_zero" and age_val >= criteria["min_value"]:
                            points += criteria["points"]
                            reasons.append(f"[{category}] {criteria['points']} for Age: {age_header_val} (non-zero)")
                    except ValueError:
                        logger.debug(f"Invalid Age header value: {age_header_val}")
            
            if name in ["expires_future", "expires_past"]:
                # Kriteria berbasis tanggal (misal: Expires)
                expires_header = response_headers.get('expires')
                if expires_header:
                    try:
                        utc_timezone = pytz.utc
                        parsed_expires = parser.parse(expires_header).astimezone(utc_timezone)
                        current_time_utc = datetime.now(utc_timezone)
                        
                        if name == "expires_future" and parsed_expires > current_time_utc:
                            points += criteria["points"]
                            reasons.append(f"[{category}] +{criteria['points']} for Expires: {expires_header} (in future)")
                        if name == "expires_past" and parsed_expires < current_time_utc:
                            points += criteria["points"]
                            reasons.append(f"[{category}] {criteria['points']} for Expires: {expires_header} (in past)")
                    except parser.ParserError:
                        logger.debug(f"Could not parse Expires header: {expires_header}")

    return points, reasons

async def is_cacheable(url: str, client: HTTPClient, headers: dict, allow_redirect: bool) -> str | None:

    try:
        result = await client.get(
            url,
            headers=headers,
            follow_redirects=allow_redirect,
            use_cache_buster=True,
            return_headers=True,
            return_content=False
        )

        response_headers = result.get("headers", {})
        
        # Menggunakan fungsi terpisah untuk menghitung skor
        total_points, reasons = await calculate_cacheability_score(response_headers)
        
        base_url = decode_double_encoding(result['url'])
        
        # Logging hasil penilaian untuk debugging
        logger.debug(f"URL: {base_url}, Total Points: {total_points}, Reasons: {reasons}")

        # Ambang batas kelayakan cache
        CACHEABLE_THRESHOLD = 2 

        if total_points >= CACHEABLE_THRESHOLD:
            logger.info(f"[blue]{base_url}[/] -> [bold yellow]CACHEABLE[/] - SCORE: {total_points}")
            return base_url
        else:
            logger.info(f"[blue]{base_url}[/] -> NOT CACHEABLE - SCORE: {total_points}")
            return None

    except asyncio.TimeoutError:
        logger.error(f"Timeout checking cacheability for '{url}'")
        return None
    except Exception as e:
        logger.error(f"Error checking cacheable for '{url}': {e}")
        return None