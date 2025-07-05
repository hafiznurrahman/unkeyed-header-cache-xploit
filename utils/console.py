from rich.console import Console
from rich.theme import Theme

console = Console(theme=Theme({
        "info": "bold dim cyan",
        "warning": "bold magenta",
        "error": "bold red",
        "critical": "bold white on red",
        "debug": "bold green"
    }))