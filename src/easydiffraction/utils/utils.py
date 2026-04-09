# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import functools
import json
import pathlib
import urllib.request
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import pooch
from packaging.version import Version
from uncertainties import UFloat
from uncertainties import ufloat
from uncertainties import ufloat_fromstr

from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

pooch.get_logger().setLevel('WARNING')  # Suppress pooch info messages


def _validate_url(url: str) -> None:
    """
    Validate that a URL uses only safe HTTP/HTTPS schemes.

    Parameters
    ----------
    url : str
        The URL to validate.

    Raises
    ------
    ValueError
        If the URL scheme is not HTTP or HTTPS.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'}:
        msg = f"Unsafe URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are allowed."
        raise ValueError(msg)


def _filename_for_id_from_url(data_id: int | str, url: str) -> str:
    """Return local filename using the extension from the URL."""
    suffix = pathlib.Path(urlparse(url).path).suffix  # includes leading dot ('.cif', '.xye', ...)
    # If URL has no suffix, fall back to no extension.
    return f'ed-{data_id}{suffix}'


def _normalize_known_hash(value: str | None) -> str | None:
    """
    Return pooch-compatible known_hash or None.

    Treat placeholder values like 'sha256:...' as unset.
    """
    if not value:
        return None
    value = value.strip()
    if value.lower() == 'sha256:...':
        return None
    return value


def _fetch_data_index() -> dict:
    """Fetch and cache the diffraction data index.json."""
    index_url = 'https://raw.githubusercontent.com/easyscience/data/refs/heads/master/diffraction/index.json'
    _validate_url(index_url)

    # macOS: sha256sum index.json
    index_hash = 'sha256:af64483b9e0941af56d582b9d50285b8404e3d10a103d8696cddf3850ee2b660'
    destination_dirname = 'easydiffraction'
    destination_fname = 'data-index.json'
    cache_dir = pooch.os_cache(destination_dirname)

    index_path = pooch.retrieve(
        url=index_url,
        known_hash=index_hash,
        fname=destination_fname,
        path=cache_dir,
        progressbar=False,
    )

    with pathlib.Path(index_path).open('r', encoding='utf-8') as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def _fetch_tutorials_index() -> dict:
    """
    Fetch and cache the tutorials index.json from gh-pages.

    The index is fetched from:
    https://easyscience.github.io/diffraction-lib/{version}/tutorials/index.json

    For released versions, {version} is the public version string (e.g.,
    '0.8.0.post1'). For development versions, 'dev' is used.

    Returns
    -------
    dict
        The tutorials index as a dictionary, or empty dict if fetch
        fails.
    """
    version = _get_version_for_url()
    index_url = f'https://easyscience.github.io/diffraction-lib/{version}/tutorials/index.json'

    try:
        _validate_url(index_url)
        with _safe_urlopen(index_url) as response:
            return json.load(response)
    except (OSError, ValueError) as e:
        log.warning(
            f'Failed to fetch tutorials index from {index_url}: {e}',
            exc_type=UserWarning,
        )
        return {}


def download_data(
    id: int | str,
    destination: str = 'data',
    *,
    overwrite: bool = False,
) -> str:
    """
    Download a dataset by numeric ID using the remote diffraction index.

    Example: path = download_data(id=12, destination="data")

    Parameters
    ----------
    id : int | str
        Numeric dataset id (e.g. 12).
    destination : str, default='data'
        Directory to save the file into (created if missing).
    overwrite : bool, default=False
        Whether to overwrite the file if it already exists.

    Returns
    -------
    str
        Full path to the downloaded file as string.

    Raises
    ------
    KeyError
        If the id is not found in the index.
    """
    index = _fetch_data_index()
    key = str(id)

    if key not in index:
        # Provide a helpful message (and keep KeyError semantics)
        available = ', '.join(
            sorted(index.keys(), key=lambda s: int(s) if s.isdigit() else s)[:20]
        )
        msg = f'Unknown dataset id={id}. Example available ids: {available} ...'
        raise KeyError(msg)

    record = index[key]
    url = record['url']
    _validate_url(url)

    known_hash = _normalize_known_hash(record.get('hash'))
    fname = _filename_for_id_from_url(id, url)

    dest_path = pathlib.Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname

    description = record.get('description', '')
    message = f'Data #{id}'
    if description:
        message += f': {description}'

    console.paragraph('Getting data...')
    console.print(f'{message}')

    if file_path.exists():
        if not overwrite:
            console.print(
                f"✅ Data #{id} already present at '{file_path}'. Keeping existing file."
            )
            return str(file_path)
        log.debug(f"Data #{id} already present at '{file_path}', but will be overwritten.")
        file_path.unlink()

    # Pooch downloads to destination with our controlled filename.
    pooch.retrieve(
        url=url,
        known_hash=known_hash,
        fname=fname,
        path=str(dest_path),
    )

    console.print(f"✅ Data #{id} downloaded to '{file_path}'")
    return str(file_path)


def package_version(package_name: str) -> str | None:
    """
    Get the installed version string of the specified package.

    Parameters
    ----------
    package_name : str
        The name of the package to query.

    Returns
    -------
    str | None
        The raw version string (may include local part, e.g.,
        '1.2.3+abc123'), or None if the package is not installed.
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def stripped_package_version(package_name: str) -> str | None:
    """
    Get installed package version, stripped of local version parts.

    Returns only the public version segment (e.g., '1.2.3' or
    '1.2.3.post4'), omitting any local segment (e.g., '+d136').

    Parameters
    ----------
    package_name : str
        The name of the package to query.

    Returns
    -------
    str | None
        The public version string, or None if the package is not
        installed.
    """
    v_str = package_version(package_name)
    if v_str is None:
        return None
    try:
        v = Version(v_str)
        return str(v.public)
    except ValueError:
        return v_str


