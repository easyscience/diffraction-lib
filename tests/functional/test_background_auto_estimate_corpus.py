# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tutorial-corpus regression for automatic background estimation.

Loads a representative constant-wavelength tutorial experiment (the HRPT
LBCO pattern from ed-2, whose hand-placed background is a flat ~170), runs
``auto_estimate()`` data-only, and asserts the recovered background tracks
the known one. Data-only: no calculation engine is run.
"""

import easydiffraction as ed
import numpy as np


def test_auto_estimate_recovers_cwl_background(tmp_path):
    project = ed.Project()
    data_path = ed.download_data(id=3, destination=str(tmp_path))
    project.experiments.add_from_data_path(
        name='hrpt',
        data_path=data_path,
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
    )
    experiment = project.experiments['hrpt']
    # Mirror the tutorial's excluded edges so noisy ends do not skew anchors.
    experiment.excluded_regions.create(id='1', start=0, end=5)
    experiment.excluded_regions.create(id='2', start=165, end=180)

    experiment.background.auto_estimate()

    points = list(experiment.background)
    heights = np.array([p.y.value for p in points])
    positions = np.array([p.x.value for p in points])

    # A sensible, sparse set of points was produced from the real pattern.
    assert 2 <= len(points) < 100
    # The hand-placed ground-truth background is flat at ~170; the recovered
    # heights track it and never go negative.
    assert np.all(heights >= 0)
    assert 100.0 < float(np.median(heights)) < 250.0
    # Points span the active measured range.
    assert positions.min() < 20.0
    assert positions.max() > 150.0


def test_auto_estimate_recovers_tof_background(tmp_path):
    project = ed.Project()
    data_path = ed.download_data(id=17, destination=str(tmp_path))
    project.experiments.add_from_data_path(
        name='sim_si',
        data_path=data_path,
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
    )
    experiment = project.experiments['sim_si']
    experiment.excluded_regions.create(id='1', start=0, end=55000)
    experiment.excluded_regions.create(id='2', start=105500, end=200000)

    experiment.background.auto_estimate()

    points = list(experiment.background)
    heights = np.array([p.y.value for p in points])
    # Sparse, non-negative anchors on the real TOF pattern (different beam
    # mode and a curved/decaying regime), confirming the single arpls
    # default holds across beam modes.
    assert 2 <= len(points) < 100
    assert np.all(heights >= 0)
    # The hand-placed TOF background is flat at ~0.01; recovered stays small.
    assert float(np.median(heights)) < 5.0
