# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the cross-engine verification helpers."""

import numpy as np
import pytest

from easydiffraction.analysis import verification as verify


def _gaussian(x: np.ndarray, center: float, width: float) -> np.ndarray:
    """Return a simple Gaussian peak for synthetic patterns."""
    return np.exp(-((x - center) ** 2) / (2.0 * width**2))


# ----------------------------------------------------------------------
#  Reference-profile loaders
# ----------------------------------------------------------------------


def test_load_fullprof_profile_reconstructs_grid(tmp_path):
    sub = tmp_path / 'ref.sub'
    # Header: min increment max + comment, then flattened intensities.
    sub.write_text(
        '   10.0   0.5   12.0   ! a comment\n   1.0  2.0  3.0\n   4.0  5.0\n',
        encoding='utf-8',
    )
    x, y = verify.load_fullprof_profile(str(sub))
    np.testing.assert_allclose(x, [10.0, 10.5, 11.0, 11.5, 12.0])
    np.testing.assert_allclose(y, [1.0, 2.0, 3.0, 4.0, 5.0])


def test_load_fullprof_profile_parses_fixed_width_header(tmp_path):
    sub = tmp_path / 'ref.sub'
    # Step and max run together in the fixed 10-character columns, as in
    # FullProf's '5.00000030004.1875'-style headers.
    sub.write_text(
        '   10.0000  0.50000012.000000   ! comment\n   1.0 2.0 3.0\n   4.0 5.0\n',
        encoding='utf-8',
    )
    x, y = verify.load_fullprof_profile(str(sub))
    np.testing.assert_allclose(x, [10.0, 10.5, 11.0, 11.5, 12.0])
    np.testing.assert_allclose(y, [1.0, 2.0, 3.0, 4.0, 5.0])


def test_load_columned_profile_reads_two_columns(tmp_path):
    dat = tmp_path / 'ref.dat'
    dat.write_text('! header line\n10.0 100.0\n10.5 200.0\n11.0 150.0\n', encoding='utf-8')
    x, y = verify.load_columned_profile(str(dat), skip_rows=1, columns=(0, 1))
    np.testing.assert_allclose(x, [10.0, 10.5, 11.0])
    np.testing.assert_allclose(y, [100.0, 200.0, 150.0])


def test_bundled_reference_dir_points_at_fullprof():
    path = verify.bundled_reference_dir()
    assert path.parts[-2:] == ('verification', 'fullprof')


# ----------------------------------------------------------------------
#  Closeness metrics
# ----------------------------------------------------------------------


def test_pattern_closeness_identical_patterns():
    x = np.linspace(0.0, 10.0, 200)
    pattern = _gaussian(x, 5.0, 0.4) * 1000.0 + 1.0
    metrics = verify.pattern_closeness(pattern, pattern)
    assert metrics.profile_difference_percent == pytest.approx(0.0, abs=1e-9)
    assert metrics.max_deviation == pytest.approx(0.0, abs=1e-9)
    assert metrics.intensity_ratio == pytest.approx(1.0)
    assert metrics.correlation == pytest.approx(1.0)


def test_pattern_closeness_is_scale_independent():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 1000.0 + 1.0
    # A pure rescaling must not change any shape metric.
    candidate = reference * 0.25
    metrics = verify.pattern_closeness(reference, candidate)
    assert metrics.profile_difference_percent == pytest.approx(0.0, abs=1e-9)
    assert metrics.intensity_ratio == pytest.approx(1.0)
    assert metrics.correlation == pytest.approx(1.0)


def test_pattern_closeness_detects_a_shape_difference():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 100.0
    candidate = _gaussian(x, 5.3, 0.4) * 100.0  # shifted peak
    metrics = verify.pattern_closeness(reference, candidate)
    assert metrics.profile_difference_percent > 1.0
    assert metrics.correlation < 1.0


def test_pattern_closeness_length_mismatch_raises():
    with pytest.raises(ValueError, match='same length'):
        verify.pattern_closeness(np.zeros(5), np.zeros(6))


def test_closeness_annotation_marks_pass_and_fail():
    passing = verify.ClosenessMetrics(
        profile_difference_percent=1.23,
        max_deviation=0.45,
        intensity_ratio=1.01,
        correlation=0.999,
    )
    lines = verify.closeness_annotation(passing)
    assert len(lines) == 4
    assert all(line.startswith('✅') for line in lines)
    assert all('color:' not in line for line in lines)

    failing = verify.ClosenessMetrics(
        profile_difference_percent=25.0,
        max_deviation=20.0,
        intensity_ratio=0.7,
        correlation=0.9,
    )
    fail_lines = verify.closeness_annotation(failing)
    assert all(line.startswith('❌') for line in fail_lines)
    assert all('color:' in line for line in fail_lines)


# ----------------------------------------------------------------------
#  Agreement table
# ----------------------------------------------------------------------


def test_assert_patterns_agree_passes_for_close_patterns():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 100.0
    candidate = reference * 1.0001
    assert verify.assert_patterns_agree([('a vs b', reference, candidate)]) is True


def test_assert_patterns_agree_raises_for_divergent_patterns():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 100.0
    candidate = _gaussian(x, 6.5, 0.4) * 100.0
    with pytest.raises(AssertionError, match='agreement check failed'):
        verify.assert_patterns_agree([('a vs b', reference, candidate)])


def test_assert_patterns_agree_can_report_without_raising():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 100.0
    candidate = _gaussian(x, 6.5, 0.4) * 100.0
    result = verify.assert_patterns_agree(
        [('a vs b', reference, candidate)],
        raise_on_failure=False,
    )
    assert result is False


def test_agreement_tolerances_defaults():
    tolerances = verify.AgreementTolerances()
    assert tolerances.max_profile_difference_percent == 10.0
    assert tolerances.min_intensity_ratio < 1.0 < tolerances.max_intensity_ratio
    assert tolerances.min_correlation == 0.99


# ----------------------------------------------------------------------
#  Experiment-grid population
# ----------------------------------------------------------------------


def test_set_reference_as_measured_populates_grid():
    from easydiffraction import ExperimentFactory
    from easydiffraction.datablocks.experiment.item.base import intensity_category_for

    experiment = ExperimentFactory.from_scratch(
        name='ref',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    x = np.array([10.0, 10.5, 11.0, 11.5])
    y = np.array([5.0, 7.0, 9.0, 4.0])
    verify.set_reference_as_measured(experiment, x, y)

    pattern = intensity_category_for(experiment)
    np.testing.assert_allclose(pattern.x, x)
    np.testing.assert_allclose(pattern.intensity_meas, y)
