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

from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import numpy as np

from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.utils.utils import render_table

# Reference shape metrics are computed on peak-normalised profiles so
# they do not depend on the arbitrary calculated scale of each engine.
_PEAK_NORMALISATION = 100.0

# A FullProf single-crystal F2cal table row needs at least these many
# columns: h, k, l, ivk, cod, F2obs, F2cal.
_MIN_SC_F2CAL_COLUMNS = 7

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


def load_fullprof_profile(path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load a FullProf ``.sub``/``.sim`` profile as ``(x, y)`` arrays.

    The first line holds ``min increment max`` followed by a comment;
    the x grid is reconstructed from that header and the remaining lines
    are flattened into the intensity array. The header is parsed by
    :func:`_parse_fullprof_header`, which also handles the fixed-width
    case where the values run together.

    Parameters
    ----------
    path : str
        Path to the FullProf ``.sub`` or ``.sim`` file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The reconstructed x grid and the profile intensities.
    """
    with Path(path).open(encoding='utf-8') as handle:
        lines = handle.readlines()
    x_min, x_increment, x_max = _parse_fullprof_header(lines[0])
    # The 1e-5 nudge avoids a spurious extra point from float rounding.
    x = np.arange(start=x_min, stop=x_max + x_increment - 1e-5, step=x_increment)
    body = ' '.join(line.strip() for line in lines[1:])
    y = np.genfromtxt(StringIO(body))
    return x, y


def load_columned_profile(
    path: str,
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
    path : str
        Path to the column-formatted file.
    skip_rows : int, default=1
        Number of header rows to skip.
    columns : tuple[int, int], default=(0, 1)
        Indices of the x and y columns.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The x and y arrays.
    """
    with Path(path).open(encoding='utf-8') as handle:
        lines = handle.readlines()[skip_rows:]
    cleaned = '\n'.join(line.replace('(', ' ').replace(')', ' ') for line in lines)
    x, y = np.genfromtxt(StringIO(cleaned), usecols=columns, unpack=True)
    return x, y


def load_fullprof_sc_f2calc(path: str) -> dict[tuple[int, int, int], float]:
    """
    Extract calculated F² per reflection from a FullProf SC output.

    Reads the integrated-intensity reflection table — the one whose
    header carries the ``F2obs`` and ``F2cal`` columns — and returns a
    mapping from each ``(h, k, l)`` to its ``F2cal``. FullProf reports
    ``F2cal = scale * Corr * |F|²`` (scaled and extinction-corrected),
    so compare it on a peak-normalised basis, where the scale cancels.

    Parameters
    ----------
    path : str
        Path to the FullProf single-crystal ``.out`` file.

    Returns
    -------
    dict[tuple[int, int, int], float]
        ``{(h, k, l): F2cal}`` for every tabulated reflection.
    """
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
    experiment categories, and returns ``intensity_calc`` keyed by
    ``(h, k, l)``.

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


@dataclass(frozen=True)
class ClosenessMetrics:
    """Closeness scores between a reference and a candidate pattern."""

    profile_difference_percent: float
    max_deviation: float
    intensity_ratio: float
    correlation: float


def _peak_normalised(values: np.ndarray) -> np.ndarray:
    """Scale a profile so its maximum equals the normalisation peak."""
    peak = float(np.max(values))
    if not peak:
        return values
    return values / peak * _PEAK_NORMALISATION


def pattern_closeness(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> ClosenessMetrics:
    """
    Score how closely a candidate pattern matches a reference.

    All metrics use peak-normalised profiles so they are independent of
    each engine's arbitrary calculated scale; this keeps the integrated-
    intensity ratio meaningful when comparing against external software
    (for example FullProf) that uses a different scale convention.

    Parameters
    ----------
    reference : np.ndarray
        Reference intensities (for example FullProf or another engine).
    candidate : np.ndarray
        Candidate intensities to compare against the reference.

    Returns
    -------
    ClosenessMetrics
        Profile difference (%), maximum point-wise deviation,
        integrated- intensity ratio, and Pearson correlation.

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

    reference_norm = _peak_normalised(reference)
    candidate_norm = _peak_normalised(candidate)

    reference_area = float(np.sum(reference_norm))
    intensity_ratio = (
        float(np.sum(candidate_norm) / reference_area) if reference_area else float('nan')
    )

    difference = reference_norm - candidate_norm
    scale = float(np.sqrt(np.mean(reference_norm**2)))
    profile_difference_percent = (
        100.0 * float(np.sqrt(np.mean(difference**2))) / scale if scale else float('nan')
    )
    max_deviation = float(np.max(np.abs(difference)))
    correlation = float(np.corrcoef(reference_norm, candidate_norm)[0, 1])

    return ClosenessMetrics(
        profile_difference_percent=profile_difference_percent,
        max_deviation=max_deviation,
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

    Defaults keep a generous cross-platform margin for calculation-only
    comparisons while still catching a real regression; tighten them as
    multi-platform spreads are characterised.
    """

    max_profile_difference_percent: float = 10.0
    max_deviation: float = 10.0
    min_intensity_ratio: float = 0.8
    max_intensity_ratio: float = 1.25
    min_correlation: float = 0.99


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
    deviation_ok = metrics.max_deviation < tolerances.max_deviation
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
            metric='Max deviation',
            expected=f'< {tolerances.max_deviation:g}',
            actual=f'{metrics.max_deviation:.3g}',
            passed=deviation_ok,
        ),
        _AgreementCheck(
            metric='Intensity ratio',
            expected=f'{tolerances.min_intensity_ratio:g} to {tolerances.max_intensity_ratio:g}',
            actual=f'{metrics.intensity_ratio:.4f}',
            passed=ratio_ok,
        ),
        _AgreementCheck(
            metric='Correlation',
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