def _is_dev_version(package_name: str) -> bool:
    """
    Check if the installed package version is a dev version.

    A version is considered "dev" if: - The raw version contains '+dev',
    '+dirty', or '+devdirty' (local suffixes from versioningit) - The
    public version is '999.0.0' (versioningit default-tag fallback)

    Parameters
    ----------
    package_name : str
        The name of the package to query.

    Returns
    -------
    bool
        True if the version is a development version, False otherwise.
    """
    raw_version = package_version(package_name)
    if raw_version is None:
        return True  # No version found, assume dev

    # Check for local version suffixes from versioningit
    if any(marker in raw_version for marker in ('+dev', '+dirty', '+devdirty')):
        return True

    # Check for default-tag fallback (999.0.0)
    public_version = stripped_package_version(package_name)
    return bool(public_version and public_version.startswith('999.'))


def _get_version_for_url(package_name: str = 'easydiffraction') -> str:
    """
    Get the version string to use in URLs for fetching remote resources.

    Returns the public version for released versions, or 'dev' for
    development/local versions.

    Parameters
    ----------
    package_name : str, default='easydiffraction'
        The name of the package to query.

    Returns
    -------
    str
        The version string to use in URLs ('dev' or a version like
        '0.8.0.post1').
    """
    if _is_dev_version(package_name):
        return 'dev'
    return stripped_package_version(package_name) or 'dev'


def _safe_urlopen(request_or_url: object) -> object:  # type: ignore[no-untyped-def]
    """
    Open a URL with prior validation.

    Centralises lint suppression for validated HTTPS requests.
    """
    # Only allow https scheme.
    if isinstance(request_or_url, str):
        parsed = urllib.parse.urlparse(request_or_url)
        if parsed.scheme != 'https':  # pragma: no cover - sanity check
            msg = 'Only https URLs are permitted'
            raise ValueError(msg)
    elif isinstance(request_or_url, urllib.request.Request):  # noqa: S310
        parsed = urllib.parse.urlparse(request_or_url.full_url)
        if parsed.scheme != 'https':  # pragma: no cover
            msg = 'Only https URLs are permitted'
            raise ValueError(msg)
    else:
        msg = f'Expected str or Request, got {type(request_or_url).__name__}'
        raise TypeError(msg)
    return urllib.request.urlopen(request_or_url)  # noqa: S310


