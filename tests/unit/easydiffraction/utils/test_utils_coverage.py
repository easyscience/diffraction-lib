# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Supplementary unit tests for easydiffraction.utils.utils — coverage gaps."""

import urllib.request

import numpy as np
import pytest


# --- _validate_url -----------------------------------------------------------


def test_validate_url_accepts_http():
    import easydiffraction.utils.utils as MUT

    # Should not raise for http
    MUT._validate_url('http://example.com/file.cif')


def test_validate_url_accepts_https():
    import easydiffraction.utils.utils as MUT

    # Should not raise for https
    MUT._validate_url('https://example.com/file.cif')


# --- _filename_for_id_from_url ------------------------------------------------


def test_filename_for_id_from_url_with_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_url(12, 'https://example.com/data/file.xye')
    assert result == 'ed-12.xye'


def test_filename_for_id_from_url_cif_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_url('3', 'https://example.com/path/model.cif')
    assert result == 'ed-3.cif'


def test_filename_for_id_from_url_no_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_url(7, 'https://example.com/path/noext')
    assert result == 'ed-7'


# --- _normalize_known_hash ----------------------------------------------------


def test_normalize_known_hash_none():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash(None) is None


def test_normalize_known_hash_empty_string():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('') is None


def test_normalize_known_hash_placeholder():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('sha256:...') is None


def test_normalize_known_hash_placeholder_uppercase():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('SHA256:...') is None


def test_normalize_known_hash_valid():
    import easydiffraction.utils.utils as MUT

    h = 'sha256:abc123'
    assert MUT._normalize_known_hash(h) == h


def test_normalize_known_hash_strips_whitespace():
    import easydiffraction.utils.utils as MUT

    h = '  sha256:abc123  '
    assert MUT._normalize_known_hash(h) == 'sha256:abc123'


# --- stripped_package_version -------------------------------------------------


def test_stripped_package_version_returns_public():
    import easydiffraction.utils.utils as MUT

    # numpy is always installed in the test env
    result = MUT.stripped_package_version('numpy')
    assert result is not None
    assert '+' not in result  # no local segment


def test_stripped_package_version_missing_package():
    import easydiffraction.utils.utils as MUT

    result = MUT.stripped_package_version('__definitely_not_installed__')
    assert result is None


def test_stripped_package_version_strips_local(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '1.2.3+local456')
    result = MUT.stripped_package_version('mypkg')
    assert result == '1.2.3'


def test_stripped_package_version_invalid_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: 'not-a-version!!!')
    result = MUT.stripped_package_version('mypkg')
    assert result == 'not-a-version!!!'


# --- _is_dev_version ---------------------------------------------------------


def test_is_dev_version_none_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: None)
    assert MUT._is_dev_version('easydiffraction') is True


# --- _safe_urlopen ------------------------------------------------------------


def test_safe_urlopen_rejects_non_https_string():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(ValueError, match='Only https URLs are permitted'):
        MUT._safe_urlopen('http://example.com/file')


def test_safe_urlopen_rejects_non_https_request():
    import easydiffraction.utils.utils as MUT

    req = urllib.request.Request('http://example.com/file')
    with pytest.raises(ValueError, match='Only https URLs are permitted'):
        MUT._safe_urlopen(req)


def test_safe_urlopen_rejects_invalid_type():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match='Expected str or Request, got int'):
        MUT._safe_urlopen(42)


# --- _resolve_tutorial_url ----------------------------------------------------


def test_resolve_tutorial_url_replaces_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '1.0.0')
    template = 'https://example.com/{version}/tutorials/ed-1.ipynb'
    result = MUT._resolve_tutorial_url(template)
    assert result == 'https://example.com/1.0.0/tutorials/ed-1.ipynb'


def test_resolve_tutorial_url_dev(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: 'dev')
    template = 'https://example.com/{version}/tutorials/ed-2.ipynb'
    result = MUT._resolve_tutorial_url(template)
    assert result == 'https://example.com/dev/tutorials/ed-2.ipynb'


# --- render_cif ---------------------------------------------------------------


def test_render_cif_outputs_cif_text(capsys):
    import easydiffraction.utils.utils as MUT

    cif_text = '_cell_length_a 5.0\n_cell_length_b 6.0'
    MUT.render_cif(cif_text)
    out = capsys.readouterr().out
    assert '_cell_length_a 5.0' in out
    assert '_cell_length_b 6.0' in out


# --- sin_theta_over_lambda_to_d_spacing ---------------------------------------


def test_sin_theta_over_lambda_to_d_scalar():
    import easydiffraction.utils.utils as MUT

    # d = 1 / (2 * sin_theta_over_lambda)
    result = MUT.sin_theta_over_lambda_to_d_spacing(0.25)
    assert np.isclose(result, 2.0)


def test_sin_theta_over_lambda_to_d_array():
    import easydiffraction.utils.utils as MUT

    vals = np.array([0.1, 0.25, 0.5])
    expected = 1.0 / (2 * vals)
    result = MUT.sin_theta_over_lambda_to_d_spacing(vals)
    assert np.allclose(result, expected)


