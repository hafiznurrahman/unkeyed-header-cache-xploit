### utils/uhcx_icon.py ###
from utils.console import console_no_record
from rich.text import Text

icon_art = """
      ▄    ▄  █ ▄█▄       ▄  
       █  █   █ █▀ ▀▄ ▀▄   █ 
    █   █ ██▀▀█ █   ▀   █ ▀  
    █   █ █   █ █▄  ▄▀ ▄ █   
    █▄ ▄█    █  ▀███▀ █   ▀▄ 
     ▀▀▀    ▀          ▀     UHCX v0.1
"""

def uhcx_icon():
    colored_icon = Text(icon_art, style="bold red")
    console_no_record.print(colored_icon)