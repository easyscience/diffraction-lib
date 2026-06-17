# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Helpers for the documentation cross-engine verification pages.

These utilities back the Verification notebooks: they load externally
calculated reference profiles (for example FullProf output), populate an
experiment grid from a reference pattern, score how closely two
calculated patterns agree, and render a pass/fail agreement table for
the regression checks. They are deliberately kept out of the headline
public API and imported explicitly by the verification notebooks so
those pages stay short and readable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import numpy as np

from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.utils.utils import SOFTWARE_PACKAGE_BY_ENGINE
from easydiffraction.utils.utils import package_version
from easydiffraction.utils.utils import render_table

# Closeness metrics are computed on absolute intensities: each page
# seeds the FullProf scale (from its .pcr) so the calculated patterns
# are compared on their true scale, and the integrated-intensity ratio
# is meaningful rather than forced to one by normalisation.

# A FullProf single-crystal F2cal table row needs at least these many
# columns: h, k, l, ivk, cod, F2obs, F2cal.
_MIN_SC_F2CAL_COLUMNS = 7

# A FullProf ``.prf`` profile data row (Prf=-3 format) has exactly
# these columns: 2Theta, Yobs, Ycal, Yobs-Ycal, Backg. Reflection-
# marker rows carry a trailing ``(h k l)`` and more columns, so they
# are skipped. The calculated intensity is column 2 (Ycal).
_PRF_PROFILE_COLUMNS = 5
_PRF_YCALC_COLUMN = 2
# A two-column ``.bac`` background row holds ``2Theta background``.
_BAC_MIN_COLUMNS = 2

# A FullProf ``Prf=2`` IGOR profile row has columns TwoTheta, Iobs,
# Icalc, Diff under a ``BEGIN``/``END`` block; the calculated intensity
# is column 2 (Icalc).
_IGOR_ICALC_COLUMN = 2
_IGOR_MIN_COLUMNS = 3

# FullProf writes a profile header (min, increment, max) in three fixed
# columns of this width; adjacent values run together when one fills its
# field, so the header is sliced by column when it cannot be split on
# whitespace.
_FULLPROF_HEADER_FIELD_COUNT = 3
_FULLPROF_HEADER_FIELD_WIDTH = 10

# The FullProf reference projects for the docs Verification pages are
# bundled under this directory for now. They will move to the
# downloadable ``diffraction`` data repository, after which
# `download_data` replaces `bundled_reference_dir`.
_VERIFICATION_DOCS_DIR = ('docs', 'docs', 'verification')
_BUNDLED_REFERENCE_SUBPATH = ('fullprof',)


def bundled_reference_dir() -> Path:
    """
    Return the bundled FullProf reference directory.

    Resolves correctly whether called from the repository root (the
    script-test working directory) or from the verification notebook
    directory (the notebook-test working directory). Temporary: the
    bundled files move to the ``diffraction`` data repository later.

    Returns
    -------
    Path
        Directory holding the FullProf reference profiles.
    """
    docs_dir = Path(*_VERIFICATION_DOCS_DIR)
    base = docs_dir if docs_dir.is_dir() else Path()
    return base.joinpath(*_BUNDLED_REFERENCE_SUBPATH)


# ----------------------------------------------------------------------
#  Reference-profile loaders (external software output formats)
# ----------------------------------------------------------------------


def _parse_fullprof_header(line: str) -> tuple[float, float, float]:
    """
    Parse a FullProf profile header into ``(min, increment, max)``.

    The three leading numbers are read on whitespace when they are
    cleanly separated, and sliced from fixed-width columns when they run
    together (for example ``5.00000030004.1875``).

    Parameters
    ----------
    line : str
        First line of a FullProf ``.sub``/``.sim`` file.

    Returns
    -------
    tuple[float, float, float]
        The grid minimum, increment, and maximum.
    """
    header = line.split('!', 1)[0]
    count = _FULLPROF_HEADER_FIELD_COUNT
    tokens = header.split()
    if len(tokens) >= count and all(token.count('.') <= 1 for token in tokens[:count]):
        minimum, increment, maximum = (float(token) for token in tokens[:count])
    else:
        width = _FULLPROF_HEADER_FIELD_WIDTH
        minimum, increment, maximum = (
            float(header[index * width : (index + 1) * width]) for index in range(count)
        )
    return minimum, increment, maximum