def test_sin_theta_over_lambda_to_d_zero_returns_nan():
    import easydiffraction.utils.utils as MUT

    result = MUT.sin_theta_over_lambda_to_d_spacing(np.array([0.0]))
    assert np.isnan(result[0])


def test_sin_theta_over_lambda_to_d_negative_returns_nan():
    import easydiffraction.utils.utils as MUT

    result = MUT.sin_theta_over_lambda_to_d_spacing(np.array([-0.1]))
    assert np.isnan(result[0])


# --- str_to_ufloat additional branches ----------------------------------------


def test_str_to_ufloat_none_returns_default():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat(None, default=5.0)
    assert np.isclose(u.nominal_value, 5.0)
    assert np.isnan(u.std_dev)


def test_str_to_ufloat_none_no_default_raises():
    import easydiffraction.utils.utils as MUT

    # When s=None and default=None, ufloat(None, nan) raises TypeError
    with pytest.raises(TypeError):
        MUT.str_to_ufloat(None)


def test_str_to_ufloat_empty_brackets_zero_uncertainty():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat('3.566()')
    assert np.isclose(u.nominal_value, 3.566)
    assert np.isclose(u.std_dev, 0.0)


def test_str_to_ufloat_invalid_string_returns_default():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat('not_a_number', default=99.0)
    assert np.isclose(u.nominal_value, 99.0)
    assert np.isnan(u.std_dev)


# --- tof_to_d additional branches ---------------------------------------------


def test_tof_to_d_type_error_non_array():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'tof' must be a NumPy array"):
        MUT.tof_to_d([10.0, 20.0], offset=0.0, linear=1.0, quad=0.0)


def test_tof_to_d_type_error_non_numeric_offset():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'offset' must be a real number"):
        MUT.tof_to_d(np.array([10.0]), offset='bad', linear=1.0, quad=0.0)


def test_tof_to_d_type_error_non_numeric_linear():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'linear' must be a real number"):
        MUT.tof_to_d(np.array([10.0]), offset=0.0, linear=None, quad=0.0)


def test_tof_to_d_both_linear_and_quad_zero():
    import easydiffraction.utils.utils as MUT

    tof = np.array([1.0, 2.0])
    result = MUT.tof_to_d(tof, offset=0.0, linear=0.0, quad=0.0)
    assert np.all(np.isnan(result))


def test_tof_to_d_negative_discriminant():
    import easydiffraction.utils.utils as MUT

    # Choose coefficients that produce a negative discriminant:
    # disc = linear^2 - 4*quad*(offset - tof) < 0
    # linear=0, quad=1, offset=10, tof=5 → disc = 0 - 4*1*(10-5) = -20 < 0
    tof = np.array([5.0])
    result = MUT.tof_to_d(tof, offset=10.0, linear=0.0, quad=1.0)
    assert np.all(np.isnan(result))


def test_tof_to_d_linear_negative_tof_minus_offset_gives_nan():
    import easydiffraction.utils.utils as MUT

    # linear case: d = (tof - offset) / linear → negative when tof < offset
    tof = np.array([1.0])
    result = MUT.tof_to_d(tof, offset=10.0, linear=1.0, quad=0.0)
    assert np.all(np.isnan(result))


# --- download_data ------------------------------------------------------------


def test_download_data_unknown_id(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {'1': {'path': 'data.xye', 'hash': None}}
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)
    with pytest.raises(KeyError, match='Unknown dataset id=999'):
        MUT.download_data(id=999)


def test_download_data_already_exists_no_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file
    (tmp_path / 'ed-1.xye').write_text('existing data')

    result = MUT.download_data(id=1, destination=str(tmp_path), overwrite=False)
    assert result == str(tmp_path / 'ed-1.xye')
    out = capsys.readouterr().out
    assert 'already present' in out
    assert (tmp_path / 'ed-1.xye').read_text() == 'existing data'


def test_download_data_success(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Mock pooch.retrieve to create the file
    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('x y e')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data(id=1, destination=str(tmp_path))
    assert result == str(tmp_path / 'ed-1.xye')
    assert (tmp_path / 'ed-1.xye').exists()
    out = capsys.readouterr().out
    assert 'downloaded' in out


def test_download_data_overwrite_existing(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file
    (tmp_path / 'ed-1.xye').write_text('old data')

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('new data')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data(id=1, destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'ed-1.xye')
    assert (tmp_path / 'ed-1.xye').read_text() == 'new data'


def test_download_data_no_description(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': 'sha256:...',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file so we hit the no-overwrite short-circuit
    (tmp_path / 'ed-1.xye').write_text('existing')

    result = MUT.download_data(id=1, destination=str(tmp_path))
    assert result == str(tmp_path / 'ed-1.xye')
    out = capsys.readouterr().out
    assert 'Data #1' in out


# --- download_tutorial with overwrite=True ------------------------------------


def test_download_tutorial_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
            'title': 'Quick Start',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    # Create existing file
    (tmp_path / 'ed-1.ipynb').write_text('old content')

    class DummyResp:
        def read(self):
            return b'{"cells": ["new"]}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MUT, '_safe_urlopen', lambda url: DummyResp())

    result = MUT.download_tutorial(id=1, destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'ed-1.ipynb')
    assert 'new' in (tmp_path / 'ed-1.ipynb').read_text()
