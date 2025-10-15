import numpy as np


def test_excluded_regions_add_updates_datastore_and_cif():
    from types import SimpleNamespace
    from easydiffraction.experiments.categories.excluded_regions import ExcludedRegion, ExcludedRegions

    # Minimal fake datastore
    full_x = np.array([0.0, 1.0, 2.0, 3.0])
    full_meas = np.array([10.0, 11.0, 12.0, 13.0])
    full_meas_su = np.array([1.0, 1.0, 1.0, 1.0])
    ds = SimpleNamespace(
        full_x=full_x,
        full_meas=full_meas,
        full_meas_su=full_meas_su,
        excluded=np.zeros_like(full_x, dtype=bool),
        x=full_x.copy(),
        meas=full_meas.copy(),
        meas_su=full_meas_su.copy(),
    )

    coll = ExcludedRegions()
    # stitch in a parent with datastore
    object.__setattr__(coll, '_parent', SimpleNamespace(datastore=ds))

    r = ExcludedRegion(start=1.0, end=2.0)
    coll.add(r)

    # Second and third points excluded
    assert np.all(ds.excluded == np.array([False, True, True, False]))
    assert np.all(ds.x == np.array([0.0, 3.0]))
    assert np.all(ds.meas == np.array([10.0, 13.0]))

    # CIF loop includes header tags
    cif = coll.as_cif
    assert 'loop_' in cif and '_excluded_region.start' in cif and '_excluded_region.end' in cif
