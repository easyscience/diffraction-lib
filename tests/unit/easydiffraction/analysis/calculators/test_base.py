# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.analysis.calculators.base as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.base'
