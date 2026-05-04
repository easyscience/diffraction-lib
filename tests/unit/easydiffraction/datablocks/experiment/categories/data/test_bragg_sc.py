# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory


def test_bragg_sc_module_reexports_single_crystal_reflection_types():
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import Refln
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import ReflnData
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import Refln as NewRefln
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import (
        ReflnData as NewReflnData,
    )

    assert Refln is NewRefln
    assert ReflnData is NewReflnData


def test_bragg_sc_module_registers_refln_data_with_data_factory():
    obj = DataFactory.create('bragg-sc')
    assert obj.__class__.__name__ == 'ReflnData'
