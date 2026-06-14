# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Data/tutorial downloads, table rendering, and unit helpers."""

from __future__ import annotations

import functools
import hashlib
import importlib.resources
import json
import pathlib
import re
import shutil
import urllib.request
from enum import Enum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import pooch
from packaging.version import Version
from rich.markup import escape
from uncertainties import UFloat
from uncertainties import ufloat
from uncertainties import ufloat_fromstr

from easydiffraction.display.tables import TableRenderer
from easydiffraction.io.ascii import extract_project_from_zip
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.environment import resolve_artifact_path
from easydiffraction.utils.logging import CONSOLE_PARAGRAPH_STYLE
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

pooch.get_logger().setLevel('WARNING')  # Suppress pooch info messages


def display_path(path: pathlib.Path | str) -> str:
    """
    Format a filesystem path for user-facing display.

    Returns the path relative to the current working directory so
    messages stay compact and avoid forced line breaks. Paths outside
    the cwd subtree use ``..`` segments to walk up to a common ancestor
    (e.g. ``../sibling/data.cif``) rather than falling back to an
    absolute path. The absolute path is only used when no relative form
    is possible — on Windows that happens when the path is on a
    different drive from the cwd.

    Parameters
    ----------
    path : pathlib.Path | str
        Filesystem path to format.

    Returns
    -------
    str
        Display string suitable for inline use in console messages.
    """
    resolved = pathlib.Path(path).resolve()
    cwd = pathlib.Path.cwd().resolve()
    try:
        return str(resolved.relative_to(cwd, walk_up=True))
    except ValueError:
        return str(resolved)


def print_metrics_table(rows: list[list[str]]) -> None:
    """
    Render a two-column ``Metric | Value`` table.

    Used for fit-results, settings, and similar summary blocks where
    each row is one labelled scalar. Skips rendering entirely when
    ``rows`` is empty.

    Parameters
    ----------
    rows : list[list[str]]
        Each inner list is ``[label, value_string]``.
    """
    if not rows:
        return
    render_table(
        columns_headers=['Metric', 'Value'],
        columns_alignment=['left', 'right'],
        columns_data=rows,
    )


def print_table_footnote(entries: list[tuple[str, str]]) -> None:
    """
    Print a glossary block below a fit-results-style table.

    Each entry renders as a left-aligned ``• header = description``
    bullet line. The block uses :meth:`ConsolePrinter.small` so it shows
    as dim, smaller supplementary text — in Jupyter the font size
    matches the table-cell text.

    Parameters
    ----------
    entries : list[tuple[str, str]]
        Each tuple is ``(column header, one-line description)``.
    """
    if not entries:
        return
    width = max(len(name) for name, _ in entries) + 4
    lines = [f'  • {name:<{width}} = {description}' for name, description in entries]
    console.small(*lines)


def format_bulleted_warning(header: str, items: list[str]) -> str:
    """
    Format a warning as a header followed by indented bullets.

    Parameters
    ----------
    header : str
        First warning line. Use a trailing colon when bullets follow.
    items : list[str]
        Bullet line bodies.

    Returns
    -------
    str
        Multiline warning text.
    """
    if not items:
        return header
    bullet_lines = [f'• {item}' for item in items]
    return '\n'.join([header, *bullet_lines])