def _resolve_tutorial_url(url_template: str) -> str:
    """
    Replace {version} placeholder in URL template with actual version.

    Parameters
    ----------
    url_template : str
        URL template containing {version} placeholder.

    Returns
    -------
    str
        URL with {version} replaced by actual version string.
    """
    version = _get_version_for_url()
    return url_template.replace('{version}', version)


def list_tutorials() -> None:
    """
    Display a table of available tutorial notebooks.

    Shows tutorial ID, filename and title for all tutorials available
    for the current version of easydiffraction.
    """
    index = _fetch_tutorials_index()
    if not index:
        console.print('❌ No tutorials available.')
        return

    version = _get_version_for_url()
    console.paragraph(f'Tutorials available for easydiffraction v{version}:')

    columns_headers = ['id', 'file', 'title']
    columns_alignment = ['right', 'left', 'left']
    columns_data = []

    for tutorial_id in index:
        record = index[tutorial_id]
        filename = f'ed-{tutorial_id}.ipynb'
        title = record.get('title', '')
        columns_data.append([tutorial_id, filename, title])

    render_table(
        columns_headers=columns_headers,
        columns_data=columns_data,
        columns_alignment=columns_alignment,
    )


def download_tutorial(
    id: int | str,
    destination: str = 'tutorials',
    *,
    overwrite: bool = False,
) -> str:
    """
    Download a tutorial notebook by numeric ID.

    Example: path = download_tutorial(id=1, destination="tutorials")

    Parameters
    ----------
    id : int | str
        Numeric tutorial id (e.g. 1).
    destination : str, default='tutorials'
        Directory to save the file into (created if missing).
    overwrite : bool, default=False
        Whether to overwrite the file if it already exists.

    Returns
    -------
    str
        Full path to the downloaded file as string.

    Raises
    ------
    KeyError
        If the id is not found in the index.
    """
    index = _fetch_tutorials_index()
    key = str(id)

    if key not in index:
        available = ', '.join(
            sorted(index.keys(), key=lambda s: int(s) if s.isdigit() else s)[:20]
        )
        msg = f'Unknown tutorial id={id}. Available ids: {available}'
        raise KeyError(msg)

    record = index[key]
    url_template = record['url']
    url = _resolve_tutorial_url(url_template)
    _validate_url(url)

    fname = f'ed-{id}.ipynb'

    dest_path = pathlib.Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname

    title = record.get('title', '')
    message = f'Tutorial #{id}'
    if title:
        message += f': {title}'

    console.paragraph('Getting tutorial...')
    console.print(f'{message}')

    if file_path.exists():
        if not overwrite:
            console.print(
                f"✅ Tutorial #{id} already present at '{file_path}'. Keeping existing file."
            )
            return str(file_path)
        log.debug(f"Tutorial #{id} already present at '{file_path}', but will be overwritten.")
        file_path.unlink()

    # Download the notebook
    with _safe_urlopen(url) as resp:
        file_path.write_bytes(resp.read())

    console.print(f"✅ Tutorial #{id} downloaded to '{file_path}'")
    return str(file_path)


def download_all_tutorials(
    destination: str = 'tutorials',
    *,
    overwrite: bool = False,
) -> list[str]:
    """
    Download all available tutorial notebooks.

    Example: paths = download_all_tutorials(destination="tutorials")

    Parameters
    ----------
    destination : str, default='tutorials'
        Directory to save the files into (created if missing).
    overwrite : bool, default=False
        Whether to overwrite files if they already exist.

    Returns
    -------
    list[str]
        List of full paths to the downloaded files.
    """
    index = _fetch_tutorials_index()
    if not index:
        console.print('❌ No tutorials available to download.')
        return []

    version = _get_version_for_url()
    console.print(f'📥 Downloading all tutorials for easydiffraction v{version}...')

    downloaded_paths = []
    for tutorial_id in sorted(index.keys(), key=lambda x: int(x) if x.isdigit() else x):
        try:
            path = download_tutorial(
                id=tutorial_id,
                destination=destination,
                overwrite=overwrite,
            )
            downloaded_paths.append(path)
        except (OSError, ValueError) as e:
            log.warning(f'Failed to download tutorial #{tutorial_id}: {e}')

    console.print(f'✅ Downloaded {len(downloaded_paths)} tutorials to "{destination}/"')
    return downloaded_paths


