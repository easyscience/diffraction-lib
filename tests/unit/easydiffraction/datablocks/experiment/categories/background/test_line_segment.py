# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.background import line_segment
from easydiffraction.datablocks.experiment.categories.background.line_segment import (
    LineSegmentBackground,
)


def test_line_segment_background_calculate_and_cif():
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.categories.background.line_segment import (
        LineSegmentBackground,
    )

    # Create mock parent with data
    x = np.array([0.0, 1.0, 2.0])
    mock_data = SimpleNamespace(x=x, _bkg=None)
    mock_data._set_intensity_bkg = lambda y: setattr(mock_data, '_bkg', y)
    mock_parent = SimpleNamespace(data=mock_data)

    bkg = LineSegmentBackground()
    object.__setattr__(bkg, '_parent', mock_parent)

    # No points -> zeros
    bkg._update()
    assert np.allclose(mock_data._bkg, [0.0, 0.0, 0.0])

    # Add two points -> linear interpolation
    bkg.create(id='1', position=0.0, intensity=0.0)
    bkg.create(id='2', position=2.0, intensity=4.0)
    bkg._update()
    assert np.allclose(mock_data._bkg, [0.0, 2.0, 4.0])

    # CIF loop has correct header and rows
    cif = bkg.as_cif
    assert 'loop_' in cif
    assert '_background.position' in cif
    assert '_background.intensity' in cif


def _make_background(x, intensity_meas, intensity_calc=None, intensity_bkg=None):
    n = len(x)
    calc = np.zeros(n) if intensity_calc is None else intensity_calc
    bkg = np.zeros(n) if intensity_bkg is None else intensity_bkg
    data = SimpleNamespace(
        x=np.asarray(x, dtype=float),
        intensity_meas=np.asarray(intensity_meas, dtype=float),
        intensity_calc=np.asarray(calc, dtype=float),
        intensity_bkg=np.asarray(bkg, dtype=float),
    )
    bkg_obj = LineSegmentBackground()
    object.__setattr__(bkg_obj, '_parent', SimpleNamespace(data=data))
    return bkg_obj


def _synthetic(n=300, seed=0):
    x = np.linspace(0.0, 10.0, n)
    y = 5.0 + 0.3 * x + 8.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2))
    rng = np.random.default_rng(seed)
    return x, y + rng.normal(0.0, 0.05, size=n)


def _fake_log(records, key):
    methods = {
        'info': lambda self, m, *a, **k: None,
        'warning': lambda self, m, *a, **k: None,
    }
    methods[key] = lambda self, m, *a, **k: records.append(str(m))
    return type('FakeLog', (), methods)()


def test_auto_estimate_creates_sequential_fixed_points():
    x, y = _synthetic(seed=1)
    bkg = _make_background(x, y)
    bkg.auto_estimate()
    assert len(bkg) >= 2
    ids = [p.id.value for p in bkg._items]
    assert ids == [str(i) for i in range(1, len(bkg) + 1)]
    assert all(p.intensity.free is False for p in bkg._items)


def test_auto_estimate_overwrites_and_refixes():
    x, y = _synthetic(seed=2)
    bkg = _make_background(x, y)
    bkg.create(id='99', position=1.0, intensity=1.0)
    bkg._items[0].intensity.free = True  # user freed a hand-added point
    bkg.auto_estimate()
    ids = [p.id.value for p in bkg._items]
    assert '99' not in ids
    assert ids[0] == '1'
    assert all(p.intensity.free is False for p in bkg._items)


def test_auto_estimate_replace_notice(monkeypatch):
    records = []
    monkeypatch.setattr(line_segment, 'log', _fake_log(records, 'info'))
    x, y = _synthetic(seed=3)
    bkg = _make_background(x, y)
    bkg.auto_estimate()  # first call: nothing to replace
    assert not [r for r in records if 'Replacing' in r]
    records.clear()
    bkg.auto_estimate()  # second call: replace notice
    assert any('Replacing' in r for r in records)


def test_auto_estimate_model_guided_path():
    x, y = _synthetic(seed=4)
    calc = 8.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2)) + 6.0
    bkg = _make_background(x, y, intensity_calc=calc, intensity_bkg=np.full_like(x, 6.0))
    bkg.auto_estimate(use_model=True)
    assert len(bkg) >= 2
    assert all(p.intensity.free is False for p in bkg._items)


def test_auto_estimate_accepts_each_method():
    x, y = _synthetic(seed=5)
    for method in ('auto', 'snip', 'arpls', 'fabc'):
        bkg = _make_background(x, y)
        bkg.auto_estimate(method=method)
        assert len(bkg) >= 2


def test_auto_estimate_rejects_invalid_method():
    x, y = _synthetic(seed=6)
    bkg = _make_background(x, y)
    with pytest.raises(ValueError, match='method'):
        bkg.auto_estimate(method='nope')


def test_auto_estimate_validates_overrides():
    x, y = _synthetic(seed=7)
    bkg = _make_background(x, y)
    with pytest.raises(ValueError, match='width'):
        bkg.auto_estimate(width=-1.0)
    with pytest.raises(ValueError, match='n_points'):
        bkg.auto_estimate(n_points=1)


def test_auto_estimate_empty_data_warns(monkeypatch):
    records = []
    monkeypatch.setattr(line_segment, 'log', _fake_log(records, 'warning'))
    bkg = _make_background(np.array([]), np.array([]))
    bkg.auto_estimate()
    assert len(bkg) == 0
    assert any('No active data' in r for r in records)


