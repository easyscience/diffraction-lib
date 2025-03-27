from colorama import Fore, Style

WIDTH = 100
SYMBOL = "═"

def chapter(title: str) -> str:
    """Formats a chapter header with bold magenta text, uppercase, and padding."""
    full_title = f" {title.upper()} "
    pad_len = (WIDTH - len(full_title)) // 2
    padding = SYMBOL * pad_len
    line = f"{Fore.MAGENTA + Style.BRIGHT}{padding}{full_title}{padding}{Style.RESET_ALL}"
    if len(line) < WIDTH:
        line += SYMBOL
    return f'\n{line}'

def section(title: str) -> str:
    """Formats a section header with bold green text."""
    full_title = f'*** {title.upper()} ***'
    return f"\n{Fore.GREEN + Style.BRIGHT}{full_title}{Style.RESET_ALL}"

def paragraph(title: str) -> str:
    """Formats a subsection header with bold blue text while keeping quoted text unformatted."""
    import re
    parts = re.split(r"('.*?')", title)
    formatted = f"{Fore.BLUE + Style.BRIGHT}"
    for part in parts:
        if part.startswith("'") and part.endswith("'"):
            formatted += Style.RESET_ALL + part + Fore.BLUE + Style.BRIGHT
        else:
            formatted += part
    formatted += Style.RESET_ALL
    return f"\n{formatted}"

def error(title: str) -> str:
    """Formats an error message with red text."""
    return f"\n❌ {Fore.RED}Error:{Style.RESET_ALL}\n{title}"

def warning(title: str) -> str:
    """Formats a warning message with yellow text."""
    return f"\n⚠️ {Fore.YELLOW}Warning:{Style.RESET_ALL}\n{title}"

def info(title: str) -> str:
    """Formats an info message with cyan text."""
    return f"\nℹ️ {Fore.CYAN}Info:{Style.RESET_ALL}\n{title}"