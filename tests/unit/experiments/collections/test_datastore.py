import numpy as np
import pytest

from easydiffraction.experiments.datastore import DatastoreFactory
from easydiffraction.experiments.datastore import PowderDatastore
from easydiffraction.experiments.datastore import SingleCrystalDatastore


def test_powder_datastore_init():
    ds = PowderDatastore(beam_mode='constant wavelength')
    assert ds.meas is None
    assert ds.meas_su is None
    assert ds.calc is None

    assert ds.beam_mode == 'constant wavelength'
    assert ds.x is None
    assert ds.d is None
    assert ds.bkg is None


def test_powder_datastore_calc():
    ds = PowderDatastore()
    with pytest.raises(TypeError):
        ds.calc = [1, 2, 3]  # Should raise TypeError because list is not allowed
    arr = np.array([1, 2, 3])
    ds.calc = arr
    assert np.array_equal(ds.calc, arr)


def test_single_crystal_datastore_init():
    ds = SingleCrystalDatastore()
    assert ds.meas is None
    assert ds.meas_su is None
    assert ds.calc is None

    assert ds.sin_theta_over_lambda is None
    assert ds.index_h is None
    assert ds.index_k is None
    assert ds.index_l is None


def test_datastore_factory_create_powder():
    ds = DatastoreFactory.create(sample_form='powder')
    assert isinstance(ds, PowderDatastore)


def test_datastore_factory_create_single_crystal():
    ds = DatastoreFactory.create(sample_form='single crystal')
    assert isinstance(ds, SingleCrystalDatastore)


def test_datastore_factory_create_powder_time_of_flight():
    ds = DatastoreFactory.create(sample_form='powder', beam_mode='time-of-flight')
    assert isinstance(ds, PowderDatastore)
    assert ds.beam_mode == 'time-of-flight'


def test_datastore_factory_create_powder_constant_wavelength():
    ds = DatastoreFactory.create(sample_form='powder', beam_mode='constant wavelength')
    assert isinstance(ds, PowderDatastore)
    assert ds.beam_mode == 'constant wavelength'


def test_datastore_factory_create_invalid_sample_form():
    with pytest.raises(ValueError, match="Unsupported sample form: 'invalid'"):
        DatastoreFactory.create(sample_form='invalid')


def test_datastore_factory_create_invalid_beam_mode():
    with pytest.raises(ValueError, match="Unsupported beam mode: 'invalid'"):
        DatastoreFactory.create(beam_mode='invalid')


def test_datastore_factory_cif_mapping_powder_time_of_flight():
    ds = DatastoreFactory.create(
        sample_form='powder',
        beam_mode='time-of-flight',
    )
    desired = {
        'x': '_pd_meas.time_of_flight',
        'meas': '_pd_meas.intensity_total',
        'meas_su': '_pd_meas.intensity_total_su',
    }
    actual = ds._cif_mapping()
    assert actual == desired


def test_datastore_factory_cif_mapping_powder_constant_wavelength():
    ds = DatastoreFactory.create(
        sample_form='powder',
        beam_mode='constant wavelength',
    )
    desired = {
        'x': '_pd_meas.2theta_scan',
        'meas': '_pd_meas.intensity_total',
        'meas_su': '_pd_meas.intensity_total_su',
    }
    actual = ds._cif_mapping()
    assert actual == desired


def test_datastore_factory_cif_mapping_single_crystal():
    ds = DatastoreFactory.create(
        sample_form='single crystal',
        beam_mode='constant wavelength',
    )
    desired = {
        'index_h': '_refln.index_h',
        'index_k': '_refln.index_k',
        'index_l': '_refln.index_l',
        'meas': '_refln.intensity_meas',
        'meas_su': '_refln.intensity_meas_su',
    }
    actual = ds._cif_mapping()
    assert actual == desired


def test_powder_as_cif_constant_wavelength():
    ds = PowderDatastore(beam_mode='constant wavelength')
    ds.x = np.array([1.0, 2.0, 3.0])
    ds.meas = np.array([10.0, 20.0, 30.0])
    ds.meas_su = np.array([0.1, 0.2, 0.3])
    ds.bkg = np.array([0.5, 0.5, 0.5])
    cif = ds.as_cif()
    assert '_pd_meas.2theta_scan' in cif
    assert '_pd_meas.intensity_total' in cif
    assert '_pd_meas.intensity_total_su' in cif


def test_powder_as_cif_time_of_flight():
    ds = PowderDatastore(beam_mode='time-of-flight')
    ds.x = np.array([0.5, 1.0, 1.5])
    ds.meas = np.array([15.0, 25.0, 35.0])
    ds.meas_su = np.array([0.15, 0.25, 0.35])
    ds.bkg = np.array([0.4, 0.4, 0.4])
    cif = ds.as_cif()
    assert '_pd_meas.time_of_flight' in cif
    assert '_pd_meas.intensity_total' in cif
    assert '_pd_meas.intensity_total_su' in cif


def test_single_crystal_as_cif():
    ds = SingleCrystalDatastore()
    ds.sin_theta_over_lambda = np.array([0.1, 0.2])
    ds.index_h = np.array([1, 0])
    ds.index_k = np.array([0, 1])
    ds.index_l = np.array([0, 0])
    ds.meas = np.array([100, 200])
    ds.meas_su = np.array([10, 20])
    cif = ds.as_cif()
    assert '_refln.index_h' in cif
    assert '_refln.index_k' in cif
    assert '_refln.index_l' in cif
    assert '_refln.intensity_meas' in cif
    assert '_refln.intensity_meas_su' in cif


def test_as_cif_truncation():
    ds = PowderDatastore()
    ds.x = np.arange(10)
    ds.meas = np.arange(10) * 10
    ds.meas_su = np.arange(10) * 0.1
    ds.bkg = np.arange(10) * 0.5

    cif = ds.as_cif(max_points=2)

    # It should contain CIF headers
    assert '_pd_meas.2theta_scan' in cif
    assert '_pd_meas.intensity_total' in cif
    assert '_pd_meas.intensity_total_su' in cif

    # It should contain first 2 and last 2 rows, but not the middle
    assert '0 0 0.0' in cif
    assert '1 10 0.1' in cif
    assert '3 20 0.2' not in cif
    assert '7 70 0.7' not in cif
    assert '8 80 0.8' in cif
    assert '9 90 0.9' in cif

    # Ellipsis should indicate truncation
    assert '...' in cif
