# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.crystallography.crystallography as MUT

    expected_module_name = 'easydiffraction.crystallography.crystallography'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name
