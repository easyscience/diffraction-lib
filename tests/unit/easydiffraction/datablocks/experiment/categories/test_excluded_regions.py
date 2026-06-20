# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_excluded_regions_add_updates_datastore_and_cif():
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.categories.excluded_regions import ExcludedRegions

    # Minimal fake datastore
    full_x = np.array([0.0, 1.0, 2.0, 3.0])
    full_meas = np.array([10.0, 11.0, 12.0, 13.0])
    full_meas_su = np.array([1.0, 1.0, 1.0, 1.0])
    ds = SimpleNamespace(
        unfiltered_x=full_x,
        _items=list(full_x),  # point count for the apply-skip signature
        full_x=full_x,
        full_meas=full_meas,
        full_meas_su=full_meas_su,
        excluded=np.zeros_like(full_x, dtype=bool),
        x=full_x.copy(),
        meas=full_meas.copy(),
        meas_su=full_meas_su.copy(),
    )

    def set_calc_status(status):
        # _set_calc_status sets excluded to the inverse
        ds.excluded = ~status
        # Filter x, meas, meas_su to only include non-excluded points
        ds.x = ds.full_x[status]
        ds.meas = ds.full_meas[status]
        ds.meas_su = ds.full_meas_su[status]

    ds._set_calc_status = set_calc_status

    coll = ExcludedRegions()
    # stitch in a parent with data
    object.__setattr__(coll, '_parent', SimpleNamespace(data=ds))

    coll.create(start=1.0, end=2.0)
    # Call _update() to apply exclusions
    coll._update()

    # Second and third points excluded
    assert np.array_equal(ds.excluded, np.array([False, True, True, False]))
    assert np.array_equal(ds.x, np.array([0.0, 3.0]))
    assert np.array_equal(ds.meas, np.array([10.0, 13.0]))

    # CIF loop includes header tags
    cif = coll.as_cif
    assert 'loop_' in cif
    assert '_excluded_region.start' in cif
    assert '_excluded_region.end' in cif


def _fake_excluded_regions(npts=4):
    """Excluded-regions collection wired to a minimal fake datastore.

    The datastore counts ``_set_calc_status`` calls so tests can assert
    when the mask is (re)applied vs skipped.
    """
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.categories.excluded_regions import ExcludedRegions

    full_x = np.arange(float(npts))
    ds = SimpleNamespace(unfiltered_x=full_x, _items=list(full_x), apply_count=0)

    def set_calc_status(status):
        ds.apply_count += 1
        ds.last_status = np.asarray(status)

    ds._set_calc_status = set_calc_status
    coll = ExcludedRegions()
    object.__setattr__(coll, '_parent', SimpleNamespace(data=ds))
    return coll, ds


def test_excluded_skip_under_minimizer_when_unchanged():
    coll, ds = _fake_excluded_regions()
    coll.create(start=1.0, end=2.0)
    coll._update(called_by_minimizer=False)  # initial apply
    assert ds.apply_count == 1
    # Unchanged grid + regions: minimizer iterations must skip the re-apply
    coll._update(called_by_minimizer=True)
    coll._update(called_by_minimizer=True)
    assert ds.apply_count == 1


def test_excluded_non_minimizer_always_reapplies():
    coll, ds = _fake_excluded_regions()
    coll.create(start=1.0, end=2.0)
    coll._update(called_by_minimizer=False)
    coll._update(called_by_minimizer=False)
    assert ds.apply_count == 2


def test_excluded_reapplies_under_minimizer_when_region_changes():
    coll, ds = _fake_excluded_regions()
    coll.create(start=1.0, end=2.0)
    coll._update(called_by_minimizer=False)
    assert ds.apply_count == 1
    region = next(iter(coll.values()))
    region.end = 3.0  # region bound changed -> signature changes
    coll._update(called_by_minimizer=True)
    assert ds.apply_count == 2
    assert np.array_equal(ds.last_status, np.array([True, False, False, False]))


def test_excluded_reapplies_under_minimizer_when_grid_changes():
    coll, ds = _fake_excluded_regions(npts=4)
    coll.create(start=1.0, end=2.0)
    coll._update(called_by_minimizer=False)
    assert ds.apply_count == 1
    # Grid replaced (different point count) -> signature changes -> re-apply
    ds.unfiltered_x = np.arange(5.0)
    ds._items = list(np.arange(5.0))
    coll._update(called_by_minimizer=True)
    assert ds.apply_count == 2
