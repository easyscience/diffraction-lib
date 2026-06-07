# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tutorial-corpus regression for automatic background estimation.

Loads representative tutorial experiments (constant-wavelength HRPT/LBCO
from ed-2 and time-of-flight Si from ed-13), records each tutorial's
hand-placed background as a reference curve, then strips it, runs
``auto_estimate()``, and asserts the estimated line-segment background
tracks the reference to within a small fraction of the *signal* scale
over the active data. Data-only: no calculation engine is run.

These two data ids represent the CWL and TOF regimes through the same
adapter and estimator code path. The other tutorials the plan lists are
substituted deliberately: ed-17 ships its data as a zip scan directory
and ed-16 defines its background in a loop, both of which complicate a
clean data-only load without adding coverage of a new code path. Sloping
and curved backgrounds are covered against *exact* analytic ground truth
by the unit tests in
``tests/unit/.../categories/background/test_estimate.py``.
"""

import numpy as np

import easydiffraction as ed

# The estimated background may differ from the coarse hand-placed
# reference by at most these fractions of the measured signal scale
# (the 5-95 percentile range of the measured intensities). They are loose
# enough for a hand-placed reference yet tight enough that a wrong-level
# or garbage estimate fails.
_MEDIAN_TOL = 0.15
_MAX_TOL = 0.45


def _assert_tracks_reference(tmp_path, name, data_id, beam_mode, probe, excluded, ref_points):
    project = ed.Project()
    data_path = ed.download_data(id=data_id, destination=str(tmp_path))
    project.experiments.add_from_data_path(
        name=name,
        data_path=data_path,
        sample_form='powder',
        beam_mode=beam_mode,
        radiation_probe=probe,
    )
    experiment = project.experiments[name]
    for start, end in excluded:
        experiment.excluded_regions.create(start=start, end=end)

    data = experiment.background._parent.data
    x = np.asarray(data.x, dtype=float)
    measured = np.asarray(data.intensity_meas, dtype=float)
    signal_scale = float(np.percentile(measured, 95) - np.percentile(measured, 5))

    # The tutorial's hand-placed background is the reference curve.
    for px, py in ref_points:
        experiment.background.create(x=px, y=py)
    ref_x = np.array([p.x.value for p in experiment.background])
    ref_y = np.array([p.y.value for p in experiment.background])
    reference = np.interp(x, ref_x, ref_y)

    # Strip the reference and estimate the background automatically.
    experiment.background.auto_estimate()
    points = list(experiment.background)
    est_x = np.array([p.x.value for p in points])
    est_y = np.array([p.y.value for p in points])
    estimate = np.interp(x, est_x, est_y)

    span = x.max() - x.min()
    # A sparse, non-negative set of anchors spanning the active range.
    assert 2 <= len(points) < 100
    assert np.all(est_y >= 0)
    assert est_x.min() <= x.min() + 0.05 * span
    assert est_x.max() >= x.max() - 0.05 * span
    # The estimate tracks the hand-placed reference within a small fraction
    # of the signal scale (a wrong-level or garbage estimate would not).
    assert np.median(np.abs(estimate - reference)) < _MEDIAN_TOL * signal_scale
    assert np.max(np.abs(estimate - reference)) < _MAX_TOL * signal_scale


def test_auto_estimate_tracks_cwl_tutorial_background(tmp_path):
    # ed-2: constant-wavelength neutron HRPT/LBCO, flat background ~170.
    _assert_tracks_reference(
        tmp_path,
        'hrpt',
        3,
        'constant wavelength',
        'neutron',
        [(0, 5), (165, 180)],
        [(10, 170), (30, 170), (50, 170), (110, 170), (165, 170)],
    )


def test_auto_estimate_tracks_tof_tutorial_background(tmp_path):
    # ed-13: time-of-flight neutron Si, flat background ~0.01.
    _assert_tracks_reference(
        tmp_path,
        'sim_si',
        17,
        'time-of-flight',
        'neutron',
        [(0, 55000), (105500, 200000)],
        [
            (50000, 0.01),
            (60000, 0.01),
            (70000, 0.01),
            (80000, 0.01),
            (90000, 0.01),
            (100000, 0.01),
            (110000, 0.01),
        ],
    )
