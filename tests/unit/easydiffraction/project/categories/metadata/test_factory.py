# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_project_info_factory_default_and_create():
    from easydiffraction.project.categories.metadata.default import ProjectMetadata
    from easydiffraction.project.categories.metadata.factory import ProjectMetadataFactory

    assert ProjectMetadataFactory.default_tag() == 'default'
    assert 'default' in ProjectMetadataFactory.supported_tags()

    info = ProjectMetadataFactory.create(
        'default',
        name='beer',
        title='Beer title',
        description='Some description',
    )

    assert isinstance(info, ProjectMetadata)
    assert info.name == 'beer'
    assert info.title == 'Beer title'


def test_project_info_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.metadata.factory import ProjectMetadataFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        ProjectMetadataFactory.create('missing')
