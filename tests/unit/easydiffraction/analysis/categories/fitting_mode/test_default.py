# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


class _Parent:
    def __init__(self, fitting_mode):
        self.fitting_mode = fitting_mode
        self.swap_calls: list[str] = []

    def _supported_filters_for(self, category: object) -> dict[str, object]:
        assert category is self.fitting_mode
        return {}

    def _swap_fitting_mode(self, value: str) -> None:
        self.swap_calls.append(value)
        self.fitting_mode._type.value = value


def test_fitting_mode_defaults():
    from easydiffraction.analysis.categories.fitting_mode.default import FittingMode

    fitting_mode = FittingMode()

    assert fitting_mode.type_info.tag == 'default'
    assert fitting_mode._identity.category_code == 'fitting_mode'
    assert fitting_mode.type == 'single'


def test_fitting_mode_selector_delegates_to_parent():
    from easydiffraction.analysis.categories.fitting_mode.default import FittingMode

    fitting_mode = FittingMode()
    parent = _Parent(fitting_mode)
    fitting_mode._parent = parent

    fitting_mode.type = 'joint'

    assert parent.swap_calls == ['joint']
    assert fitting_mode.type == 'joint'


def test_fitting_mode_supported_types_include_all_modes():
    from easydiffraction.analysis.categories.fitting_mode.default import FittingMode

    supported = FittingMode()._supported_types({})
    tags = [tag for tag, _description in supported]

    assert tags == ['single', 'joint', 'sequential']


def test_fitting_mode_from_cif_restores_value_without_parent():
    from easydiffraction.analysis.categories.fitting_mode.default import FittingMode

    fitting_mode = FittingMode()
    block = gemmi.cif.read_string(
        'data_test\n_fitting_mode.type sequential\n',
    ).sole_block()

    fitting_mode.from_cif(block)

    assert fitting_mode.type == 'sequential'
