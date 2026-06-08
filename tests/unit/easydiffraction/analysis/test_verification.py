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


def test_load_fullprof_profile_length_mismatch_raises(tmp_path):
    sub = tmp_path / 'ref.sub'
    # Header maximum 12.0 implies five points (10.0..12.0 step 0.5) but
    # only three intensities follow, so the grid built from the body ends
    # at 11.0 — more than one step short of 12.0: a corrupt reference.
    sub.write_text(
        '   10.0   0.5   12.0   ! a comment\n   1.0  2.0  3.0\n',
        encoding='utf-8',
    )
    with pytest.raises(ValueError, match='header maximum'):
        verify.load_fullprof_profile(str(sub))


def test_load_fullprof_profile_empty_file_raises(tmp_path):
    sub = tmp_path / 'ref.sub'
    sub.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='expected a header line'):
        verify.load_fullprof_profile(str(sub))


def test_load_fullprof_profile_header_only_raises(tmp_path):
    sub = tmp_path / 'ref.sub'
    # A header with no intensity lines following must surface a clear
    # error rather than a confusing grid-mismatch message.
    sub.write_text('   10.0   0.5   12.0   ! a comment\n', encoding='utf-8')
    with pytest.raises(ValueError, match='no intensity values'):
        verify.load_fullprof_profile(str(sub))


def test_load_fullprof_profile_tolerates_rounded_header_maximum(tmp_path):
    sub = tmp_path / 'ref.sub'
    # The header maximum is rounded a fraction of a step high (12.0004 vs
    # the true last point 12.0), which must not add a spurious point.
    sub.write_text(
        '   10.0   0.5   12.0004   ! a comment\n   1.0  2.0  3.0  4.0  5.0\n',
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
#  Single-crystal reference loaders
# ----------------------------------------------------------------------


def test_load_fullprof_sc_f2calc_reads_table(tmp_path):
    out = tmp_path / 'sc.out'
    # A header line carrying 'F2obs' and 'F2cal' starts the table; F2cal
    # is the seventh column. A short row (or non-numeric row) ends it, so
    # the trailing summary line must not be parsed as a reflection.
    out.write_text(
        'Some preamble line that should be ignored\n'
        '   h   k   l ivk   cod      F2obs         F2cal     more...\n'
        '   2   0   0   0     1     175.6782     173.6998     0.0\n'
        '   4   0   0   0     1     787.9925     788.1127     0.0\n'
        ' => end of table\n'
        '   9   9   9   0     1     1.0          2.0          0.0\n',
        encoding='utf-8',
    )
    f2calc = verify.load_fullprof_sc_f2calc(str(out))
    assert f2calc == {(2, 0, 0): pytest.approx(173.6998), (4, 0, 0): pytest.approx(788.1127)}
    # The reflection after the terminator row must not be picked up.
    assert (9, 9, 9) not in f2calc


def test_align_reflections_keeps_common_hkls_in_order():
    reference = {(2, 0, 0): 10.0, (4, 0, 0): 20.0, (6, 0, 0): 30.0}
    candidate = {(4, 0, 0): 21.0, (2, 0, 0): 11.0, (8, 0, 0): 99.0}
    ref, cand = verify.align_reflections(reference, candidate)
    # Only the shared (2,0,0) and (4,0,0), in a common sorted order.
    np.testing.assert_allclose(ref, [10.0, 20.0])
    np.testing.assert_allclose(cand, [11.0, 21.0])


# ----------------------------------------------------------------------
#  Closeness metrics
# ----------------------------------------------------------------------


def test_pattern_closeness_identical_patterns():
    x = np.linspace(0.0, 10.0, 200)
    pattern = _gaussian(x, 5.0, 0.4) * 1000.0 + 1.0
    metrics = verify.pattern_closeness(pattern, pattern)
    assert metrics.profile_difference_percent == pytest.approx(0.0, abs=1e-9)
    assert metrics.max_deviation_percent == pytest.approx(0.0, abs=1e-9)
    assert metrics.intensity_ratio == pytest.approx(1.0)
    assert metrics.correlation == pytest.approx(1.0)


def test_pattern_closeness_reflects_absolute_scale():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 1000.0 + 1.0
    # Metrics are absolute: a pure rescaling changes the integrated ratio
    # and the profile difference, while the shape correlation stays one.
    candidate = reference * 0.25
    metrics = verify.pattern_closeness(reference, candidate)
    assert metrics.intensity_ratio == pytest.approx(0.25)
    assert metrics.profile_difference_percent > 1.0
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
        max_deviation_percent=0.45,
        intensity_ratio=1.01,
        correlation=0.999,
    )
    lines = verify.closeness_annotation(passing)
    assert len(lines) == 4
    assert all(line.startswith('✅') for line in lines)
    assert all('color:' not in line for line in lines)

    failing = verify.ClosenessMetrics(
        profile_difference_percent=25.0,
        max_deviation_percent=20.0,
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
    assert tolerances.max_profile_difference_percent == 3.0
    assert tolerances.max_deviation_percent == 5.0
    assert tolerances.min_intensity_ratio == pytest.approx(0.98)
    assert tolerances.max_intensity_ratio == pytest.approx(1.02)
    assert tolerances.min_correlation == 0.99


# ----------------------------------------------------------------------
#  Refinement comparison
# ----------------------------------------------------------------------


def test_report_refinement_closeness_scores_before_and_after():
    x = np.linspace(0.0, 10.0, 200)
    reference = _gaussian(x, 5.0, 0.4) * 100.0
    before = _gaussian(x, 5.4, 0.4) * 100.0  # shifted peak — poor match
    after = _gaussian(x, 5.02, 0.4) * 100.0  # almost on the reference
    # The display helper renders the table and returns nothing, so a
    # notebook cell ending in it shows only the table.
    assert verify.report_refinement_closeness(reference, before, after) is None
    # The underlying metrics still move the candidate closer.
    before_metrics = verify.pattern_closeness(reference, before)
    after_metrics = verify.pattern_closeness(reference, after)
    assert after_metrics.profile_difference_percent < before_metrics.profile_difference_percent
    assert after_metrics.correlation > before_metrics.correlation


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


def test_set_reference_reflections_populates_refln():
    from easydiffraction import ExperimentFactory

    experiment = ExperimentFactory.from_scratch(
        name='ref',
        sample_form='single crystal',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    reflections = {(2, 0, 0): 175.0, (4, 0, 0): 788.0, (0, 2, 0): 177.0}
    verify.set_reference_reflections(experiment, reflections)

    refln = experiment.refln
    # Reflections are created in sorted (h, k, l) order.
    hkls = list(
        zip(
            refln.index_h.astype(int),
            refln.index_k.astype(int),
            refln.index_l.astype(int),
            strict=True,
        )
    )
    assert hkls == sorted(reflections)
    expected = np.array([reflections[hkl] for hkl in sorted(reflections)], dtype=float)
    np.testing.assert_allclose(refln.intensity_meas, expected)
