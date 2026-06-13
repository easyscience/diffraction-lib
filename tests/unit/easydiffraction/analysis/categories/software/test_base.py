# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_software_role_serializes_name_version_and_url():
    from easydiffraction.analysis.categories.software.base import SoftwareRole
    from easydiffraction.analysis.enums import SoftwareRoleEnum

    role = SoftwareRole(SoftwareRoleEnum.CALCULATOR)
    role.name = 'cryspy'
    role.version = '1.0'
    role.url = 'https://example.invalid/cryspy'

    assert [parameter.name for parameter in role.parameters] == [
        'id',
        'name',
        'version',
        'url',
    ]
    assert role.id.value == 'calculator'
    assert '_software.id calculator' in role.as_cif
    assert '_software.name cryspy' in role.as_cif
    assert '_software.version 1.0' in role.as_cif
    assert '_software.url https://example.invalid/cryspy' in role.as_cif
