"""
General utilities and helpers for easydiffraction.
"""

import os
import pandas as pd
import urllib.request

from pathlib import Path
from tabulate import tabulate

try:
    import IPython
    from IPython.display import (
        display,
        HTML
    )
except ImportError:
    IPython = None


def download_from_repository(url: str,
                             save_path: str = ".",
                             overwrite: bool = False) -> str:
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
    if IPython is None:
        return False

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


def ensure_dir(directory: str) -> str:
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


def render_table(columns_headers,
                 columns_alignment,
                 columns_data,
                 show_index=False):
    """
    Renders a table either as an HTML (in Jupyter Notebook) or ASCII (in terminal),
    with aligned columns.

    Args:
        columns_headers (list): List of column headers.
        columns_alignment (list): Corresponding text alignment for each column (e.g., 'left', 'center', 'right').
        columns_data (list): List of row data.
        show_index (bool): Whether to show the index column.
    """

    # Use pandas DataFrame for Jupyter Notebook rendering
    if is_notebook():
        # Create DataFrame
        df = pd.DataFrame(columns_data,
                          columns=columns_headers)

        # Force starting index from 1
        if show_index:
            df.index += 1

        # Formatters for data cell alignment
        formatters = {
            col: (lambda align: (lambda x: f'<div style="text-align: {align};">{x}</div>'))(align)
            for col, align in zip(columns_headers, columns_alignment)
        }

        # Convert DataFrame to HTML
        html = df.to_html(escape=False,
                          index=show_index,
                          formatters=formatters,
                          border=0)

        # Add inline CSS to align the entire table to the left and show border
        html = html.replace('<table class="dataframe">',
                            '<table class="dataframe" '
                            'style="'
                            'border-collapse: collapse; '
                            'border: 1px solid #515155; '
                            'margin-left: 0;'
                            '">')

        # Manually apply text alignment to headers
        for col, align in zip(columns_headers, columns_alignment):
            html = html.replace(f'<th>{col}', f'<th style="text-align: {align};">{col}')

        display(HTML(html))

    # Use tabulate for terminal rendering
    else:
        indices = show_index
        if show_index:
            # Force starting index from 1
            indices = range(1, len(columns_data) + 1)

        table = tabulate(
            columns_data,
            headers=columns_headers,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=indices
        )

        print(table)
