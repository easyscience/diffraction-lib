"""
General utilities and helpers for easydiffraction.
"""

import os
import numpy as np
import urllib.request
from pathlib import Path

def calculate_r_factor(y_obs, y_calc):
    """
    Calculates R-factor (R1).

    Args:
        y_obs (array-like): Observed intensities.
        y_calc (array-like): Calculated intensities.

    Returns:
        float: R-factor.
    """
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum(np.abs(y_obs - y_calc))
    denominator = np.sum(np.abs(y_obs))
    return numerator / denominator if denominator != 0 else np.nan


def calculate_weighted_r_factor(y_obs, y_calc, weights):
    """
    Calculates weighted R-factor (wR2).

    Args:
        y_obs (array-like): Observed intensities.
        y_calc (array-like): Calculated intensities.
        weights (array-like): Weights (typically 1/sigma^2).

    Returns:
        float: Weighted R-factor.
    """
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    weights = np.asarray(weights)
    numerator = np.sum(weights * (y_obs - y_calc) ** 2)
    denominator = np.sum(weights * y_obs ** 2)
    return np.sqrt(numerator / denominator) if denominator != 0 else np.nan


def calculate_rb_factor(y_obs, y_calc):
    """
    Calculates Rb factor.

    Args:
        y_obs (array-like): Observed intensities.
        y_calc (array-like): Calculated intensities.

    Returns:
        float: Rb-factor.
    """
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum(np.abs(y_obs - y_calc))
    denominator = np.sum(y_obs)
    return numerator / denominator if denominator != 0 else np.nan


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

def get_reliability_inputs(sample_models, experiments, calculator):
    y_obs_all = []
    y_calc_all = []
    y_err_all = []
    for expt_id, experiment in experiments._items.items():
        y_calc = calculator.calculate_pattern(sample_models, experiment)
        y_meas = experiment.datastore.pattern.meas
        y_meas_su = experiment.datastore.pattern.meas_su

        if y_meas is not None and y_calc is not None:
            y_obs_all.extend(y_meas)
            y_calc_all.extend(y_calc)
            y_err_all.extend(y_meas_su if y_meas_su is not None else np.ones_like(y_meas))

    return (
        np.array(y_obs_all),
        np.array(y_calc_all),
        np.array(y_err_all) if y_err_all else None
    )

def calculate_r_factor_squared(y_obs, y_calc):
    """
    Calculates R-factor squared (Rf²).

    Args:
        y_obs (array-like): Observed intensities.
        y_calc (array-like): Calculated intensities.

    Returns:
        float: R-factor squared.
    """
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum((y_obs - y_calc) ** 2)
    denominator = np.sum(y_obs ** 2)
    return np.sqrt(numerator / denominator) if denominator != 0 else np.nan

def calculate_reduced_chi_square(residuals, num_parameters):
    """
    Calculates the reduced chi-square value.

    Args:
        residuals (array-like): Residuals between observed and calculated values.
        num_parameters (int): Number of fitting parameters.

    Returns:
        float: Reduced chi-square.
    """
    residuals = np.asarray(residuals)
    chi_square = np.sum(residuals ** 2)
    n_points = len(residuals)
    dof = n_points - num_parameters
    if dof > 0:
        return chi_square / dof
    else:
        return np.nan