_DATA_REPO = 'easyscience/diffraction'
_DATA_ROOT = 'data'
_DOCS_BASE_URL = 'https://easyscience.github.io/diffraction-lib'
_PARAMETER_DOCS_BLOCKS = {
    'project': frozenset({
        'alias',
        'metadata',
        'rendering_plot',
        'rendering_structure',
        'rendering_table',
        'report',
        'structure_style',
        'structure_view',
        'verbosity',
    }),
    'structure': frozenset({
        'atom_site',
        'atom_site_aniso',
        'cell',
        'geom',
        'space_group',
        'space_group_Wyckoff',
    }),
    'experiment': frozenset({
        'background',
        'calculator',
        'data',
        'diffrn',
        'excluded_region',
        'experiment_type',
        'extinction',
        'instrument',
        'linked_structure',
        'pd_background',
        'pd_meas',
        'peak',
        'preferred_orientation',
        'refln',
    }),
    'analysis': frozenset({
        'constraint',
        'fit_parameter',
        'fit_parameter_correlation',
        'fit_result',
        'fitting_mode',
        'joint_fit',
        'minimizer',
        'sequential_fit',
        'sequential_fit_extract',
        'software',
    }),
}
_PARAMETER_DOCS_CATEGORY_PAGES = {
    'excluded_regions': 'excluded_region',
}
_PARAMETER_DOCS_ITEM_ROUTES = {
    ('data_range', 'two_theta_inc'): ('experiment/pd_meas', 'pd-meas-2theta-range-inc'),
    ('data_range', 'two_theta_max'): ('experiment/pd_meas', 'pd-meas-2theta-range-max'),
    ('data_range', 'two_theta_min'): ('experiment/pd_meas', 'pd-meas-2theta-range-min'),
    (
        'data_range',
        'time_of_flight_inc',
    ): ('experiment/pd_meas', 'pd-meas-time-of-flight-range-inc'),
    (
        'data_range',
        'time_of_flight_max',
    ): ('experiment/pd_meas', 'pd-meas-time-of-flight-range-max'),
    (
        'data_range',
        'time_of_flight_min',
    ): ('experiment/pd_meas', 'pd-meas-time-of-flight-range-min'),
    (
        'data_range',
        'sin_theta_over_lambda_max',
    ): ('experiment/refln', 'refln-sin-theta-over-lambda-range-max'),
    (
        'data_range',
        'sin_theta_over_lambda_min',
    ): ('experiment/refln', 'refln-sin-theta-over-lambda-range-min'),
}
# The downloadable data is pinned to one git commit of the data
# repository, stored in this packaged file and read at runtime (see the
# data-source-pinning ADR). It is the single source of truth for which
# data snapshot a build uses; edit the file to bump the data.
_DATA_INDEX_REF_RESOURCE = '_data_index_ref.txt'
_FULL_SHA_LENGTH = 40
_HEX_DIGITS = frozenset('0123456789abcdef')


@functools.lru_cache(maxsize=1)
def _data_index_ref() -> str:
    """
    Return the validated commit pinning the downloadable data.

    Returns
    -------
    str
        The full 40-character hexadecimal commit SHA read from the
        packaged ``_data_index_ref.txt`` file.

    Raises
    ------
    ValueError
        If the stored value is not a full 40-character hex commit SHA.
    """
    raw = (
        importlib.resources.files('easydiffraction')
        .joinpath(_DATA_INDEX_REF_RESOURCE)
        .read_text(encoding='utf-8')
    )
    ref = raw.strip()
    if len(ref) != _FULL_SHA_LENGTH or not set(ref.lower()) <= _HEX_DIGITS:
        msg = (
            f"Invalid data index ref '{ref}' in {_DATA_INDEX_REF_RESOURCE}: "
            'expected a full 40-character hexadecimal git commit SHA.'
        )
        raise ValueError(msg)
    return ref


def _build_data_url(path: str) -> str:
    path = path.lstrip('/')
    return f'https://raw.githubusercontent.com/{_DATA_REPO}/{_data_index_ref()}/{_DATA_ROOT}/{path}'


class DataNamespace(str, Enum):
    """The fixed namespaces a downloadable dataset id can carry."""

    STRUCTURES = 'structures'
    EXPERIMENTS = 'experiments'
    MEASURED = 'measured'
    PROJECTS = 'projects'


_DATA_NAMESPACES = frozenset(member.value for member in DataNamespace)
# One slug segment: lowercase ASCII letters/digits in dash-separated
# groups, no leading/trailing/doubled dashes (resource-naming ADR).
_SLUG_SEGMENT_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def _validate_slug_segment(segment: str, *, kind: str) -> None:
    """Raise ValueError unless ``segment`` is a valid slug segment."""
    if not _SLUG_SEGMENT_RE.fullmatch(segment):
        msg = (
            f"Invalid {kind} '{segment}': expected lowercase ASCII letters and "
            'digits in dash-separated groups (e.g. lbco-hrpt), with no file '
            'extension, empty segments, or other characters.'
        )
        raise ValueError(msg)


