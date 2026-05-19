# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_project_info_factory_default_and_create():
    from easydiffraction.project.categories.info.default import ProjectInfo
    from easydiffraction.project.categories.info.factory import ProjectInfoFactory

    assert ProjectInfoFactory.default_tag() == 'default'
    assert 'default' in ProjectInfoFactory.supported_tags()

    info = ProjectInfoFactory.create(
        'default',
        name='beer',
        title='Beer title',
        description='Some description',
    )

    assert isinstance(info, ProjectInfo)
    assert info.name == 'beer'
    assert info.title == 'Beer title'


def test_project_info_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.info.factory import ProjectInfoFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        ProjectInfoFactory.create('missing')
