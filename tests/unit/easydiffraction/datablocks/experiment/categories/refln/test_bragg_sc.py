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


def test_refln_data_point_defaults():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import Refln

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
    assert not hasattr(pt, 'wavelength')
    assert pt._identity.category_code == 'refln'


def test_tof_refln_data_point_has_wavelength():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import TofRefln

    pt = TofRefln()
    assert pt.wavelength.value == 0.0
    assert pt.intensity_calc.value == 0.0


def test_refln_data_collection_create_and_properties():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import TofReflnData

    coll = TofReflnData()

    h = np.array([1.0, 2.0, 0.0])
    k = np.array([0.0, 1.0, 0.0])
    l = np.array([0.0, 0.0, 2.0])
    coll._create_items_set_hkl_and_id(h, k, l)

    assert len(coll._items) == 3
    np.testing.assert_array_almost_equal(coll.index_h, h)
    np.testing.assert_array_almost_equal(coll.index_k, k)
    np.testing.assert_array_almost_equal(coll.index_l, l)
    assert coll._items[0].id.value == '1'
    assert coll._items[1].id.value == '2'
    assert coll._items[2].id.value == '3'

    meas = np.array([50.0, 100.0, 150.0])
    coll._set_intensity_meas(meas)
    np.testing.assert_array_almost_equal(coll.intensity_meas, meas)

    su = np.array([5.0, 10.0, 15.0])
    coll._set_intensity_meas_su(su)
    np.testing.assert_array_almost_equal(coll.intensity_meas_su, su)

    wl = np.array([0.84, 0.84, 0.84])
    coll._set_wavelength(wl)
    np.testing.assert_array_almost_equal(coll.wavelength, wl)

    calc = np.array([48.0, 102.0, 148.0])
    coll._set_intensity_calc(calc)
    np.testing.assert_array_almost_equal(coll.intensity_calc, calc)


def test_cwl_refln_data_has_no_wavelength():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import CwlReflnData

    coll = CwlReflnData()
    assert not hasattr(coll, 'wavelength')
    assert not hasattr(coll, '_set_wavelength')


def test_refln_data_d_spacing_and_stol():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import CwlReflnData

    coll = CwlReflnData()
    h = np.array([1.0, 2.0])
    k = np.array([0.0, 0.0])
    l = np.array([0.0, 0.0])
    coll._create_items_set_hkl_and_id(h, k, l)

    d = np.array([5.43, 2.715])
    coll._set_d_spacing(d)
    np.testing.assert_array_almost_equal(coll.d_spacing, d)

    stol = np.array([0.092, 0.184])
    coll._set_sin_theta_over_lambda(stol)
    np.testing.assert_array_almost_equal(coll.sin_theta_over_lambda, stol)


def test_refln_items_resolve_experiment_datablock_name():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import CwlReflnData

    coll = CwlReflnData()
    coll._parent = _experiment_stub('sc-exp')

    coll._create_items_set_hkl_and_id(
        np.array([1.0, 2.0]),
        np.array([0.0, 0.0]),
        np.array([0.0, 1.0]),
    )

    param = coll._items[0].intensity_meas
    assert param._identity.datablock_entry_name == 'sc-exp'
    assert param.unique_name == 'sc-exp.refln.1.intensity_meas'


def test_refln_data_type_info():
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import CwlReflnData
    from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import TofReflnData

    assert CwlReflnData.type_info.tag == 'bragg-sc-cwl'
    assert CwlReflnData.type_info.description == 'Bragg CWL single-crystal reflection data'
    assert TofReflnData.type_info.tag == 'bragg-sc-tof'
    assert TofReflnData.type_info.description == 'Bragg TOF single-crystal reflection data'
