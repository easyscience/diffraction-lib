"""
General utilities and helpers for easydiffraction.
"""

import numpy as np
import pandas as pd
import pooch
import re
import os
from tabulate import tabulate
from typing import List, Optional

try:
    import IPython
    from IPython.display import (
        display,
        HTML
    )
except ImportError:
    IPython = None


def download_from_repository(file_name: str,
                             branch: str = 'master',
                             destination: str = 'data') -> None:
    """
    This function downloads a file from the EasyDiffraction repository
    on GitHub.
    :param file_name: The name of the file to download
    :param branch: The branch of the repository to download from
    :param destination: The destination folder to save the file
    :return: None
    """
    prefix = 'https://raw.githubusercontent.com'
    organisation = 'easyscience'
    repository = 'diffraction-lib'
    source = 'tutorials/data'
    url = f'{prefix}/{organisation}/{repository}/refs/heads/{branch}/{source}/{file_name}'
    pooch.retrieve(
        url=url,
        known_hash=None,
        fname=file_name,
        path=destination
    )


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


def is_pycharm() -> bool:
    """
    Determines if the current environment is PyCharm.

    Returns:
        bool: True if running inside PyCharm, False otherwise.
    """
    return os.environ.get("PYCHARM_HOSTED") == "1"


def render_table(columns_data,
                 columns_alignment,
                 columns_headers=None,
                 show_index=False,
                 display_handle=None):
    """
    Renders a table either as an HTML (in Jupyter Notebook) or ASCII (in terminal),
    with aligned columns.

    Args:
        columns_data (list): List of lists, where each inner list represents a row of data.
        columns_alignment (list): Corresponding text alignment for each column (e.g., 'left', 'center', 'right').
        columns_headers (list): List of column headers.
        show_index (bool): Whether to show the index column.
    """

    # Use pandas DataFrame for Jupyter Notebook rendering
    if is_notebook():
        # Create DataFrame
        if columns_headers is None:
            df = pd.DataFrame(columns_data)
            df.columns = range(df.shape[1])  # Ensure numeric column labels
            columns_headers = df.columns.tolist()
            skip_headers = True
        else:
            df = pd.DataFrame(columns_data,
                              columns=columns_headers)
            skip_headers = False

        # Force starting index from 1
        if show_index:
            df.index += 1

        # Replace None/NaN values with empty strings
        df.fillna("", inplace=True)

        # Formatters for data cell alignment and replacing None with empty string
        def make_formatter(align):
            return lambda x: f'<div style="text-align: {align};">{x}</div>'

        formatters = {
            col: make_formatter(align)
            for col, align in zip(columns_headers, columns_alignment)
        }

        # Convert DataFrame to HTML
        html = df.to_html(escape=False,
                          index=show_index,
                          formatters=formatters,
                          border=0,
                          header=not skip_headers)

        # Add inline CSS to align the entire table to the left and show border
        html = html.replace('<table class="dataframe">',
                            '<table class="dataframe" '
                            'style="'
                            'border-collapse: collapse; '
                            'border: 1px solid #515155; '
                            'margin-left: 0.5em;'
                            'margin-top: 0.5em;'
                            'margin-bottom: 1em;'
                            '">')

        # Manually apply text alignment to headers
        if not skip_headers:
            for col, align in zip(columns_headers, columns_alignment):
                html = html.replace(f'<th>{col}', f'<th style="text-align: {align};">{col}')

        # Display or update the table in Jupyter Notebook
        if display_handle is not None:
            display_handle.update(HTML(html))
        else:
            display(HTML(html))

    # Use tabulate for terminal rendering
    else:
        if columns_headers is None:
            columns_headers = []

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


def render_cif(cif_text, paragraph_title) -> None:
    """
    Display the CIF text as a formatted table in Jupyter Notebook or terminal.
    """
    # Split into lines and replace empty ones with a '&nbsp;'
    # (non-breaking space) to force empty lines to be rendered in
    # full height in the table. This is only needed in Jupyter Notebook.
    if is_notebook():
        lines: List[str] = [line if line.strip() else '&nbsp;' for line in cif_text.splitlines()]
    else:
        lines: List[str] = [line for line in cif_text.splitlines()]

    # Convert each line into a single-column format for table rendering
    columns: List[List[str]] = [[line] for line in lines]

    # Print title paragraph
    print(paragraph_title)

    # Render the table using left alignment and no headers
    render_table(columns_data=columns,
                 columns_alignment=["left"])


def tof_to_d(tof, offset, linear, quad):
    """
    Convert TOF to d-spacing using quadratic calibration.

    Parameters:
        tof (float or np.ndarray): Time-of-flight in microseconds.
        offset (float): Time offset.
        linear (float): Linear coefficient.
        quad (float): Quadratic coefficient.

    Returns:
        d (float or np.ndarray): d-spacing in Å.
    """
    A = quad
    B = linear
    C = offset - tof

    discriminant = B**2 - 4*A*C
    if np.any(discriminant < 0):
        raise ValueError("Negative discriminant: invalid calibration or TOF range")

    sqrt_discriminant = np.sqrt(discriminant)
    d = (-B + sqrt_discriminant) / (2*A)
    return d


def twotheta_to_d(twotheta, wavelength):
    """
    Convert 2-theta to d-spacing using Bragg's law.

    Parameters:
        twotheta (float or np.ndarray): 2-theta angle in degrees.
        wavelength (float): Wavelength in Å.

    Returns:
        d (float or np.ndarray): d-spacing in Å.
    """
    # Convert twotheta from degrees to radians
    theta_rad = np.radians(twotheta / 2)

    # Calculate d-spacing using Bragg's law
    d = wavelength / (2 * np.sin(theta_rad))

    return d


def get_value_from_xye_header(file_path, key):
    """
    Extracts a floating point value from the first line of the file, corresponding to the given key.

    Parameters:
        file_path (str): Path to the input file.
        key (str): The key to extract ('DIFC' or 'two_theta').

    Returns:
        float: The extracted value.

    Raises:
        ValueError: If the key is not found.
    """
    pattern = rf"{key}\s*=\s*([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)"

    with open(file_path, 'r') as f:
        first_line = f.readline()

    match = re.search(pattern, first_line)
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"{key} not found in the header.")