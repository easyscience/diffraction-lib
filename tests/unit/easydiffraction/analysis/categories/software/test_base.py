# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_software_role_serializes_name_version_and_url():
    from easydiffraction.analysis.categories.software.base import SoftwareRole

    role = SoftwareRole(role_name='calculator', description='Calculator')
    role.name = 'cryspy'
    role.version = '1.0'
    role.url = 'https://example.invalid/cryspy'

    assert [parameter.name for parameter in role.parameters] == [
        'calculator_name',
        'calculator_version',
        'calculator_url',
    ]
    assert '_software.calculator_name cryspy' in role.as_cif
    assert '_software.calculator_version 1.0' in role.as_cif
    assert '_software.calculator_url https://example.invalid/cryspy' in role.as_cif