def _validate_dataset_id(name: str) -> None:
    """Validate a dataset id of the form ``<namespace>/<slug>``."""
    if name.count('/') != 1:
        msg = (
            f"Invalid dataset id '{name}': expected '<namespace>/<slug>' with a "
            f'single namespace from {sorted(_DATA_NAMESPACES)}.'
        )
        raise ValueError(msg)
    namespace, slug = name.split('/', 1)
    if namespace not in _DATA_NAMESPACES:
        msg = (
            f"Invalid dataset namespace '{namespace}' in '{name}': expected one "
            f'of {sorted(_DATA_NAMESPACES)}.'
        )
        raise ValueError(msg)
    _validate_slug_segment(slug, kind='dataset slug')


def _validate_tutorial_id(name: str) -> None:
    """Validate a tutorial id (a single slug segment, no namespace)."""
    if '/' in name:
        msg = f"Invalid tutorial id '{name}': tutorials use a bare slug with no '/'."
        raise ValueError(msg)
    _validate_slug_segment(name, kind='tutorial id')


def _ordered_keys(index: dict) -> list[str]:
    """Return index keys in the deterministic order listings show."""
    return sorted(index)


def _is_positional(name: int | str) -> bool:
    """Return True when ``name`` is an interactive positional shortcut."""
    return isinstance(name, int) or (isinstance(name, str) and name.isdigit())


def _resolve_positional(position: int, keys: list[str], *, kind: str) -> str:
    """
    Resolve a 1-based row number against the deterministic listing order.

    The number is a transient row index, never a stored identity
    (resource-naming ADR, Decision 6).
    """
    if not 1 <= position <= len(keys):
        msg = (
            f'Invalid {kind} number {position}: expected 1..{len(keys)} as shown '
            f'by the listing. Use the slug for saved code.'
        )
        raise IndexError(msg)
    return keys[position - 1]


def _record_path(record: dict) -> str:
    if 'path' in record:
        return record['path']

    msg = "Index record must contain 'path' key."
    raise KeyError(msg)


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


def _filename_from_path(record_path: str) -> str:
    """
    Return the local filename for a record (slug leaf plus extension).

    The id already mirrors the file path (resource-naming ADR,
    Decision 5), so the saved file keeps the slug name, e.g.
    ``lbco-hrpt.easydiff``.
    """
    return pathlib.PurePosixPath(record_path).name


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


def _record_hash(record: dict) -> str | None:
    """Return the normalized ``sha256:`` content hash for a record."""
    return _normalize_known_hash(record.get('hash'))


