# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from easydiffraction.analysis.calculators.base import PowderReflnRecord
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum


def test_powder_cwl_refln_defaults():
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlRefln

    refln = PowderCwlRefln()

    assert refln.id.value == '0'
    assert refln.phase_id.value == ''
    assert refln.two_theta.value == 0.0
    assert refln.d_spacing.value == 0.0
    assert refln.f_calc.value == 0.0
    assert refln.f_squared_calc.value == 0.0
    assert refln._identity.category_code == 'refln'


def test_powder_cwl_refln_data_replace_from_records_sets_arrays():
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlReflnData

    refln = PowderCwlReflnData()
    refln._replace_from_records([
        PowderReflnRecord(
            phase_id='alpha',
            d_spacing=2.1,
            sin_theta_over_lambda=0.25,
            index_h=1,
            index_k=0,
            index_l=1,
            f_calc=3.0,
            f_squared_calc=9.0,
            two_theta=14.5,
        ),
        PowderReflnRecord(
            phase_id='beta',
            d_spacing=1.5,
            sin_theta_over_lambda=0.33,
            index_h=2,
            index_k=1,
            index_l=0,
            f_calc=4.0,
            f_squared_calc=16.0,
            two_theta=22.0,
        ),
    ])

    assert [item.id.value for item in refln._items] == ['1', '2']
    np.testing.assert_array_equal(refln.phase_id, np.array(['alpha', 'beta']))
    np.testing.assert_allclose(refln.d_spacing, np.array([2.1, 1.5]))
    np.testing.assert_allclose(refln.two_theta, np.array([14.5, 22.0]))
    np.testing.assert_allclose(refln.f_calc, np.array([3.0, 4.0]))
    np.testing.assert_allclose(refln.f_squared_calc, np.array([9.0, 16.0]))


def test_powder_tof_refln_data_replace_from_records_sets_arrays():
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderTofReflnData

    refln = PowderTofReflnData()
    refln._replace_from_records([
        PowderReflnRecord(
            phase_id='gamma',
            d_spacing=3.2,
            sin_theta_over_lambda=0.15,
            index_h=1,
            index_k=1,
            index_l=0,
            f_calc=5.0,
            f_squared_calc=25.0,
            time_of_flight=1200.0,
        )
    ])

    assert [item.id.value for item in refln._items] == ['1']
    np.testing.assert_array_equal(refln.phase_id, np.array(['gamma']))
    np.testing.assert_allclose(refln.time_of_flight, np.array([1200.0]))
    np.testing.assert_allclose(refln.d_spacing, np.array([3.2]))


def test_powder_refln_is_cryspy_only():
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlReflnData
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderTofReflnData

    assert PowderCwlReflnData.calculator_support.calculators == frozenset({CalculatorEnum.CRYSPY})
    assert PowderTofReflnData.calculator_support.calculators == frozenset({CalculatorEnum.CRYSPY})


def test_powder_refln_replace_from_records_rebuilds_index_and_parents():
    from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlReflnData

    refln = PowderCwlReflnData()
    refln._replace_from_records([
        PowderReflnRecord(
            phase_id='alpha',
            d_spacing=2.1,
            sin_theta_over_lambda=0.25,
            index_h=1,
            index_k=0,
            index_l=1,
            f_calc=3.0,
            f_squared_calc=9.0,
            two_theta=14.5,
        )
    ])

    old_item = refln['1']
    assert old_item._parent is refln

    refln._replace_from_records([])

    assert len(refln) == 0
    assert old_item._parent is None
    with pytest.raises(KeyError):
        refln['1']

    refln._replace_from_records([
        PowderReflnRecord(
            phase_id='beta',
            d_spacing=1.5,
            sin_theta_over_lambda=0.33,
            index_h=2,
            index_k=1,
            index_l=0,
            f_calc=4.0,
            f_squared_calc=16.0,
            two_theta=22.0,
        )
    ])

    new_item = refln['1']
    assert new_item is refln._items[0]
    assert new_item._parent is refln
    assert new_item.phase_id.value == 'beta'


def test_powder_refln_round_trips_via_experiment_cif():
    experiment = ExperimentFactory.from_scratch(
        name='powder',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment.refln._replace_from_records([
        PowderReflnRecord(
            phase_id='alpha',
            d_spacing=2.1,
            sin_theta_over_lambda=0.25,
            index_h=1,
            index_k=0,
            index_l=1,
            f_calc=3.0,
            f_squared_calc=9.0,
            two_theta=14.5,
        ),
        PowderReflnRecord(
            phase_id='beta',
            d_spacing=1.5,
            sin_theta_over_lambda=0.33,
            index_h=2,
            index_k=1,
            index_l=0,
            f_calc=4.0,
            f_squared_calc=16.0,
            two_theta=22.0,
        ),
    ])
    experiment._need_categories_update = False

    cif = experiment.as_cif
    loaded = ExperimentFactory.from_cif_str(cif)

    assert '_refln.phase_id' in cif
    assert '_refln.f_calc' in cif
    assert '_refln.f_squared_calc' in cif
    np.testing.assert_array_equal(loaded.refln.phase_id, np.array(['alpha', 'beta']))
    np.testing.assert_allclose(loaded.refln.two_theta, np.array([14.5, 22.0]))
    np.testing.assert_allclose(loaded.refln.f_calc, np.array([3.0, 4.0]))
    np.testing.assert_allclose(loaded.refln.f_squared_calc, np.array([9.0, 16.0]))
