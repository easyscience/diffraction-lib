# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_background_type_info():
    from easydiffraction.datablocks.experiment.categories.background.chebyshev import (
        ChebyshevPolynomialBackground,
    )
    from easydiffraction.datablocks.experiment.categories.background.line_segment import (
        LineSegmentBackground,
    )

    assert LineSegmentBackground.type_info.tag == 'line-segment'
    assert LineSegmentBackground.type_info.description == 'Linear interpolation between points'

    assert ChebyshevPolynomialBackground.type_info.tag == 'chebyshev'
    assert ChebyshevPolynomialBackground.type_info.description == 'Chebyshev polynomial background'
