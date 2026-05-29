# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_software_factory_default_and_create():
    from easydiffraction.analysis.categories.software.default import Software
    from easydiffraction.analysis.categories.software.factory import SoftwareFactory

    assert SoftwareFactory.default_tag() == 'default'
    assert 'default' in SoftwareFactory.supported_tags()

    software = SoftwareFactory.create('default')

    assert isinstance(software, Software)


def test_software_factory_rejects_unknown_tag():
    from easydiffraction.analysis.categories.software.factory import SoftwareFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        SoftwareFactory.create('missing')
