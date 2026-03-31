# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_total_data_point_defaults():
    from easydiffraction.datablocks.experiment.categories.data.total_pd import TotalDataPoint

    pt = TotalDataPoint()
    assert pt.point_id.value == '0'
    assert pt.r.value == 0.0
    assert pt.g_r_meas.value == 0.0
    assert pt.g_r_meas_su.value == 0.0
    assert pt.g_r_calc.value == 0.0
    assert pt.calc_status.value == 'incl'
    assert pt._identity.category_code == 'total_data'


def test_total_data_collection_create_and_properties():
    from easydiffraction.datablocks.experiment.categories.data.total_pd import TotalData

    coll = TotalData()

    # Create items with r values
    r_vals = np.array([1.0, 2.0, 3.0, 4.0])
    coll._create_items_set_xcoord_and_id(r_vals)

    assert len(coll._items) == 4

    # Check x property (returns calc items, all included)
    np.testing.assert_array_almost_equal(coll.x, r_vals)

    # Check unfiltered_x returns all items
    np.testing.assert_array_almost_equal(coll.unfiltered_x, r_vals)

    # Set and read measured G(r)
    g_meas = np.array([0.1, 0.5, 0.3, 0.2])
    coll._set_g_r_meas(g_meas)
    np.testing.assert_array_almost_equal(coll.intensity_meas, g_meas)

    # Set and read su
    g_su = np.array([0.01, 0.05, 0.03, 0.02])
    coll._set_g_r_meas_su(g_su)
    np.testing.assert_array_almost_equal(coll.intensity_meas_su, g_su)

    # Point IDs
    assert coll._items[0].point_id.value == '1'
    assert coll._items[3].point_id.value == '4'


def test_total_data_calc_status_and_exclusion():
    from easydiffraction.datablocks.experiment.categories.data.total_pd import TotalData

    coll = TotalData()
    r_vals = np.array([1.0, 2.0, 3.0, 4.0])
    coll._create_items_set_xcoord_and_id(r_vals)
    coll._set_g_r_meas(np.array([0.1, 0.5, 0.3, 0.2]))

    # Exclude the second and third points
    coll._set_calc_status([True, False, False, True])

    assert np.array_equal(coll.calc_status, np.array(['incl', 'excl', 'excl', 'incl']))

    # x should only return included points
    np.testing.assert_array_almost_equal(coll.x, np.array([1.0, 4.0]))

    # intensity_meas should only return included points
    np.testing.assert_array_almost_equal(coll.intensity_meas, np.array([0.1, 0.2]))


def test_total_data_intensity_bkg_always_zero():
    from easydiffraction.datablocks.experiment.categories.data.total_pd import TotalData

    coll = TotalData()
    r_vals = np.array([1.0, 2.0, 3.0])
    coll._create_items_set_xcoord_and_id(r_vals)

    # Set calc G(r) so intensity_calc is non-empty
    coll._set_g_r_calc(np.array([0.5, 0.6, 0.7]))

    # Background should always be zeros
    bkg = coll.intensity_bkg
    np.testing.assert_array_almost_equal(bkg, np.zeros(3))


def test_total_data_type_info():
    from easydiffraction.datablocks.experiment.categories.data.total_pd import TotalData

    assert TotalData.type_info.tag == 'total-pd'
    assert TotalData.type_info.description == 'Total scattering (PDF) data'
