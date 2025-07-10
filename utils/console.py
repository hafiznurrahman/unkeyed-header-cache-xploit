from rich.console import Console
from rich.theme import Theme

theme = Theme({
        "info": "bold dim cyan",
        "warning": "bold magenta",
        "error": "bold red",
        "critical": "bold white on red",
        "debug": "bold green"
    })

console_record = Console(theme=theme, record=True)
console_no_record = Console(theme=theme)