# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_display_handler_is_frozen_value_object():
    import dataclasses

    import pytest

    from easydiffraction.core.display_handler import DisplayHandler

    handler = DisplayHandler(
        display_name='2theta',
        display_units='deg',
        latex_name=r'$2\theta$',
        latex_units=r'$^\circ$',
    )

    assert dataclasses.asdict(handler) == {
        'display_name': '2theta',
        'display_units': 'deg',
        'latex_name': r'$2\theta$',
        'latex_units': r'$^\circ$',
    }
    with pytest.raises(dataclasses.FrozenInstanceError):
        handler.display_name = 'other'
