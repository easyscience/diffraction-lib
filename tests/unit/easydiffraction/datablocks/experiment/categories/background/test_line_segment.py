# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from types import SimpleNamespace

from easydiffraction.datablocks.experiment.categories.background import line_segment
from easydiffraction.datablocks.experiment.categories.background.line_segment import LineSegmentBackground


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
    bkg.create(id='1', x=0.0, y=0.0)
    bkg.create(id='2', x=2.0, y=4.0)
    bkg._update()
    assert np.allclose(mock_data._bkg, [0.0, 2.0, 4.0])

    # CIF loop has correct header and rows
    cif = bkg.as_cif
    assert 'loop_' in cif
    assert '_pd_background.line_segment_X' in cif
    assert '_pd_background.line_segment_intensity' in cif


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
    assert all(p.y.free is False for p in bkg._items)


def test_auto_estimate_overwrites_and_refixes():
    x, y = _synthetic(seed=2)
    bkg = _make_background(x, y)
    bkg.create(id='99', x=1.0, y=1.0)
    bkg._items[0].y.free = True  # user freed a hand-added point
    bkg.auto_estimate()
    ids = [p.id.value for p in bkg._items]
    assert '99' not in ids
    assert ids[0] == '1'
    assert all(p.y.free is False for p in bkg._items)


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
    assert all(p.y.free is False for p in bkg._items)


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
