import pytest
import numpy as np
import importlib

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.utils.utils

def test_module_import():
    import easydiffraction.utils.utils as MUT
    expected_module_name = "easydiffraction.utils.utils"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_twotheta_to_d_scalar_and_array():
    import easydiffraction.utils.utils as MUT
    wavelength = 1.54
    # scalar
    expected_scalar = wavelength / (2 * np.sin(np.radians(30 / 2)))
    actual_scalar = MUT.twotheta_to_d(30.0, wavelength)
    assert np.isclose(expected_scalar, actual_scalar)
    # array
    twotheta = np.array([10.0, 20.0, 40.0])
    expected_array = wavelength / (2 * np.sin(np.radians(twotheta / 2)))
    actual_array = MUT.twotheta_to_d(twotheta, wavelength)
    assert np.allclose(expected_array, actual_array)


def test_tof_to_d_linear_case():
    import easydiffraction.utils.utils as MUT
    tof = np.array([10.0, 20.0, 30.0])
    offset, linear, quad = 2.0, 4.0, 0.0
    expected = (tof - offset) / linear
    actual = MUT.tof_to_d(tof, offset, linear, quad)
    assert np.allclose(expected, actual)


def test_tof_to_d_quadratic_case_smallest_positive_root():
    import easydiffraction.utils.utils as MUT
    # Model: TOF = quad * d^2, with offset=linear=0
    quad = 2.0
    tof = np.array([2.0, 8.0, 18.0])  # roots: sqrt(tof/quad)
    expected = np.sqrt(tof / quad)
    actual = MUT.tof_to_d(tof, offset=0.0, linear=0.0, quad=quad)
    assert np.allclose(expected, actual, equal_nan=False)


def test_str_to_ufloat_parsing_nominal_and_esd():
    import easydiffraction.utils.utils as MUT
    u = MUT.str_to_ufloat("3.566(2)")
    expected = np.array([3.566, 0.002])
    actual = np.array([u.nominal_value, u.std_dev])
    assert np.allclose(expected, actual)


def test_str_to_ufloat_no_esd_defaults_nan():
    import easydiffraction.utils.utils as MUT
    u = MUT.str_to_ufloat("1.23")
    expected_value = 1.23
    actual_value = u.nominal_value
    # uncertainty is NaN when not specified
    assert (np.isclose(expected_value, actual_value) and np.isnan(u.std_dev))


def test_get_value_from_xye_header(tmp_path):
    import easydiffraction.utils.utils as MUT
    text = "DIFC = 123.45 two_theta = 67.89\nrest of file\n"
    p = tmp_path / "file.xye"
    p.write_text(text)
    expected_difc = 123.45
    expected_two_theta = 67.89
    actual = np.array([
        MUT.get_value_from_xye_header(p, "DIFC"),
        MUT.get_value_from_xye_header(p, "two_theta"),
    ])
    expected = np.array([expected_difc, expected_two_theta])
    assert np.allclose(expected, actual)


def test_validate_url_rejects_non_http_https():
    import easydiffraction.utils.utils as MUT
    with pytest.raises(ValueError):
        MUT._validate_url("ftp://example.com/file")


def test_is_github_ci_env_true(monkeypatch):
    import easydiffraction.utils.utils as MUT
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    expected = True
    actual = MUT.is_github_ci()
    assert expected == actual


def test_package_version_missing_package_returns_none():
    import easydiffraction.utils.utils as MUT
    expected = None
    actual = MUT.package_version("__definitely_not_installed__")
    assert expected == actual


def test_is_notebook_false_in_plain_env(monkeypatch):
    import easydiffraction.utils.utils as MUT
    # Ensure no IPython and not PyCharm
    monkeypatch.setattr(MUT, 'IPython', None)
    monkeypatch.setenv('PYCHARM_HOSTED', '', prepend=False)
    assert MUT.is_notebook() is False


def test_is_pycharm_and_is_colab(monkeypatch):
    import easydiffraction.utils.utils as MUT
    # PyCharm
    monkeypatch.setenv('PYCHARM_HOSTED', '1')
    assert MUT.is_pycharm() is True
    # Colab detection when module is absent -> False
    assert MUT.is_colab() is False


def test_render_table_terminal_branch(capsys, monkeypatch):
    import easydiffraction.utils.utils as MUT
    monkeypatch.setattr(MUT, 'is_notebook', lambda: False)
    MUT.render_table(columns_data=[[1, 2], [3, 4]], columns_alignment=['left', 'left'])
    out = capsys.readouterr().out
    # fancy_outline uses box-drawing characters; accept a couple of expected ones
    assert ('╒' in out and '╕' in out) or ('┌' in out and '┐' in out)


def test_fetch_tutorial_list_handles_missing_release(monkeypatch):
    import easydiffraction.utils.utils as MUT

    # Force _get_release_info to return None twice (tag & latest) → empty list
    monkeypatch.setattr(MUT, '_get_release_info', lambda tag: None)
    notebooks = MUT.fetch_tutorial_list()
    assert notebooks == []


def test_fetch_tutorial_list_no_asset(monkeypatch):
    import easydiffraction.utils.utils as MUT

    release_info = {'assets': []}
    monkeypatch.setattr(MUT, '_get_release_info', lambda tag: release_info)
    notebooks = MUT.fetch_tutorial_list()
    assert notebooks == []


def test_show_version_prints(capsys, monkeypatch):
    import easydiffraction.utils.utils as MUT
    monkeypatch.setattr(MUT, 'package_version', lambda name: '1.2.3+abc')
    MUT.show_version()
    out = capsys.readouterr().out
    assert '1.2.3+abc' in out


def test_extract_notebooks_from_asset_with_inmemory_zip(monkeypatch):
    import io, zipfile
    import easydiffraction.utils.utils as MUT

    # Build an in-memory zip with .ipynb files
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        zf.writestr('dir/a.ipynb', '{}')
        zf.writestr('b.ipynb', '{}')
        zf.writestr('c.txt', 'x')
    data = mem.getvalue()

    class DummyResp:
        def __init__(self, b):
            self._b = b
        def read(self):
            return self._b
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MUT, '_safe_urlopen', lambda url: DummyResp(data))
    out = MUT._extract_notebooks_from_asset('https://example.com/tut.zip')
    # returns sorted basenames of .ipynb
    assert out == ['a.ipynb', 'b.ipynb']
