"""
General utilities and helpers for easydiffraction.
"""

import os
import urllib.request
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
