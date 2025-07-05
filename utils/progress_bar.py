### utils/progress_bar.py ###

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from utils.console import console

def get_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("[{task.completed}/{task.total}]"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True 
    )
