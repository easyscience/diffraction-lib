# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.project.project_metadata as MUT

    expected_module_name = 'easydiffraction.project.project_metadata'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name
