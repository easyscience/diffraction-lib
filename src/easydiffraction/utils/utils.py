"""
General utilities and helpers for easydiffraction.
"""

import numpy as np
import pandas as pd
import pooch
from tabulate import tabulate

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