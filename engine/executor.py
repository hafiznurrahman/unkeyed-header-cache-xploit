import asyncio
from utils.logger import get_logging
from utils.http_client import HTTPClient
from utils.console import console_record
from engine.assessment import assessment
from engine.cacheable import is_cacheable
from utils.write_report import safe_write_report
from utils.progress_bar import get_progress_default
from utils.read_line_by_line import read_line_by_line
from utils.inject_placeholder import inject_placeholder
from utils.helpers import without_param_fragment

logger = get_logging()

async def executor(
    http_client: HTTPClient,
    concurrent: int,
    payloads: dict,
    executor_conf: dict,
    input_file: str,
    output_file: str
):
    try:
        single_payload_conf = payloads.get("single_header_dinamic", default={})
        multiple_payload_conf = payloads.get("multiple_header", default={})

        user_agent = executor_conf.get("user_agent", {})

        semaphore = asyncio.Semaphore(concurrent)
        progress = get_progress_default()
        result_set = await read_line_by_line(input_file)

        async def handle_assessment(url: str, payload: dict):
            async with semaphore:
                try:
                    base_url = without_param_fragment(url)
                    response = await http_client.get(
                        base_url,
                        headers=payload,
                        follow_redirects=False,
                        return_content=True,
                        return_headers=True,
                        use_cache_buster=True
                    )
                    res_status = response["status"]
                    res_url = response["url"]
                    res_headers = response["headers"]
                    res_content = response["content"]
                    
                    headers_to_truncate = [
                        'content-security-policy',
                        'x-webkit-csp',
                        'x-content-security-policy',
                        'permissions-policy',
                        'feature-policy'
                    ]
                
                    for h in headers_to_truncate:
                        if h in res_headers:
                            res_headers[h] = '...(truncated)'

                    await assessment(res_status, res_url, payload, res_headers, res_content, output_file)

                except Exception as e:
                    logger.debug(f"[Assessment Error] {url} {payload} -> {e}")

        assess_tasks = []
        console_record.rule("[bold cyan]🧪 Cache Poisoning Assessment Result")
        for url in result_set:
            for header in single_payload_conf:
                try:
                    placeholder = inject_placeholder(header, executor_conf)
                    payload = {header["header"]: placeholder["value"]}
                    assess_tasks.append(asyncio.create_task(handle_assessment(url, payload)))
                except Exception as e:
                    logger.debug(f"[Payload Injection Error] {url} {header} -> {e}")

        await asyncio.gather(*assess_tasks)
        console_record.rule("[bold cyan]End of Report")
        await safe_write_report(output_file, console_record.export_text())
        logger.info(f"Saved to '{output_file}'")
        
    except Exception as e:
        logger.error(f"[Executor Fatal Error] -> {e}")
