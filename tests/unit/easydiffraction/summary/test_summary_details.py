# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

# -- Stub classes for test_summary_crystallographic_and_experimental ---


class _Val:
    def __init__(self, v):
        self.value = v


class _CellParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class _Cell:
    @property
    def parameters(self):
        return [
            _CellParam('length_a', 5.4321),
            _CellParam('angle_alpha', 90.0),
        ]


class _Site:
    def __init__(self, label, typ, x, y, z, occ, biso):
        self.label = _Val(label)
        self.type_symbol = _Val(typ)
        self.fract_x = _Val(x)
        self.fract_y = _Val(y)
        self.fract_z = _Val(z)
        self.occupancy = _Val(occ)
        self.adp_iso = _Val(biso)


class _Model:
    def __init__(self):
        self.name = 'phaseA'
        self.space_group = type('SG', (), {'name_h_m': _Val('P 1')})()
        self.cell = _Cell()
        self.atom_sites = [_Site('Na1', 'Na', 0.1, 0.2, 0.3, 1.0, 0.5)]


class _Instr:
    def __init__(self):
        self.setup_wavelength = _Val(1.23456)
        self.calib_twotheta_offset = _Val(0.12345)

    def _public_attrs(self):
        return ['setup_wavelength', 'calib_twotheta_offset']


class _Peak:
    def __init__(self):
        self.broad_gauss_u = _Val(0.1)
        self.broad_gauss_v = _Val(0.2)
        self.broad_gauss_w = _Val(0.3)
        self.broad_lorentz_x = _Val(0.4)
        self.broad_lorentz_y = _Val(0.5)

    def _public_attrs(self):
        return [
            'broad_gauss_u',
            'broad_gauss_v',
            'broad_gauss_w',
            'broad_lorentz_x',
            'broad_lorentz_y',
        ]


class _Expt:
    def __init__(self):
        self.name = 'exp1'
        typ = type(
            'T',
            (),
            {
                'sample_form': _Val('powder'),
                'radiation_probe': _Val('neutron'),
                'beam_mode': _Val('constant wavelength'),
            },
        )
        self.type = typ()
        self.instrument = _Instr()
        self.peak_profile_type = 'pseudo-Voigt'
        self.peak = _Peak()

    def _public_attrs(self):
        return ['instrument', 'peak_profile_type', 'peak']


class _Info:
    title = 'T'
    description = ''


class _StubProject:
    def __init__(self):
        self.info = _Info()
        self.structures = {'phaseA': _Model()}
        self.experiments = {'exp1': _Expt()}

        class A:
            current_minimizer = 'lmfit'

            class R:
                reduced_chi_square = 1.23

            fit_results = R()

        self.analysis = A()


# ----------------------------------------------------------------------


def test_summary_crystallographic_and_experimental_sections(capsys):
    from easydiffraction.summary.summary import Summary

    s = Summary(_StubProject())
    # Run both sections separately for targeted assertions
    s.show_crystallographic_data()
    s.show_experimental_data()
    out = capsys.readouterr().out

    # Crystallographic section
    assert 'CRYSTALLOGRAPHIC DATA' in out
    assert '🧩 phaseA' in out
    assert 'Space group' in out
    assert 'P 1' in out
    # Cell parameter names are shortened by the implementation (e.g., 'length_a' -> 'a')
    assert 'Cell parameters' in out
    assert ' a ' in out
    assert ' alpha ' in out
    assert 'Atom sites' in out
    assert 'Na1' in out
    assert 'Na' in out

    # Experimental section
    assert 'EXPERIMENTS' in out
    assert '🔬 exp1' in out
    assert 'powder' in out
    assert 'neutron' in out
    assert 'constant wavelength' in out
    assert 'Wavelength' in out
    assert '1.23456'[:6] in out
    assert '2θ offset' in out
    assert '0.12345'[:6] in out
    assert 'Profile type' in out
    assert 'pseudo-Voigt' in out
    assert 'Peak broadening (Gaussian)' in out
    assert 'Peak broadening (Lorentzian)' in out
