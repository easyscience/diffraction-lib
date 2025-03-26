"""
General utilities and helpers for easydiffraction.
"""

import os
import urllib.request
from colorama import Fore, Style
from pathlib import Path


def download_from_repository(url: str, save_path: str = ".", overwrite: bool = False):
    """
    Downloads a file from a remote repository and saves it locally.

    Args:
        url (str): URL to the file to be downloaded.
        save_path (str): Local directory or file path where the file will be saved.
        overwrite (bool): If True, overwrites the existing file.

    Returns:
        str: Full path to the downloaded file.
    """
    save_path = Path(save_path)

    # Determine if save_path is a directory or file
    if save_path.is_dir():
        filename = os.path.basename(url)
        file_path = save_path / filename
    else:
        file_path = save_path

    if file_path.exists() and not overwrite:
        print(f"[INFO] File already exists: {file_path}. Use overwrite=True to replace it.")
        return str(file_path)

    try:
        print(f"[INFO] Downloading from {url} to {file_path}")
        urllib.request.urlretrieve(url, file_path)
        print(f"[INFO] Download complete: {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to download {url}. Error: {e}")
        raise

    return str(file_path)


def is_notebook() -> bool:
    """
    Determines if the current environment is a Jupyter Notebook.

    Returns:
        bool: True if running inside a Jupyter Notebook, False otherwise.
    """
    try:
        shell = get_ipython().__class__.__name__  # noqa: F821
        if shell == "ZMQInteractiveShell":
            return True   # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (unlikely)
    except NameError:
        return False  # Probably standard Python interpreter


def ensure_dir(directory: str):
    """
    Ensures that a directory exists. Creates it if it doesn't exist.

    Args:
        directory (str): Path to the directory to ensure.

    Returns:
        str: Absolute path of the ensured directory.
    """
    path = Path(directory)
    if not path.exists():
        print(f"[INFO] Creating directory: {directory}")
        path.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())


def human_readable_size(size_bytes: int, decimal_places: int = 2) -> str:
    """
    Converts a file size in bytes to a human-readable string.

    Args:
        size_bytes (int): The size in bytes.
        decimal_places (int): Number of decimal places for formatted output.

    Returns:
        str: Human-readable file size (e.g., '1.23 MB').
    """
    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    index = int(min(len(size_name) - 1, (size_bytes.bit_length() - 1) / 10))
    power = 1024 ** index
    size = size_bytes / power

    return f"{size:.{decimal_places}f} {size_name[index]}"


def list_files(directory: str, extension: str = "", recursive: bool = False):
    """
    Lists files in a directory with an optional extension filter.

    Args:
        directory (str): Directory path to search.
        extension (str): Optional file extension to filter by (e.g., '.cif').
        recursive (bool): Whether to search directories recursively.

    Returns:
        list[str]: List of file paths matching the criteria.
    """
    path = Path(directory)
    if not path.is_dir():
        raise ValueError(f"{directory} is not a valid directory.")

    if recursive:
        files = path.rglob(f"*{extension}")
    else:
        files = path.glob(f"*{extension}")

    return [str(file.resolve()) for file in files if file.is_file()]

def chapter(title: str) -> str:
    """
    Formats a chapter header with bold blue text, uppercase, and padded with '-' to 80 characters.
    """
    width = 100
    symbol = "═"
    full_title = f" {title.upper()} "
    pad_len = (width - len(full_title)) // 2
    padding = symbol * pad_len
    line = f"{Fore.MAGENTA + Style.BRIGHT}{padding}{full_title}{padding}{Style.RESET_ALL}"
    if len(line) < width:
        line += symbol
    return f'\n{line}'

def section(title: str) -> str:
    """
    Formats a section header with bold green text.
    """
    full_title = f'*** {title.upper()} ***'
    colorized = f"{Fore.GREEN + Style.BRIGHT}{full_title}{Style.RESET_ALL}"
    return f"\n{colorized}"

def paragraph(title: str) -> str:
    """
    Formats a subsection header with bold blue text.
    If input text includes quoted content, the quoted part is not colorized.
    """
    import re

    # Split around quoted text
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
    """
    Formats an error message with red text.
    """
    return f"\n❌️ {Fore.RED}Error:{Style.RESET_ALL}\n{title}"

def warning(title: str) -> str:
    """
    Formats a warning message with yellow text.
    """
    return f"\n⚠️ {Fore.YELLOW}Warning:{Style.RESET_ALL}\n{title}"

def info(title: str) -> str:
    """
    Formats a warning message with yellow text.
    """
    return f"\nℹ️️ {Fore.CYAN}Info:{Style.RESET_ALL}\n{title}"