def _patch_helper(monkeypatch, captured, anchors=None):
    """Replace the estimator helper with a fake that records its inputs."""

    def fake(x, y, *, method, peaks, width, smoothness, n_points):
        captured.update(
            x=np.asarray(x),
            y=np.asarray(y),
            method=method,
            peaks=(None if peaks is None else np.asarray(peaks)),
            width=width,
            n_points=n_points,
        )
        rows = anchors if anchors is not None else np.array([[x[0], 1.0], [x[-1], 1.0]])
        return SimpleNamespace(anchors=rows, width=5.0)

    monkeypatch.setattr(line_segment, 'estimate', SimpleNamespace(estimate_background_curve=fake))


def test_auto_estimate_applies_pending_excluded_regions_before_sampling(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData
    from easydiffraction.datablocks.experiment.categories.excluded_regions import ExcludedRegions

    captured = {}
    _patch_helper(monkeypatch, captured)
    data = PdCwlData()
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    intensity_meas = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    data._create_items_set_xcoord_and_id(x)
    data._set_intensity_meas(intensity_meas)
    data._set_intensity_meas_su(np.ones_like(x))

    excluded_regions = ExcludedRegions()
    parent = SimpleNamespace(data=data, excluded_regions=excluded_regions)
    object.__setattr__(data, '_parent', parent)
    object.__setattr__(excluded_regions, '_parent', parent)

    obj = LineSegmentBackground()
    object.__setattr__(obj, '_parent', parent)
    excluded_regions.create(id='1', start=1.0, end=3.0)

    np.testing.assert_array_equal(data.calc_status, np.full(x.shape, 'incl', dtype=object))

    obj.auto_estimate()

    np.testing.assert_array_equal(
        data.calc_status,
        np.array(['incl', 'excl', 'excl', 'excl', 'incl'], dtype=object),
    )
    np.testing.assert_allclose(captured['x'], np.array([0.0, 4.0]))
    np.testing.assert_allclose(captured['y'], np.array([10.0, 50.0]))
    np.testing.assert_allclose(
        [point.position.value for point in obj._items],
        np.array([0.0, 4.0]),
    )


def test_auto_estimate_respects_existing_calc_status_without_regions(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.data.bragg_pd import PdCwlData
    from easydiffraction.datablocks.experiment.categories.excluded_regions import ExcludedRegions

    captured = {}
    _patch_helper(monkeypatch, captured)
    data = PdCwlData()
    x = np.array([0.0, 1.0, 2.0])
    intensity_meas = np.array([10.0, 20.0, 30.0])
    data._create_items_set_xcoord_and_id(x)
    data._set_intensity_meas(intensity_meas)
    data._set_intensity_meas_su(np.ones_like(x))
    data._set_calc_status([True, False, True])

    excluded_regions = ExcludedRegions()
    parent = SimpleNamespace(data=data, excluded_regions=excluded_regions)
    object.__setattr__(data, '_parent', parent)
    object.__setattr__(excluded_regions, '_parent', parent)

    obj = LineSegmentBackground()
    object.__setattr__(obj, '_parent', parent)

    obj.auto_estimate()

    np.testing.assert_array_equal(
        data.calc_status,
        np.array(['incl', 'excl', 'incl'], dtype=object),
    )
    np.testing.assert_allclose(captured['x'], np.array([0.0, 2.0]))
    np.testing.assert_allclose(captured['y'], np.array([10.0, 30.0]))


def test_auto_estimate_forwards_resolved_method(monkeypatch):
    captured = {}
    _patch_helper(monkeypatch, captured)
    x, y = _synthetic(seed=20)
    for requested, expected in (
        ('auto', 'arpls'),
        ('snip', 'snip'),
        ('arpls', 'arpls'),
        ('fabc', 'fabc'),
    ):
        _make_background(x, y).auto_estimate(method=requested)
        assert captured['method'] == expected


def test_auto_estimate_model_guided_passes_peak_subtracted_inputs(monkeypatch):
    captured = {}
    _patch_helper(monkeypatch, captured)
    x = np.linspace(0.0, 10.0, 200)
    peak = 40.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2))
    bkg = np.full_like(x, 90.0)
    meas = bkg + peak + 3.0
    calc = bkg + peak  # populated model -> model-guided path
    obj = _make_background(x, meas, intensity_calc=calc, intensity_bkg=bkg)
    obj.auto_estimate(use_model=True)
    # Helper receives the peak-subtracted measured intensities, not the raw data.
    assert np.allclose(captured['y'], meas - (calc - bkg))
    # ...and a non-empty forbidden mask built from the model peak.
    assert captured['peaks'] is not None
    assert captured['peaks'].any()


def test_auto_estimate_data_only_passes_raw_inputs(monkeypatch):
    captured = {}
    _patch_helper(monkeypatch, captured)
    x, meas = _synthetic(seed=21)
    calc = meas.copy()  # even with a populated model present...
    obj = _make_background(x, meas, intensity_calc=calc)
    obj.auto_estimate(use_model=False)  # ...use_model=False forces the data-only path
    assert np.allclose(captured['y'], meas)
    assert captured['peaks'] is None


def test_auto_estimate_clips_heights_to_measured(monkeypatch):
    captured = {}
    x = np.linspace(0.0, 10.0, 101)
    meas = np.full_like(x, 50.0)
    anchors = np.array([[x[0], 80.0], [x[50], -10.0], [x[-1], 30.0]])
    _patch_helper(monkeypatch, captured, anchors=anchors)
    obj = _make_background(x, meas)
    obj.auto_estimate()
    heights = [p.intensity.value for p in obj._items]
    # Absolute anchor heights clipped to [0, measured(=50)] -- no residual add-back.
    assert heights == [50.0, 0.0, 30.0]