def _sha256_of_file(path: pathlib.Path) -> str:
    """Return the ``sha256:<hex>`` digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return f'sha256:{digest.hexdigest()}'


def _content_tag(record: dict) -> str:
    """
    Return a short content tag for keying extracted project directories.

    Derived from the record's ``sha256`` so that a replaced archive
    extracts to a fresh directory instead of reusing a stale one
    (data-source-pinning ADR, Decision 7). Returns an empty string when
    the record carries no usable hash.
    """
    known = _record_hash(record)
    if known is None:
        return ''
    return known.split(':', 1)[-1][:12]


def _fetch_data_index() -> dict:
    """Fetch and cache the diffraction data index.json."""
    index_url = _build_data_url('index.json')
    _validate_url(index_url)

    cache_dir = pooch.os_cache('easydiffraction')
    # Cache under a commit-named file so a ref bump downloads a fresh
    # index instead of reusing a stale one (data-source-pinning ADR).
    destination_fname = f'data-index-{_data_index_ref()}.json'

    index_path = pooch.retrieve(
        url=index_url,
        known_hash=None,
        fname=destination_fname,
        path=cache_dir,
        progressbar=False,
    )

    with pathlib.Path(index_path).open('r', encoding='utf-8') as f:
        return json.load(f)


def _existing_project_dir(extraction_dir: pathlib.Path) -> pathlib.Path | None:
    """Return one extracted project directory from a destination."""
    project_files = sorted(extraction_dir.rglob('project.easydiff'))
    if not project_files:
        return None
    return project_files[0].parent.resolve()


def _download_data_message(name: str, record: dict) -> str:
    """Return the console message for one downloadable data record."""
    description = record.get('description', '')
    message = f"Data '{name}'"
    if description:
        message += f': {description}'
    return message


def _download_data_targets(
    destination: str,
    record: dict,
) -> tuple[str, bool, pathlib.Path, pathlib.Path, pathlib.Path, str]:
    """Return URL and filesystem targets for one download request."""
    record_path = _record_path(record)
    url = _build_data_url(record_path)
    _validate_url(url)

    fname = _filename_from_path(record_path)
    is_project_archive = record.get('kind') == 'project' and fname.endswith('.zip')
    dest_path = resolve_artifact_path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname
    # Key the extraction directory by content so a replaced project
    # archive extracts to a fresh directory instead of reusing a stale
    # one (data-source-pinning ADR, Decision 7).
    stem = pathlib.Path(fname).stem
    tag = _content_tag(record)
    extraction_dir = dest_path / (f'{stem}-{tag}' if tag else stem)
    return url, is_project_archive, dest_path, file_path, extraction_dir, fname


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


def _resolve_data_id(name: int | str, index: dict) -> str:
    """Resolve a dataset slug or interactive row number to an index key."""
    if _is_positional(name):
        return _resolve_positional(int(name), _ordered_keys(index), kind='dataset')
    name = str(name)
    _validate_dataset_id(name)
    if name not in index:
        msg = f"Unknown dataset '{name}'. Run list_data() to see available datasets."
        raise KeyError(msg)
    return name


def download_data(
    name: int | str,
    destination: str = 'data',
    *,
    overwrite: bool = False,
) -> str:
    """
    Download a dataset by its slug id from the diffraction data index.

    Example: path = download_data('experiments/lbco-hrpt')

    Parameters
    ----------
    name : int | str
        Dataset slug id ``<namespace>/<slug>`` (e.g.
        ``'structures/lbco'``). Interactively, the row number shown by
        :func:`list_data` is also accepted; use the slug in saved code.
    destination : str, default='data'
        Directory to save the downloaded file or extracted project into
        (created if missing). Relative destinations are resolved against
        the configured artifact root when
        ``EASYDIFFRACTION_ARTIFACT_ROOT`` is set.
    overwrite : bool, default=False
        Whether to overwrite the file if it already exists.

    Returns
    -------
    str
        Full path to the downloaded file, or to the extracted project
        directory for project ZIP archives, as string.

    Raises
    ------
    ValueError
        If ``name`` is not a valid dataset slug id.
    KeyError
        If the slug is not found in the index.
    """
    index = _fetch_data_index()
    resource_id = _resolve_data_id(name, index)
    record = index[resource_id]
    url, is_project_archive, dest_path, file_path, extraction_dir, fname = _download_data_targets(
        destination, record
    )
    message = _download_data_message(resource_id, record)

    console.paragraph('Getting data...')
    console.print(f'{message}')

    if is_project_archive and extraction_dir.exists() and not overwrite:
        existing_project_dir = _existing_project_dir(extraction_dir)
        if existing_project_dir is not None:
            console.print(
                f"✅ Data '{resource_id}' already extracted at "
                f"'{display_path(existing_project_dir)}'. Keeping existing."
            )
            return str(existing_project_dir)

    known_hash = _record_hash(record)

    if file_path.exists():
        if is_project_archive and not overwrite:
            project_dir = extract_project_from_zip(file_path, destination=extraction_dir)
            file_path.unlink()
            console.print(f"✅ Data '{resource_id}' extracted to '{display_path(project_dir)}'")
            return str(project_dir)
        # Reuse a local file only when its bytes match the pinned index;
        # a content mismatch means the dataset was replaced upstream, so
        # re-download instead of serving stale data (data-source-pinning
        # ADR, Decision 7).
        stale = known_hash is not None and _sha256_of_file(file_path) != known_hash
        if not overwrite and not stale:
            console.print(
                f"✅ Data '{resource_id}' already present at "
                f"'{display_path(file_path)}'. Keeping existing."
            )
            return str(file_path)
        reason = 'is stale' if stale and not overwrite else 'will be overwritten'
        log.debug(
            f"Data '{resource_id}' already present at '{display_path(file_path)}', but {reason}."
        )
        file_path.unlink()

    if is_project_archive and extraction_dir.exists() and overwrite:
        shutil.rmtree(extraction_dir)

    # Pooch downloads to destination with our controlled filename.
    pooch.retrieve(
        url=url,
        known_hash=known_hash,
        fname=fname,
        path=str(dest_path),
    )

    if is_project_archive:
        project_dir = extract_project_from_zip(file_path, destination=extraction_dir)
        file_path.unlink()
        console.print(
            f"✅ Data '{resource_id}' downloaded and extracted to '{display_path(project_dir)}'"
        )
        return str(project_dir)

    console.print(f"✅ Data '{resource_id}' downloaded to '{display_path(file_path)}'")
    return str(file_path)


def list_data() -> None:
    """Display a table of available example data records."""
    index = _fetch_data_index()
    if not index:
        console.print('❌ No example data available.')
        return

    console.paragraph('Example data available for download:')

    # The id already carries the kind via its namespace, so no separate
    # kind column. The leading '#' is a transient row number for
    # interactive download; the slug is the canonical handle.
    columns_headers = ['#', 'id', 'file', 'description']
    columns_alignment = ['right', 'left', 'left', 'left']
    columns_data = []

    for position, resource_id in enumerate(_ordered_keys(index), start=1):
        record = index[resource_id]
        columns_data.append([
            position,
            resource_id,
            pathlib.PurePosixPath(_record_path(record)).name,
            record.get('description', ''),
        ])

    render_table(
        columns_headers=columns_headers,
        columns_data=columns_data,
        columns_alignment=columns_alignment,
    )


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


def parameter_docs_url(
    data_name: str,
    *,
    page: str | None = None,
    anchor: str | None = None,
    package_name: str = 'easydiffraction',
) -> str:
    """
    Return a versioned parameter documentation URL.

    Parameters
    ----------
    data_name : str
        EasyDiff data name, such as ``'_cell.length_a'``.
    page : str | None, default=None
        Parameter reference page override.
    anchor : str | None, default=None
        Parameter anchor override.
    package_name : str, default='easydiffraction'
        Package used to resolve the documentation version.

    Returns
    -------
    str
        Absolute URL for the parameter reference entry.
    """
    resolved_page, resolved_anchor = _parameter_docs_route(
        data_name,
        page=page,
        anchor=anchor,
    )
    version = _get_version_for_url(package_name)
    base_url = f'{_DOCS_BASE_URL}/{version}/user-guide/parameters/{resolved_page}/'
    return f'{base_url}#{resolved_anchor}'


def _parameter_docs_route(
    data_name: str,
    *,
    page: str | None,
    anchor: str | None,
) -> tuple[str, str]:
    """Resolve the parameter-reference page and anchor."""
    category, item = _split_parameter_data_name(data_name)
    if page is None and anchor is None:
        override = _PARAMETER_DOCS_ITEM_ROUTES.get((category, item))
        if override is not None:
            return override

    route_category = _PARAMETER_DOCS_CATEGORY_PAGES.get(category, category)
    resolved_page = page or _parameter_docs_page(route_category)
    resolved_anchor = anchor or _parameter_docs_anchor(route_category, item)
    return resolved_page.strip('/'), resolved_anchor


def _parameter_docs_page(category: str) -> str:
    """Return the grouped parameter-reference page for a category."""
    for block, categories in _PARAMETER_DOCS_BLOCKS.items():
        if category in categories:
            return f'{block}/{category}'
    return category


def _split_parameter_data_name(data_name: str) -> tuple[str, str]:
    """Split a data name into category and item components."""
    category, _, item = data_name.strip().lstrip('_').partition('.')
    return category, item


def _parameter_docs_anchor(category: str, item: str) -> str:
    """Return the stable docs anchor for a category item."""
    parts = [part for part in (category, item) if part]
    return '-'.join(parts).replace('_', '-').lower()


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

    In the terminal each row shows the tutorial ID, filename, and a
    combined entry with the title on the first line and a dimmed
    description on the second. In Jupyter the table shows the plain
    title only, since the HTML backend cannot render the terminal
    styling.
    """
    index = _fetch_tutorials_index()
    if not index:
        console.print('❌ No tutorials available.')
        return

    version = _get_version_for_url()
    console.paragraph(f'Tutorials available for easydiffraction v{version}:')

    columns_headers = ['#', 'id', 'file', 'tutorial']
    columns_alignment = ['right', 'left', 'left', 'left']
    columns_data = []

    use_markup = not in_jupyter()
    for position, tutorial_id in enumerate(_ordered_keys(index), start=1):
        record = index[tutorial_id]
        filename = f'{tutorial_id}.ipynb'
        title = record.get('title', '')
        description = record.get('description', '')
        if not use_markup:
            # Jupyter uses the HTML table backend, which would show Rich
            # markup as literal text; keep the plain title there.
            details = title
        else:
            styled_title = f'[{CONSOLE_PARAGRAPH_STYLE}]{escape(title)}[/]'
            if description:
                details = f'{styled_title}\n[dim]{escape(description)}[/dim]'
            else:
                details = styled_title
        columns_data.append([position, tutorial_id, filename, details])

    render_table(
        columns_headers=columns_headers,
        columns_data=columns_data,
        columns_alignment=columns_alignment,
        width=shutil.get_terminal_size().columns,
    )