def show_version() -> None:
    """Print the installed version of the easydiffraction package."""
    current_ed_version = package_version('easydiffraction')
    console.print(f'Current easydiffraction v{current_ed_version}')


# TODO: This is a temporary utility function. Complete migration to
#  TableRenderer (as e.g. in show_all_params) and remove this.
def render_table(
    columns_data: object,
    columns_alignment: object,
    columns_headers: object = None,
    display_handle: object = None,
) -> None:
    """
    Render tabular data to the active display backend.

    Parameters
    ----------
    columns_data : object
        A list of rows, where each row is a list of cell values.
    columns_alignment : object
        A list of alignment strings (e.g. ``'left'``, ``'right'``,
        ``'center'``) matching the number of columns.
    columns_headers : object, default=None
        Optional list of column header strings.
    display_handle : object, default=None
        Optional display handle for in-place updates (e.g. in Jupyter or
        a terminal Live context).
    """
    headers = [
        (col, align) for col, align in zip(columns_headers, columns_alignment, strict=False)
    ]
    df = pd.DataFrame(columns_data, columns=pd.MultiIndex.from_tuples(headers))

    tabler = TableRenderer.get()
    tabler.render(df, display_handle=display_handle)


def render_cif(cif_text: str) -> None:
    """
    Display CIF text as a formatted table in Jupyter or terminal.

    Parameters
    ----------
    cif_text : str
        The CIF text to display.
    """
    # Split into lines
    lines: list[str] = list(cif_text.splitlines())

    # Convert each line into a single-column format for table rendering
    columns: list[list[str]] = [[line] for line in lines]

    # Render the table using left alignment and no headers
    render_table(
        columns_headers=['CIF'],
        columns_alignment=['left'],
        columns_data=columns,
    )


def tof_to_d(
    tof: np.ndarray,
    offset: float,
    linear: float,
    quad: float,
    quad_eps: float = 1e-20,
) -> np.ndarray:
    """
    Convert time-of-flight to d-spacing using quadratic calibration.

    Model: TOF = offset + linear * d + quad * d²

    The function: - Uses a linear fallback when the quadratic term is
    effectively zero. - Solves the quadratic for d and selects the
    smallest positive, finite root. - Returns NaN where no valid
    solution exists. - Expects ``tof`` as a NumPy array; output matches
    its shape.

    Parameters
    ----------
    tof : np.ndarray
        Time-of-flight values (μs). Must be a NumPy array.
    offset : float
        Calibration offset (μs).
    linear : float
        Linear calibration coefficient (μs/Å).
    quad : float
        Quadratic calibration coefficient (μs/Å²).
    quad_eps : float, default=1e-20
        Threshold to treat ``quad`` as zero.

    Returns
    -------
    np.ndarray
        d-spacing values (Å), NaN where invalid.

    Raises
    ------
    TypeError
        If ``tof`` is not a NumPy array or coefficients are not real
        numbers.
    """
    # Type checks
    if not isinstance(tof, np.ndarray):
        msg = f"'tof' must be a NumPy array, got {type(tof).__name__}"
        raise TypeError(msg)
    for name, val in (
        ('offset', offset),
        ('linear', linear),
        ('quad', quad),
        ('quad_eps', quad_eps),
    ):
        if not isinstance(val, (int, float, np.integer, np.floating)):
            msg = f"'{name}' must be a real number, got {type(val).__name__}"
            raise TypeError(msg)

    # Output initialized to NaN
    d_out = np.full_like(tof, np.nan, dtype=float)

    # 1) If quadratic term is effectively zero, use linear formula:
    #    TOF ≈ offset + linear * d =>
    #    d ≈ (tof - offset) / linear
    if abs(quad) < quad_eps:
        if abs(linear) > quad_eps:
            d = (tof - offset) / linear
            # Keep only positive, finite results
            valid = np.isfinite(d) & (d > 0)
            d_out[valid] = d[valid]
        # If B == 0 too, there's no solution; leave NaN
        return d_out

    # 2) If quadratic term is significant, solve the quadratic equation:
    #    TOF = offset + linear * d + quad * d² =>
    #    quad * d² + linear * d + (offset - tof) = 0
    discr = linear**2 - 4 * quad * (offset - tof)
    has_real_roots = discr >= 0

    if np.any(has_real_roots):
        sqrt_discr = np.sqrt(discr[has_real_roots])

        root_1 = (-linear + sqrt_discr) / (2 * quad)
        root_2 = (-linear - sqrt_discr) / (2 * quad)

        # Pick smallest positive, finite root per element
        # Stack roots for comparison
        roots = np.stack((root_1, root_2), axis=0)
        # Replace non-finite or negative roots with NaN
        roots = np.where(np.isfinite(roots) & (roots > 0), roots, np.nan)
        # Choose the smallest positive root or NaN if none are valid
        chosen = np.nanmin(roots, axis=0)

        d_out[has_real_roots] = chosen

    return d_out


