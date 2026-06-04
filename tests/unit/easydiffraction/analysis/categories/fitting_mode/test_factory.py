# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_fitting_mode_factory_default_and_create():
    from easydiffraction.analysis.categories.fitting_mode.default import FittingMode
    from easydiffraction.analysis.categories.fitting_mode.factory import FittingModeFactory

    assert FittingModeFactory.default_tag() == 'default'
    assert 'default' in FittingModeFactory.supported_tags()

    fitting_mode = FittingModeFactory.create('default')

    assert isinstance(fitting_mode, FittingMode)


def test_fitting_mode_factory_rejects_unknown_tag():
    from easydiffraction.analysis.categories.fitting_mode.factory import FittingModeFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        FittingModeFactory.create('missing')
