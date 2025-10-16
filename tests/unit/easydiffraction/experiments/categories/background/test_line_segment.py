# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_line_segment_background_calculate_and_cif():
    from easydiffraction.experiments.categories.background.line_segment import LineSegment
    from easydiffraction.experiments.categories.background.line_segment import (
        LineSegmentBackground,
    )

    bkg = LineSegmentBackground()
    # No points -> zeros
    x = np.array([0.0, 1.0, 2.0])
    y0 = bkg.calculate(x)
    assert np.allclose(y0, [0.0, 0.0, 0.0])

    # Add two points -> linear interpolation
    p1 = LineSegment(x=0.0, y=0.0)
    p2 = LineSegment(x=2.0, y=4.0)
    bkg.add(p1)
    bkg.add(p2)
    y = bkg.calculate(x)
    assert np.allclose(y, [0.0, 2.0, 4.0])

    # CIF loop has correct header and rows
    cif = bkg.as_cif
    assert (
        'loop_' in cif
        and '_pd_background.line_segment_X' in cif
        and '_pd_background.line_segment_intensity' in cif
    )