def load_columned_profile(
    project_dir: str,
    profile_file: str,
    *,
    skip_rows: int = 1,
    columns: tuple[int, int] = (0, 1),
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load a two-column ``x y`` reference profile.

    Parentheses are stripped so values carrying bracketed uncertainties
    parse cleanly.

    Parameters
    ----------
    project_dir : str
        Reference sub-folder name (under the bundled reference
        directory) holding the FullProf project files.
    profile_file : str
        File name of the column-formatted reference file.
    skip_rows : int, default=1
        Number of header rows to skip.
    columns : tuple[int, int], default=(0, 1)
        Indices of the x and y columns.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The x and y arrays.
    """
    path = str(bundled_reference_dir() / project_dir / profile_file)
    with Path(path).open(encoding='utf-8') as handle:
        lines = handle.readlines()[skip_rows:]
    cleaned = '\n'.join(line.replace('(', ' ').replace(')', ' ') for line in lines)
    x, y = np.genfromtxt(StringIO(cleaned), usecols=columns, unpack=True)
    return x, y


def _parse_igor_profile(lines: list[str]) -> tuple[list[float], list[float]]:
    """Parse the ``Prf=2`` IGOR ``BEGIN``/``END`` profile block."""
    two_theta: list[float] = []
    icalc: list[float] = []
    started = False
    for line in lines:
        text = line.strip()
        if text == 'BEGIN':
            started = True
            continue
        if text == 'END':
            break
        fields = text.split()
        if not started or len(fields) < _IGOR_MIN_COLUMNS:
            continue
        try:
            row = (float(fields[0]), float(fields[_IGOR_ICALC_COLUMN]))
        except ValueError:
            continue
        two_theta.append(row[0])
        icalc.append(row[1])
    return two_theta, icalc


def _parse_tabbed_profile(lines: list[str], path: str) -> tuple[list[float], list[float]]:
    """Parse the tab-separated ``Prf=-3`` profile table."""
    header_index = next(
        (index for index, line in enumerate(lines) if line.lstrip().startswith('2Theta')),
        None,
    )
    if header_index is None:
        msg = f'FullProf profile {path}: no "2Theta" header or IGOR block found.'
        raise ValueError(msg)
    two_theta: list[float] = []
    icalc: list[float] = []
    for line in lines[header_index + 1 :]:
        if '(' in line:  # reflection-marker row
            continue
        fields = line.split()
        if len(fields) != _PRF_PROFILE_COLUMNS:
            continue
        two_theta.append(float(fields[0]))
        icalc.append(float(fields[_PRF_YCALC_COLUMN]))
    return two_theta, icalc


def _parse_fullprof_calc_profile(path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Read ``(2θ, Icalc)`` from a FullProf calculated-profile export.

    Handles both the ``Prf=2`` IGOR text format (``TwoTheta Iobs Icalc
    Diff`` rows inside a ``BEGIN``/``END`` block) and the tab-separated
    ``Prf=-3`` format (``2Theta Yobs Ycal …`` under a ``2Theta``-led
    header, with interleaved reflection-marker rows skipped). Both place
    the calculated intensity in column 2.

    Parameters
    ----------
    path : str
        Path to the FullProf ``.prf`` file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The 2θ grid (corrected axis) and the calculated intensities.

    Raises
    ------
    ValueError
        If no profile data rows are found.
    """
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    is_igor = any('IGOR' in line.upper() for line in lines[:3])
    if is_igor:
        two_theta, icalc = _parse_igor_profile(lines)
    else:
        two_theta, icalc = _parse_tabbed_profile(lines, path)
    if not two_theta:
        msg = f'FullProf profile {path}: no calculated-profile data rows found.'
        raise ValueError(msg)
    return np.asarray(two_theta), np.asarray(icalc)


def _parse_array_background(lines: list[str], path: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse the ``.sub``-style header + flat-array ``.bac`` layout."""
    x_min, x_step, _x_max = _parse_fullprof_header(lines[0])
    background: list[float] = []
    for line in lines[1:]:
        for text in line.split():
            try:
                background.append(float(text))
            except ValueError:
                break  # trailing non-numeric text ends the row
    if not background:
        msg = f'FullProf .bac {path}: no background values after the header.'
        raise ValueError(msg)
    y = np.asarray(background)
    x = x_min + x_step * np.arange(y.size)
    return x, y


def _parse_columned_background(lines: list[str], path: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse the two-column ``2Theta background`` ``.bac`` layout."""
    two_theta: list[float] = []
    column_background: list[float] = []
    for line in lines:
        text = line.strip()
        if text.startswith('!'):
            continue
        fields = text.split()
        if len(fields) < _BAC_MIN_COLUMNS:
            continue
        try:
            row = (float(fields[0]), float(fields[1]))
        except ValueError:
            continue
        two_theta.append(row[0])
        column_background.append(row[1])
    if not two_theta:
        msg = f'FullProf .bac {path}: no background data rows found.'
        raise ValueError(msg)
    return np.asarray(two_theta), np.asarray(column_background)


def _parse_fullprof_background(path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Read ``(2θ, background)`` from a FullProf ``Ppl=2`` ``.bac`` file.

    FullProf writes the ``.bac`` in one of two layouts, both handled
    here:

    * **Two-column** — a ``!``-prefixed comment line followed by
      ``2Theta background`` rows.
    * **Header + array** — a ``min step max`` header line
      (``.sub``-style, with a trailing ``Background of: …`` label)
      followed by the background values as a flat array (several per
      row); the 2θ grid is reconstructed from the header.

    In both layouts the 2θ axis omits the zero shift, so the caller
    realigns it onto the profile axis.

    Parameters
    ----------
    path : str
        Path to the FullProf ``.bac`` file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The (uncorrected) 2θ grid and the real background intensities.

    Raises
    ------
    ValueError
        If no background data rows are found.
    """
    lines = [line for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if not lines:
        msg = f'FullProf .bac {path}: file is empty.'
        raise ValueError(msg)
    if not lines[0].lstrip().startswith('!'):
        # Header + flat-array layout (``.sub``-style ``min step max``).
        return _parse_array_background(lines, path)
    # Two-column ``2Theta background`` layout under ``!`` comments.
    return _parse_columned_background(lines, path)


def load_fullprof_calc_profile(
    project_dir: str,
    profile_file: str,
    background_file: str,
    zero_shift: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load the Bragg-only profile from FullProf calculated + background.

    The ``.prf`` (preferably the higher-precision ``Prf=2`` IGOR export)
    holds the calculated profile ``Icalc`` on the *corrected* 2θ grid —
    the Zero/SyCos/SySin systematic peak-position shift is applied, so
    the peaks sit at their observed positions. The ``Ppl=2`` ``.bac``
    holds the *real* background (the refined polynomial, not the
    display-shifted ``Backg`` column the ``.prf`` carries) on the
    uncorrected 2θ grid. Subtracting the background from ``Icalc`` gives
    the clean Bragg profile, with no pedestal estimate.

    Both files are resolved inside the bundled reference directory, so
    the caller passes only the project sub-folder and the two file
    names. The ``.bac`` 2θ omits the zero shift, so it is realigned onto
    the profile axis by adding ``zero_shift`` (the FullProf ``Zero``)
    and interpolated onto the profile grid before subtraction (the
    background is smooth, so interpolation is lossless and ``Icalc`` is
    left exact).

    Parameters
    ----------
    project_dir : str
        Reference sub-folder name (under the bundled reference
        directory) holding the FullProf project files.
    profile_file : str
        File name of the FullProf calculated-profile ``.prf`` file.
    background_file : str
        File name of the FullProf ``.bac`` background file.
    zero_shift : float
        The FullProf ``Zero`` offset (degrees 2θ) that realigns the
        ``.bac`` 2θ onto the profile axis.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The corrected 2θ grid and the clean Bragg intensities.
    """
    base = bundled_reference_dir() / project_dir
    x, icalc = _parse_fullprof_calc_profile(str(base / profile_file))
    background_x, background_y = _parse_fullprof_background(str(base / background_file))
    background = np.interp(x, background_x + zero_shift, background_y)
    return x, icalc - background


_FULLPROF_VERSION_RE = re.compile(r'FullProf\.2k\s*\(Version\s+([0-9][0-9.]*)')


def fullprof_version(project_dir: str, summary_file: str) -> str:
    """
    Return the FullProf version that produced a reference.

    Reads the version from the banner a FullProf run writes near the top
    of its ``.sum`` (or ``.out``) output — the line ``** PROGRAM
    FullProf.2k (Version 8.40 - Feb2026-ILL JRC) **`` — and returns just
    the version number (for example ``'8.40'``), suited to a plot legend
    such as ``f'FullProf {version}'``.

    Resolved inside the bundled reference directory, so the caller
    passes the project sub-folder and the summary file name.

    Parameters
    ----------
    project_dir : str
        Reference sub-folder name (under the bundled reference
        directory) holding the FullProf project files.
    summary_file : str
        File name of a FullProf ``.sum`` or ``.out`` output file.

    Returns
    -------
    str
        The FullProf version number (for example ``'8.40'``).

    Raises
    ------
    ValueError
        If no version banner is found in the file.
    """
    path = bundled_reference_dir() / project_dir / summary_file
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        match = _FULLPROF_VERSION_RE.search(line)
        if match is not None:
            return match.group(1)
    msg = f'FullProf summary {path}: no FullProf version banner found.'
    raise ValueError(msg)


def fullprof_label(project_dir: str, summary_file: str) -> str:
    """
    Return a FullProf plot-legend label, e.g. ``'FullProf 8.40'``.

    Convenience wrapper over :func:`fullprof_version` so verification
    pages set ``reference_label`` in one line rather than repeating the
    ``f'FullProf {...}'`` formatting.

    Parameters
    ----------
    project_dir : str
        Reference sub-folder name (under the bundled reference
        directory) holding the FullProf project files.
    summary_file : str
        File name of a FullProf ``.sum`` or ``.out`` output file.

    Returns
    -------
    str
        The legend label ``f'FullProf {version}'``.
    """
    return f'FullProf {fullprof_version(project_dir, summary_file)}'


_VCS_HASH_LOCAL_RE = re.compile(r'^g[0-9a-f]{6,40}$')


def _label_version(package_name: str) -> str | None:
    """
    Return an installed package version formatted for a page label.

    Keeps this project's versioningit dev markers (``+dev{N}`` /
    ``+dirty{N}`` / ``+devdirty{N}``) and any PEP 440 public
    dev/pre-release segment, but trims a g-prefixed VCS-hash local part
    (for example ``+g1a2b3c``) so the label stays readable.

    Parameters
    ----------
    package_name : str
        Distribution name to query (for example ``'easydiffraction'``).

    Returns
    -------
    str | None
        The display version string, or ``None`` if the package is not
        installed.
    """
    raw = package_version(package_name)
    if raw is None:
        return None
    base, separator, local = raw.partition('+')
    if separator and _VCS_HASH_LOCAL_RE.match(local):
        return base
    return raw


def engine_label(engine: str, note: str | None = None) -> str:
    """
    Return the candidate label for a verification comparison.

    Builds the EasyDiffraction-plus-engine candidate string with live
    versions, for example ``'edi 1.2.3 (cryspy 2.4.1)'`` or, with a
    ``note``, ``'edi 1.2.3 (cryspy 2.4.1, refined)'``. The engine is
    named explicitly (not read from the active calculator) so a stored
    result keeps the version of the engine that produced it. An
    unresolvable version renders a visible ``?`` marker rather than
    being omitted.

    Parameters
    ----------
    engine : str
        Calculation engine tag, for example ``'cryspy'`` or
        ``'crysfml'``.
    note : str | None, default=None
        Optional annotation appended inside the parentheses, for example
        ``'refined'`` or ``'scale only'``.

    Returns
    -------
    str
        The candidate label string.

    Raises
    ------
    ValueError
        If ``engine`` is not in the shared engine-to-package map.
    """
    if engine not in SOFTWARE_PACKAGE_BY_ENGINE:
        supported = ', '.join(sorted(SOFTWARE_PACKAGE_BY_ENGINE))
        msg = f'Unknown engine {engine!r}; expected one of: {supported}.'
        raise ValueError(msg)

    edi_version = _label_version('easydiffraction')
    engine_version = _label_version(SOFTWARE_PACKAGE_BY_ENGINE[engine])
    edi_text = f'edi {edi_version}' if edi_version is not None else 'edi ?'
    engine_text = f'{engine} ?' if engine_version is None else f'{engine} {engine_version}'
    inner = engine_text if note is None else f'{engine_text}, {note}'
    return f'{edi_text} ({inner})'


def load_fullprof_sc_f2calc(project_dir: str, out_file: str) -> dict[tuple[int, int, int], float]:
    """
    Extract calculated F² per reflection from a FullProf SC output.

    Resolved inside the bundled reference directory, so the caller
    passes the project sub-folder and the file name.

    Reads the integrated-intensity reflection table — the one whose
    header carries the ``F2obs`` and ``F2cal`` columns — and returns a
    mapping from each ``(h, k, l)`` to its ``F2cal``. FullProf reports
    ``F2cal = scale * Corr * |F|²`` (scaled and extinction-corrected), a
    different absolute scale from the engines, so the verification page
    refines a single scale to bring the two onto a common basis.

    Parameters
    ----------
    project_dir : str
        Reference sub-folder name (under the bundled reference
        directory) holding the FullProf project files.
    out_file : str
        File name of the FullProf single-crystal ``.out`` file.

    Returns
    -------
    dict[tuple[int, int, int], float]
        ``{(h, k, l): F2cal}`` for every tabulated reflection.
    """
    path = str(bundled_reference_dir() / project_dir / out_file)
    f2calc: dict[tuple[int, int, int], float] = {}
    in_table = False
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if not in_table:
                in_table = 'F2obs' in line and 'F2cal' in line
                continue
            fields = line.split()
            if len(fields) < _MIN_SC_F2CAL_COLUMNS:
                break
            try:
                hkl = (int(fields[0]), int(fields[1]), int(fields[2]))
                value = float(fields[6])
            except ValueError:
                break
            f2calc[hkl] = value
    return f2calc


def align_reflections(
    reference: dict[tuple[int, int, int], float],
    candidate: dict[tuple[int, int, int], float],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Match two per-reflection maps over their common ``(h, k, l)``.

    Parameters
    ----------
    reference : dict[tuple[int, int, int], float]
        Reference values keyed by reflection.
    candidate : dict[tuple[int, int, int], float]
        Candidate values keyed by reflection.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Reference and candidate arrays over the shared reflections, in a
        common order. Ready for :func:`pattern_closeness`.
    """
    common = sorted(set(reference) & set(candidate))
    ref = np.array([reference[hkl] for hkl in common], dtype=float)
    cand = np.array([candidate[hkl] for hkl in common], dtype=float)
    return ref, cand


# ----------------------------------------------------------------------
#  Experiment-grid population
# ----------------------------------------------------------------------


def set_reference_as_measured(
    experiment: object,
    x: np.ndarray,
    y: np.ndarray,
) -> None:
    """
    Use a reference profile as an experiment's measured pattern.

    Populates the experiment data grid from ``x`` and stores ``y`` as
    the measured intensities, so every engine calculates on exactly the
    reference x grid. Standard uncertainties default to ones. Works for
    both constant-wavelength and time-of-flight powder experiments.

    Parameters
    ----------
    experiment : object
        Powder experiment to populate.
    x : np.ndarray
        Measurement x grid (2θ in degrees or time-of-flight in μs).
    y : np.ndarray
        Reference intensities aligned with ``x``.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    experiment.data._create_items_set_xcoord_and_id(x)
    experiment.data._set_intensity_meas(y)
    experiment.data._set_intensity_meas_su(np.ones_like(y))


def calculate_pattern(
    project: object,
    experiment: object,
    engine: str,
) -> np.ndarray:
    """
    Calculate one experiment's pattern with a chosen engine.

    Selects the calculation engine, refreshes the structure and
    experiment categories, and returns the calculated intensities on the
    experiment's x grid.

    Parameters
    ----------
    project : object
        Project owning the structures linked to the experiment.
    experiment : object
        Experiment to calculate.
    engine : str
        Calculation engine tag (for example ``'cryspy'`` or
        ``'crysfml'``).

    Returns
    -------
    np.ndarray
        Calculated intensities aligned with the experiment x grid.
    """
    experiment.calculator.type = engine
    for structure in project.structures:
        structure._update_categories()
    experiment._update_categories()
    return np.asarray(intensity_category_for(experiment).intensity_calc, dtype=float)


def set_reference_reflections(
    experiment: object,
    reflections: dict[tuple[int, int, int], float],
) -> None:
    """
    Seed a single-crystal experiment with reference reflections.

    Creates one reflection per ``(h, k, l)`` in ``reflections`` and
    stores the reference values as the measured intensities, so the
    chosen engine calculates ``intensity_calc`` for exactly those
    reflections. Standard uncertainties default to ones.

    Parameters
    ----------
    experiment : object
        Single-crystal experiment to populate.
    reflections : dict[tuple[int, int, int], float]
        Reference values keyed by reflection, for example FullProf
        F2cal.
    """
    hkls = sorted(reflections)
    indices_h = np.array([hkl[0] for hkl in hkls], dtype=int)
    indices_k = np.array([hkl[1] for hkl in hkls], dtype=int)
    indices_l = np.array([hkl[2] for hkl in hkls], dtype=int)
    refln = experiment.refln
    refln._create_items_set_hkl_and_id(indices_h, indices_k, indices_l)
    refln._set_intensity_meas(np.array([reflections[hkl] for hkl in hkls], dtype=float))
    refln._set_intensity_meas_su(np.ones(len(hkls), dtype=float))


def calculate_reflections(
    project: object,
    experiment: object,
    engine: str,
) -> dict[tuple[int, int, int], float]:
    """
    Calculate per-reflection intensities with a chosen engine.

    Selects the calculation engine, refreshes the structure and
    experiment categories, and returns ``intensity_calc`` keyed by ``(h,
    k, l)``.

    Parameters
    ----------
    project : object
        Project owning the structures linked to the experiment.
    experiment : object
        Single-crystal experiment to calculate.
    engine : str
        Calculation engine tag (for example ``'cryspy'``).

    Returns
    -------
    dict[tuple[int, int, int], float]
        ``{(h, k, l): intensity_calc}`` for every reflection.
    """
    experiment.calculator.type = engine
    for structure in project.structures:
        structure._update_categories()
    experiment._update_categories()
    refln = experiment.refln
    indices_h = refln.index_h.astype(int)
    indices_k = refln.index_k.astype(int)
    indices_l = refln.index_l.astype(int)
    values = np.asarray(refln.intensity_calc, dtype=float)
    return {
        (int(indices_h[i]), int(indices_k[i]), int(indices_l[i])): float(values[i])
        for i in range(len(values))
    }


# ----------------------------------------------------------------------
#  Closeness metrics
# ----------------------------------------------------------------------


def restrict_to_included(experiment: object, values: np.ndarray) -> np.ndarray:
    """
    Restrict a full-grid array to the experiment's included points.

    Excluded regions drop points from the calculated/measured arrays the
    experiment exposes (``intensity_calc`` and friends iterate the
    included points only), but an external reference loaded onto the
    full grid still spans every point. This filters such a full-length
    reference down to the same included points so it can be compared
    with or plotted against the experiment's arrays.

    Arrays that are not full-length (already restricted) and the
    no-exclusion case are returned unchanged, so the call is safe to
    apply unconditionally.

    Parameters
    ----------
    experiment : object
        Experiment whose intensity category supplies the inclusion mask.
    values : np.ndarray
        Values on the full x grid (for example a FullProf reference).

    Returns
    -------
    np.ndarray
        The values restricted to the included points, or unchanged when
        no restriction applies.
    """
    array = np.asarray(values)
    category = intensity_category_for(experiment)
    mask = getattr(category, '_calc_mask', None)
    if mask is None:
        return array
    mask = np.asarray(mask, dtype=bool)
    if array.shape[:1] == mask.shape and not bool(mask.all()):
        return array[mask]
    return array


@dataclass(frozen=True)
class ClosenessMetrics:
    """Closeness scores between a reference and a candidate pattern."""

    profile_difference_percent: float
    max_deviation_percent: float
    intensity_ratio: float
    correlation: float


def pattern_closeness(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> ClosenessMetrics:
    """
    Score how closely a candidate pattern matches a reference.

    Metrics are computed on the **absolute** intensities, so a page that
    seeds the FullProf scale sees a real scale comparison: the
    integrated-intensity ratio is one only when the calculated areas
    agree, and a scale mismatch widens the profile difference rather
    than being normalised away. The RMS and maximum differences are
    expressed as a percentage of the reference (its RMS and its peak),
    so the tolerances are dataset-independent.

    Parameters
    ----------
    reference : np.ndarray
        Reference intensities (for example FullProf or another engine).
    candidate : np.ndarray
        Candidate intensities to compare against the reference.

    Returns
    -------
    ClosenessMetrics
        Profile difference (%), maximum point-wise deviation (% of the
        reference peak), integrated-intensity ratio, and Pearson
        correlation.

    Raises
    ------
    ValueError
        If the two patterns have different lengths.
    """
    reference = np.asarray(reference, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    if reference.shape != candidate.shape:
        msg = (
            'Reference and candidate patterns must have the same length '
            f'(got {reference.shape} and {candidate.shape}).'
        )
        raise ValueError(msg)

    reference_area = float(np.sum(reference))
    intensity_ratio = float(np.sum(candidate) / reference_area) if reference_area else float('nan')

    difference = reference - candidate
    rms_reference = float(np.sqrt(np.mean(reference**2)))
    profile_difference_percent = (
        100.0 * float(np.sqrt(np.mean(difference**2))) / rms_reference
        if rms_reference
        else float('nan')
    )
    peak_reference = float(np.max(np.abs(reference)))
    max_deviation_percent = (
        100.0 * float(np.max(np.abs(difference))) / peak_reference
        if peak_reference
        else float('nan')
    )
    correlation = float(np.corrcoef(reference, candidate)[0, 1])

    return ClosenessMetrics(
        profile_difference_percent=profile_difference_percent,
        max_deviation_percent=max_deviation_percent,
        intensity_ratio=intensity_ratio,
        correlation=correlation,
    )


# ----------------------------------------------------------------------
#  Agreement assertion table
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class AgreementTolerances:
    """
    Tolerance bounds for cross-pattern agreement checks.

    Defaults expect the calculated areas to agree to about one percent
    once the FullProf scale is seeded: the integrated-intensity ratio
    must sit within 1 % of one, the profile difference under 2.5 %, the
    worst point-wise deviation under 6 %, and the shape correlation
    above 0.999. Tighten further as multi-platform spreads are
    characterised.
    """

    max_profile_difference_percent: float = 2.5
    max_deviation_percent: float = 6.0
    min_intensity_ratio: float = 0.99
    max_intensity_ratio: float = 1.01
    min_correlation: float = 0.999


@dataclass(frozen=True)
class _AgreementCheck:
    """One scored metric row with its pass/fail verdict."""

    metric: str
    expected: str
    actual: str
    passed: bool


def _agreement_checks(
    metrics: ClosenessMetrics,
    tolerances: AgreementTolerances,
) -> list[_AgreementCheck]:
    """Score one comparison's metrics against the tolerances."""
    profile_ok = metrics.profile_difference_percent < tolerances.max_profile_difference_percent
    deviation_ok = metrics.max_deviation_percent < tolerances.max_deviation_percent
    ratio_ok = (
        tolerances.min_intensity_ratio < metrics.intensity_ratio < tolerances.max_intensity_ratio
    )
    correlation_ok = metrics.correlation > tolerances.min_correlation
    return [
        _AgreementCheck(
            metric='Profile diff (%)',
            expected=f'< {tolerances.max_profile_difference_percent:g}',
            actual=f'{metrics.profile_difference_percent:.2f}',
            passed=profile_ok,
        ),
        _AgreementCheck(
            metric='Max deviation (%)',
            expected=f'< {tolerances.max_deviation_percent:g}',
            actual=f'{metrics.max_deviation_percent:.2f}',
            passed=deviation_ok,
        ),
        _AgreementCheck(
            metric='Area ratio',
            expected=f'{tolerances.min_intensity_ratio:g} to {tolerances.max_intensity_ratio:g}',
            actual=f'{metrics.intensity_ratio:.4f}',
            passed=ratio_ok,
        ),
        _AgreementCheck(
            metric='Shape correlation',
            expected=f'> {tolerances.min_correlation:g}',
            actual=f'{metrics.correlation:.4f}',
            passed=correlation_ok,
        ),
    ]


# Red for out-of-tolerance values in the in-plot metrics box, matching
# the calculated-curve colour.
_ANNOTATION_FAIL_COLOR = 'rgb(214, 39, 40)'


def closeness_annotation(
    metrics: ClosenessMetrics,
    tolerances: AgreementTolerances | None = None,
) -> list[str]:
    """
    Return in-plot metric lines with pass/fail icons.

    Each line carries a check or cross icon and shows an
    out-of-tolerance value in red, mirroring the agreement table. The
    text uses the limited HTML that Plotly annotations support.

    Parameters
    ----------
    metrics : ClosenessMetrics
        Scores to annotate.
    tolerances : AgreementTolerances | None, default=None
        Tolerance bounds; the documented defaults are used when omitted.

    Returns
    -------
    list[str]
        One formatted line per metric.
    """
    tolerances = tolerances or AgreementTolerances()
    lines: list[str] = []
    for check in _agreement_checks(metrics, tolerances):
        icon = '✅' if check.passed else '❌'
        value = (
            check.actual
            if check.passed
            else f'<span style="color:{_ANNOTATION_FAIL_COLOR}">{check.actual}</span>'
        )
        lines.append(f'{icon} {check.metric}: {value}')
    return lines


def assert_patterns_agree(
    comparisons: list[tuple[str, np.ndarray, np.ndarray]],
    *,
    tolerances: AgreementTolerances | None = None,
    raise_on_failure: bool = True,
) -> bool:
    """
    Render a pass/fail agreement table for one or more pattern pairs.

    Each comparison is scored with :func:`pattern_closeness` and checked
    against ``tolerances``. A single table summarises every metric with
    a check/cross icon; an out-of-bounds actual value is shown in red.

    Parameters
    ----------
    comparisons : list[tuple[str, np.ndarray, np.ndarray]]
        ``(label, reference, candidate)`` triples to compare.
    tolerances : AgreementTolerances | None, default=None
        Tolerance bounds; the documented defaults are used when omitted.
    raise_on_failure : bool, default=True
        Whether to raise ``AssertionError`` when any metric is out of
        bounds, so the verification notebooks stay regression-checked.

    Returns
    -------
    bool
        ``True`` when every metric is within tolerance.

    Raises
    ------
    AssertionError
        If any metric is out of bounds and ``raise_on_failure`` is True.
    """
    tolerances = tolerances or AgreementTolerances()
    rows: list[list[str]] = []
    failures: list[str] = []
    for label, reference, candidate in comparisons:
        checks = _agreement_checks(pattern_closeness(reference, candidate), tolerances)
        for index, check in enumerate(checks):
            actual = check.actual if check.passed else f'[red]{check.actual}[/red]'
            rows.append([
                label if index == 0 else '',
                check.metric,
                check.expected,
                actual,
                '✅' if check.passed else '❌',
            ])
            if not check.passed:
                failures.append(f'{label} · {check.metric} = {check.actual}')

    render_table(
        columns_headers=['Comparison', 'Metric', 'Expected', 'Actual', 'OK'],
        columns_alignment=['left', 'left', 'right', 'right', 'center'],
        columns_data=rows,
    )

    if failures and raise_on_failure:
        joined = '; '.join(failures)
        msg = f'Pattern agreement check failed: {joined}.'
        raise AssertionError(msg)
    return not failures


# ----------------------------------------------------------------------
#  Refinement comparison
# ----------------------------------------------------------------------


def report_refinement_closeness(
    reference: np.ndarray,
    before: np.ndarray,
    after: np.ndarray,
) -> None:
    """
    Tabulate closeness to a reference before and after refinement.

    Scores ``before`` and ``after`` against the same ``reference`` with
    :func:`pattern_closeness` and renders a compact before/after table,
    so a page can show whether refining the disputed parameters moved
    the candidate closer to the reference. This is a display helper: it
    renders the table and returns nothing, so a notebook cell ending in
    this call shows only the table and not an echoed return value. Call
    :func:`pattern_closeness` directly for the metrics programmatically.

    Parameters
    ----------
    reference : np.ndarray
        Reference intensities (for example FullProf).
    before : np.ndarray
        Candidate intensities before refinement.
    after : np.ndarray
        Candidate intensities after refinement.
    """
    before_metrics = pattern_closeness(reference, before)
    after_metrics = pattern_closeness(reference, after)
    rows = [
        [
            'Profile diff (%)',
            f'{before_metrics.profile_difference_percent:.2f}',
            f'{after_metrics.profile_difference_percent:.2f}',
        ],
        [
            'Max deviation (%)',
            f'{before_metrics.max_deviation_percent:.2f}',
            f'{after_metrics.max_deviation_percent:.2f}',
        ],
        [
            'Area ratio',
            f'{before_metrics.intensity_ratio:.4f}',
            f'{after_metrics.intensity_ratio:.4f}',
        ],
        [
            'Shape correlation',
            f'{before_metrics.correlation:.4f}',
            f'{after_metrics.correlation:.4f}',
        ],
    ]
    render_table(
        columns_headers=['Metric', 'Before', 'After'],
        columns_alignment=['left', 'right', 'right'],
        columns_data=rows,
    )