def _resolve_tutorial_id(name: int | str, index: dict) -> str:
    """Resolve a tutorial slug or interactive row number to an index key."""
    if _is_positional(name):
        return _resolve_positional(int(name), _ordered_keys(index), kind='tutorial')
    name = str(name)
    _validate_tutorial_id(name)
    if name not in index:
        msg = f"Unknown tutorial '{name}'. Run list_tutorials() to see available tutorials."
        raise KeyError(msg)
    return name


def download_tutorial(
    name: int | str,
    destination: str = 'tutorials',
    *,
    overwrite: bool = False,
) -> str:
    """
    Download a tutorial notebook by its slug id.

    Example: path = download_tutorial('refine-lbco-hrpt-from-cif')

    Parameters
    ----------
    name : int | str
        Tutorial slug id (e.g. ``'refine-lbco-hrpt-from-cif'``).
        Interactively, the row number shown by :func:`list_tutorials` is
        also accepted; use the slug in saved code.
    destination : str, default='tutorials'
        Directory to save the file into (created if missing). Relative
        destinations are resolved against the configured artifact root
        when ``EASYDIFFRACTION_ARTIFACT_ROOT`` is set.
    overwrite : bool, default=False
        Whether to overwrite the file if it already exists.

    Returns
    -------
    str
        Full path to the downloaded file as string.

    Raises
    ------
    ValueError
        If ``name`` is not a valid tutorial slug id.
    KeyError
        If the slug is not found in the index.
    """
    index = _fetch_tutorials_index()
    resource_id = _resolve_tutorial_id(name, index)

    record = index[resource_id]
    url_template = record['url']
    url = _resolve_tutorial_url(url_template)
    _validate_url(url)

    fname = f'{resource_id}.ipynb'

    dest_path = resolve_artifact_path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / fname

    title = record.get('title', '')
    message = f"Tutorial '{resource_id}'"
    if title:
        message += f': {title}'

    console.paragraph('Getting tutorial...')
    console.print(f'{message}')

    if file_path.exists():
        if not overwrite:
            console.print(
                f"✅ Tutorial '{resource_id}' already present at "
                f"'{display_path(file_path)}'. Keeping existing."
            )
            return str(file_path)
        log.debug(
            f"Tutorial '{resource_id}' already present at "
            f"'{display_path(file_path)}', but will be overwritten."
        )
        file_path.unlink()

    # Download the notebook
    with _safe_urlopen(url) as resp:
        file_path.write_bytes(resp.read())

    console.print(f"✅ Tutorial '{resource_id}' downloaded to '{display_path(file_path)}'")
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
        Directory to save the files into (created if missing). Relative
        destinations are resolved against the configured artifact root
        when ``EASYDIFFRACTION_ARTIFACT_ROOT`` is set.
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
    for tutorial_id in _ordered_keys(index):
        try:
            path = download_tutorial(
                tutorial_id,
                destination=destination,
                overwrite=overwrite,
            )
            downloaded_paths.append(path)
        except (OSError, ValueError) as e:
            log.warning(f"Failed to download tutorial '{tutorial_id}': {e}")

    resolved_destination = resolve_artifact_path(destination)
    console.print(
        f'✅ Downloaded {len(downloaded_paths)} tutorials to '
        f"'{display_path(resolved_destination)}'"
    )
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
    width: int | None = None,
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
    width : int | None, default=None
        Optional target table width. Honored by fixed-width backends
        (Rich); ignored by reflowing ones (HTML).
    """
    headers = [
        (col, align) for col, align in zip(columns_headers, columns_alignment, strict=False)
    ]
    df = pd.DataFrame(columns_data, columns=pd.MultiIndex.from_tuples(headers))

    tabler = TableRenderer.get()
    tabler.render(df, display_handle=display_handle, width=width)


def build_table_renderable(
    columns_data: object,
    columns_alignment: object,
    columns_headers: object = None,
) -> object:
    """
    Build a table renderable for the active display backend.

    Parameters
    ----------
    columns_data : object
        A list of rows, where each row is a list of cell values.
    columns_alignment : object
        A list of alignment strings (e.g. ``'left'``, ``'right'``,
        ``'center'``) matching the number of columns.
    columns_headers : object, default=None
        Optional list of column header strings.

    Returns
    -------
    object
        Backend-native renderable, such as a Rich table or HTML.
    """
    headers = [
        (col, align) for col, align in zip(columns_headers, columns_alignment, strict=False)
    ]
    df = pd.DataFrame(columns_data, columns=pd.MultiIndex.from_tuples(headers))

    tabler = TableRenderer.get()
    return tabler.build_renderable(df)


def _help_first_sentence(docstring: str | None) -> str:
    """Return the first paragraph of a docstring on one line."""
    if not docstring:
        return ''
    first_para = docstring.strip().split('\n\n')[0]
    return ' '.join(line.strip() for line in first_para.splitlines())


def _help_property_rows(cls: type) -> list[list[str]]:
    """Return public property rows for object help tables."""
    seen: dict[str, property] = {}
    for base in cls.mro():
        for key, attr in base.__dict__.items():
            if key.startswith('_') or not isinstance(attr, property):
                continue
            if key not in seen:
                seen[key] = attr

    rows = []
    for key in sorted(seen):
        prop = seen[key]
        writable = '✓' if prop.fset else ''
        doc = _help_first_sentence(prop.fget.__doc__ if prop.fget else None)
        rows.append([key, writable, doc])
    return rows


def _help_method_rows(cls: type) -> list[list[str]]:
    """Return public method rows for object help tables."""
    seen: set[str] = set()
    methods = []
    for base in cls.mro():
        for key, attr in base.__dict__.items():
            if key.startswith('_') or key in seen:
                continue
            if isinstance(attr, property):
                continue
            raw = attr
            if isinstance(raw, (staticmethod, classmethod)):
                raw = raw.__func__
            if callable(raw):
                seen.add(key)
                methods.append((key, raw))

    rows = []
    for key, method in sorted(methods):
        doc = _help_first_sentence(getattr(method, '__doc__', None))
        rows.append([f'{key}()', doc])
    return rows


def render_object_help(obj: object) -> None:
    """
    Print public properties and methods for a plain helper object.

    Parameters
    ----------
    obj : object
        Object whose public API should be summarized.
    """
    cls = type(obj)

    prop_rows = _help_property_rows(cls)
    if prop_rows:
        console.paragraph('Properties')
        render_table(
            columns_headers=['Name', 'Writable', 'Description'],
            columns_alignment=['left', 'center', 'left'],
            columns_data=prop_rows,
        )

    method_rows = _help_method_rows(cls)
    if method_rows:
        console.paragraph('Methods')
        render_table(
            columns_headers=['Name', 'Description'],
            columns_alignment=['left', 'left'],
            columns_data=method_rows,
        )


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
    "3.566(2)" → ufloat(3.566, 0.002) - "3.566()" → ufloat(3.566, nan) -
    None → ufloat(default, nan)

    Behavior: - If the input string contains a value with parentheses
    (e.g. "3.566(2)"), the number in parentheses is interpreted as an
    estimated standard deviation (esd) in the last digit(s). - Empty
    parentheses (e.g. "3.566()") are treated as "no esd provided". - If
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
        # Empty brackets mark refinement intent, not a zero esd.
        s = s[:-2] + '(nan)'
    try:
        return ufloat_fromstr(s)
    except ValueError:
        return ufloat(default, np.nan)
