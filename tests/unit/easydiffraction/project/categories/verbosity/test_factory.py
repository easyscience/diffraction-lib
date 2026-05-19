# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_verbosity_factory_default_and_create():
    from easydiffraction.project.categories.verbosity.default import Verbosity
    from easydiffraction.project.categories.verbosity.factory import VerbosityFactory

    assert VerbosityFactory.default_tag() == 'default'
    assert 'default' in VerbosityFactory.supported_tags()

    verbosity = VerbosityFactory.create('default')

    assert isinstance(verbosity, Verbosity)


def test_verbosity_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.verbosity.factory import VerbosityFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        VerbosityFactory.create('missing')
