# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_refln_data_point_defaults():
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import Refln

    pt = Refln()
    assert pt.id.value == '0'
    assert pt.d_spacing.value == 0.0
    assert pt.sin_theta_over_lambda.value == 0.0
    assert pt.index_h.value == 0.0
    assert pt.index_k.value == 0.0
    assert pt.index_l.value == 0.0
    assert pt.intensity_meas.value == 0.0
    assert pt.intensity_meas_su.value == 0.0
    assert pt.intensity_calc.value == 0.0
    assert pt.wavelength.value == 0.0
    assert pt._identity.category_code == 'refln'


def test_refln_data_collection_create_and_properties():
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import ReflnData

    coll = ReflnData()

    # Create items with hkl
    h = np.array([1.0, 2.0, 0.0])
    k = np.array([0.0, 1.0, 0.0])
    l = np.array([0.0, 0.0, 2.0])
    coll._create_items_set_hkl_and_id(h, k, l)

    assert len(coll._items) == 3

    # Check hkl arrays
    np.testing.assert_array_almost_equal(coll.index_h, h)
    np.testing.assert_array_almost_equal(coll.index_k, k)
    np.testing.assert_array_almost_equal(coll.index_l, l)

    # Check IDs are sequential
    assert coll._items[0].id.value == '1'
    assert coll._items[1].id.value == '2'
    assert coll._items[2].id.value == '3'

    # Set and read measured intensities
    meas = np.array([50.0, 100.0, 150.0])
    coll._set_intensity_meas(meas)
    np.testing.assert_array_almost_equal(coll.intensity_meas, meas)

    # Set and read su
    su = np.array([5.0, 10.0, 15.0])
    coll._set_intensity_meas_su(su)
    np.testing.assert_array_almost_equal(coll.intensity_meas_su, su)

    # Set wavelength
    wl = np.array([0.84, 0.84, 0.84])
    coll._set_wavelength(wl)
    np.testing.assert_array_almost_equal(coll.wavelength, wl)

    # Set and read calculated intensities
    calc = np.array([48.0, 102.0, 148.0])
    coll._set_intensity_calc(calc)
    np.testing.assert_array_almost_equal(coll.intensity_calc, calc)


def test_refln_data_d_spacing_and_stol():
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import ReflnData

    coll = ReflnData()
    h = np.array([1.0, 2.0])
    k = np.array([0.0, 0.0])
    l = np.array([0.0, 0.0])
    coll._create_items_set_hkl_and_id(h, k, l)

    # Set d-spacing
    d = np.array([5.43, 2.715])
    coll._set_d_spacing(d)
    np.testing.assert_array_almost_equal(coll.d_spacing, d)

    # Set sin(theta)/lambda
    stol = np.array([0.092, 0.184])
    coll._set_sin_theta_over_lambda(stol)
    np.testing.assert_array_almost_equal(coll.sin_theta_over_lambda, stol)


def test_refln_data_type_info():
    from easydiffraction.datablocks.experiment.categories.data.bragg_sc import ReflnData

    assert ReflnData.type_info.tag == 'bragg-sc'
    assert ReflnData.type_info.description == 'Bragg single-crystal reflection data'

