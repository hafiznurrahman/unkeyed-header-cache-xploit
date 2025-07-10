import re
import asyncio
import aiofiles
from bs4 import BeautifulSoup
from utils.console import console_record
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from utils.write_report import safe_write_report

async def assessment(status: int, url: str, payload: dict, header_response_2: dict, body_response_2: str, assessment_result_file_path: str) -> dict:
    """
    Menilai apakah URL rentan terhadap cache poisoning berdasarkan refleksi payload di body atau header.
    """
    result = {
        "status": status,
        "url": url,
        "payload": payload,
        "reflected": False,
        "header": header_response_2,
        "poc": []
    }

    # Convert body HTML to string
    html_str = str(BeautifulSoup(body_response_2, "lxml"))

    found_poc = set()

    for key, val in payload.items():
        if not val:
            continue

        # Cek refleksi di BODY
        for match in re.finditer(rf".*{re.escape(val)}.*", html_str):
            line = match.group().strip()
            if line:
                found_poc.add(line)

        # Cek refleksi di HEADER
        for h_key, h_val in header_response_2.items():
            if isinstance(h_val, str) and val in h_val:
                found_poc.add(f"[header] {h_key}: {h_val}")

    if found_poc:
        result["reflected"] = True
        result["poc"] = list(found_poc)

    if not result.get("reflected"):
        return 
    
    status = result["status"]
    url = result["url"]
    payload = result["payload"]
    header = result["header"]
    poc = result["poc"]
    
    console_record.print(f"\n[bold blue]STATUS   :[/bold blue] {status}")
    console_record.print(f"[bold blue]URL      :[/bold blue] {url}")
    console_record.print(f"[bold blue]Reflected:[/bold blue] [bold green]True[/bold green]")
    console_record.print(f"[bold blue]Payload  :[/bold blue] ", end="")
    console_record.print_json(data=payload)
    console_record.print(f"[bold blue]header   : ", end="")
    console_record.print_json(data=header)

    table = Table(title="Reflected Payload (Proof of Concept)", show_lines=True, header_style="bold magenta")
    table.add_column("No.", style="cyan", width=5)
    table.add_column("Location", style="white")

    for idx, line in enumerate(poc, start=1):
        highlighted_line = Text(line)
        for val in payload.values():
            if val in line:
                highlighted_line.highlight_words([val], style="bold red")
        table.add_row(str(idx), highlighted_line)

    console_record.print(table)
    await safe_write_report(assessment_result_file_path, console_record.export_text())
