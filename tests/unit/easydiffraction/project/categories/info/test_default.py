# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import datetime

import gemmi


def test_project_info_defaults_and_identity():
    from easydiffraction.project.categories.info.default import ProjectInfo

    info = ProjectInfo(name='beer', title='Beer title', description='Some description')

    assert info.type_info.tag == 'default'
    assert info._identity.category_code == 'project'
    assert info.name == 'beer'
    assert info.title == 'Beer title'
    assert info.description == 'Some description'
    assert info.path is None
    assert isinstance(info.created, datetime.datetime)
    assert isinstance(info.last_modified, datetime.datetime)
    assert info.created.tzinfo is not None
    assert info.last_modified.tzinfo is not None


def test_project_info_setters_and_from_cif_restore_fields():
    from easydiffraction.project.categories.info.default import ProjectInfo

    info = ProjectInfo()
    info.description = 'Some   spaced\n description'
    info.path = 'project-dir'

    assert info.description == 'Some spaced description'
    assert info.path is not None
    assert info.path.name == 'project-dir'

    block = gemmi.cif.read_string(
        """data_test
_project.id beer
_project.title 'Beer title'
_project.description 'Some description'
_project.created '17 May 2026 11:13:21'
_project.last_modified '17 May 2026 11:13:51'
""",
    ).sole_block()

    info.from_cif(block)

    assert info.name == 'beer'
    assert info.title == 'Beer title'
    assert info.description == 'Some description'
    assert info.created == datetime.datetime(2026, 5, 17, 11, 13, 21, tzinfo=datetime.UTC)
    assert info.last_modified == datetime.datetime(
        2026,
        5,
        17,
        11,
        13,
        51,
        tzinfo=datetime.UTC,
    )
