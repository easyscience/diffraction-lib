# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.analysis.minimizers.enums as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.enums'


def test_enum_members():
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert MinimizerTypeEnum.LMFIT == 'lmfit'
    assert MinimizerTypeEnum.LMFIT_LEASTSQ == 'lmfit (leastsq)'
    assert MinimizerTypeEnum.LMFIT_LEAST_SQUARES == 'lmfit (least_squares)'
    assert MinimizerTypeEnum.DFOLS == 'dfols'


def test_enum_default():
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert MinimizerTypeEnum.default() is MinimizerTypeEnum.LMFIT_LEASTSQ


def test_enum_descriptions():
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    for member in MinimizerTypeEnum:
        desc = member.description()
        assert isinstance(desc, str)
        assert len(desc) > 0