def twotheta_to_d(twotheta: object, wavelength: float) -> object:
    """
    Convert 2-theta to d-spacing using Bragg's law.

    Parameters
    ----------
    twotheta : object
        2-theta angle in degrees (float or np.ndarray).
    wavelength : float
        Wavelength in Å.

    Returns
    -------
    object
        d-spacing in Å (float or np.ndarray).
    """
    # Convert twotheta from degrees to radians
    theta_rad = np.radians(twotheta / 2)

    # Calculate d-spacing using Bragg's law
    return wavelength / (2 * np.sin(theta_rad))


def sin_theta_over_lambda_to_d_spacing(sin_theta_over_lambda: object) -> object:
    """
    Convert sin(theta)/lambda to d-spacing.

    Parameters
    ----------
    sin_theta_over_lambda : object
        sin(theta)/lambda in 1/Å (float or np.ndarray).

    Returns
    -------
    object
        d-spacing in Å (float or np.ndarray).
    """
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        d = 1 / (2 * sin_theta_over_lambda)
        # Set non-positive inputs to NaN
        return np.where(sin_theta_over_lambda > 0, d, np.nan)


def str_to_ufloat(s: str | None, default: float | None = None) -> UFloat:
    """
    Parse a CIF-style numeric string into a ufloat.

    Examples of supported input: - "3.566" → ufloat(3.566, nan) -
    "3.566(2)" → ufloat(3.566, 0.002) - "3.566()" → ufloat(3.566, 0.0) -
    None → ufloat(default, nan)

    Behavior: - If the input string contains a value with parentheses
    (e.g. "3.566(2)"), the number in parentheses is interpreted as an
    estimated standard deviation (esd) in the last digit(s). - Empty
    parentheses (e.g. "3.566()") are treated as zero uncertainty. - If
    the input string has no parentheses, an uncertainty of NaN is
    assigned to indicate "no esd provided". - If parsing fails, the
    function falls back to the given ``default`` value with uncertainty
    NaN.

    Parameters
    ----------
    s : str | None
        Numeric string in CIF format (e.g. "3.566", "3.566(2)",
        "3.566()") or None.
    default : float | None, default=None
        Default value to use if ``s`` is None or parsing fails.

    Returns
    -------
    UFloat
        An ``uncertainties.UFloat`` object with the parsed value and
        uncertainty. The uncertainty will be NaN if not specified or
        parsing failed.
    """
    if s is None:
        return ufloat(default, np.nan)

    if '(' not in s and ')' not in s:
        s = f'{s}(nan)'
    elif s.endswith('()'):
        # Empty brackets → zero uncertainty (free parameter, no esd yet)
        s = s[:-2] + '(0)'
    try:
        return ufloat_fromstr(s)
    except ValueError:
        return ufloat(default, np.nan)
