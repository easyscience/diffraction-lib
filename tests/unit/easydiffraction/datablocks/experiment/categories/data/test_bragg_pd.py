# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def _experiment_stub(name='exp1'):
    from easydiffraction.core.identity import Identity

    class ExperimentStub:
        def __init__(self):
            self._parent = None
            self._identity = Identity(owner=self)
            self._identity.datablock_entry_name = lambda: name

    return ExperimentStub()


def test_pd_cwl_data_point_defaults():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlDataPoint

    pt = PdCwlDataPoint()
    assert pt.id.value == '0'
    assert pt.d_spacing.value == 0.0
    assert pt.two_theta.value == 0.0
    assert pt.intensity_meas.value == 0.0
    assert pt.intensity_meas_su.value == 1.0
    assert pt.intensity_calc.value == 0.0
    assert pt.intensity_bkg.value == 0.0
    assert pt.calc_status.value == 'incl'
    assert pt._identity.category_code == 'data'


def test_pd_tof_data_point_defaults():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdTofDataPoint

    pt = PdTofDataPoint()
    assert pt.id.value == '0'
    assert pt.d_spacing.value == 0.0
    assert pt.time_of_flight.value == 0.0
    assert pt.intensity_meas.value == 0.0
    assert pt.intensity_meas_su.value == 1.0
    assert pt.intensity_calc.value == 0.0
    assert pt.intensity_bkg.value == 0.0
    assert pt.calc_status.value == 'incl'
    assert pt._identity.category_code == 'data'


def test_pd_cwl_data_collection_create_and_properties():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()

    # Create items with x-coordinate (two_theta) values
    x_vals = np.array([10.0, 20.0, 30.0])
    coll._create_items_set_xcoord_and_id(x_vals)

    assert len(coll._items) == 3

    # Check two_theta property (returns calc items only, all included)
    np.testing.assert_array_almost_equal(coll.two_theta, x_vals)

    # Check x is alias for two_theta
    np.testing.assert_array_almost_equal(coll.x, coll.two_theta)

    # Check unfiltered_x returns all items
    np.testing.assert_array_almost_equal(coll.unfiltered_x, x_vals)

    # Set and read measured intensities
    meas = np.array([100.0, 200.0, 300.0])
    coll._set_intensity_meas(meas)
    np.testing.assert_array_almost_equal(coll.intensity_meas, meas)

    # Set and read standard uncertainties
    su = np.array([10.0, 20.0, 30.0])
    coll._set_intensity_meas_su(su)
    np.testing.assert_array_almost_equal(coll.intensity_meas_su, su)

    # Check point IDs are set
    assert coll._items[0].id.value == '1'
    assert coll._items[1].id.value == '2'
    assert coll._items[2].id.value == '3'


def test_pd_tof_data_collection_create_and_properties():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdTofData

    coll = PdTofData()

    # Create items with x-coordinate (time_of_flight) values
    x_vals = np.array([1000.0, 2000.0, 3000.0])
    coll._create_items_set_xcoord_and_id(x_vals)

    assert len(coll._items) == 3

    # Check time_of_flight property
    np.testing.assert_array_almost_equal(coll.time_of_flight, x_vals)

    # Check x is alias for time_of_flight
    np.testing.assert_array_almost_equal(coll.x, coll.time_of_flight)

    # Check unfiltered_x returns all items
    np.testing.assert_array_almost_equal(coll.unfiltered_x, x_vals)

    # Check point IDs are set
    assert coll._items[0].id.value == '1'
    assert coll._items[2].id.value == '3'


def test_pd_data_items_resolve_experiment_datablock_name():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()
    coll._parent = _experiment_stub('hrpt')

    coll._create_items_set_xcoord_and_id(np.array([10.0, 20.0]))

    param = coll._items[0].intensity_meas
    assert param._identity.datablock_entry_name == 'hrpt'
    assert param.unique_name == 'hrpt.data.1.intensity_meas'


def test_pd_data_calc_status_exclusion():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()

    x_vals = np.array([10.0, 20.0, 30.0, 40.0])
    coll._create_items_set_xcoord_and_id(x_vals)
    coll._set_intensity_meas(np.array([100.0, 200.0, 300.0, 400.0]))
    coll._set_intensity_meas_su(np.array([10.0, 20.0, 30.0, 40.0]))

    # Exclude the second and third points
    coll._set_calc_status([True, False, False, True])

    # calc_status should reflect the change
    assert np.array_equal(coll.calc_status, np.array(['incl', 'excl', 'excl', 'incl']))

    # x should only return included points
    np.testing.assert_array_almost_equal(coll.x, np.array([10.0, 40.0]))

    # intensity_meas should only return included points
    np.testing.assert_array_almost_equal(coll.intensity_meas, np.array([100.0, 400.0]))


def test_pd_data_calc_cache_invalidated_on_public_calc_status_write():
    # Warming the included-point cache and then flipping a single
    # point's status through the public descriptor must not leave the
    # cache stale.
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()
    x_vals = np.array([10.0, 20.0, 30.0, 40.0])
    coll._create_items_set_xcoord_and_id(x_vals)
    coll._set_intensity_meas(np.array([100.0, 200.0, 300.0, 400.0]))

    # Warm the cached mask/list.
    np.testing.assert_array_almost_equal(coll.x, x_vals)

    # Public per-point descriptor write.
    coll['2'].calc_status.value = 'excl'

    np.testing.assert_array_almost_equal(coll.x, np.array([10.0, 30.0, 40.0]))
    np.testing.assert_array_almost_equal(coll.intensity_meas, np.array([100.0, 300.0, 400.0]))


def test_pd_data_calc_cache_invalidated_on_public_point_mutation():
    # Warming the cache and then mutating the point set through public
    # collection APIs (remove, clear) must rebuild the cache.
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()
    coll._create_items_set_xcoord_and_id(np.array([10.0, 20.0, 30.0]))

    # Warm the cached mask/list.
    np.testing.assert_array_almost_equal(coll.x, np.array([10.0, 20.0, 30.0]))

    # Public point removal.
    del coll['1']
    np.testing.assert_array_almost_equal(coll.x, np.array([20.0, 30.0]))

    # Public clear.
    coll.clear()
    assert coll.x.size == 0


def test_pd_cwl_data_type_info():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdTofData

    assert PdCwlData.type_info.tag == 'bragg-pd'
    assert PdCwlData.type_info.description == 'Bragg powder CWL data'

    assert PdTofData.type_info.tag == 'bragg-pd-tof'
    assert PdTofData.type_info.description == 'Bragg powder TOF data'


def test_pd_data_intensity_meas_su_zero_replacement():
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData

    coll = PdCwlData()
    x_vals = np.array([10.0, 20.0, 30.0])
    coll._create_items_set_xcoord_and_id(x_vals)

    # Set su with near-zero values — those should be replaced by 1.0
    coll._set_intensity_meas_su(np.array([0.0, 0.00001, 5.0]))
    su = coll.intensity_meas_su
    assert su[0] == 1.0  # replaced
    assert su[1] == 1.0  # replaced
    assert su[2] == 5.0  # kept
