# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration tests for anisotropic ADP fitting (Tb2Ti2O7, HEiDi)."""

import tempfile

import pytest

import easydiffraction as ed

TEMP_DIR = tempfile.gettempdir()


def _setup_tbti_project():
    """Create a Tb2Ti2O7 single-crystal project ready for fitting."""
    project = ed.Project()

    model_path = ed.download_data(id=20, destination=TEMP_DIR)
    project.structures.add_from_cif_path(model_path)

    data_path = ed.download_data(id=19, destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='heidi',
        data_path=data_path,
        sample_form='single crystal',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
    )
    experiment = project.experiments['heidi']
    experiment.linked_crystal.id = 'tbti'
    experiment.linked_crystal.scale = 1.0
    experiment.instrument.setup_wavelength = 0.793
    experiment.extinction.mosaicity = 35000
    experiment.extinction.radius = 10

    return project


@pytest.mark.fast
def test_iso_then_aniso_fit() -> None:
    """Fit Uiso first, then switch to Uani and fit again."""
    project = _setup_tbti_project()
    s = project.structures['tbti']
    e = project.experiments['heidi']

    # Step 1: Set all atoms to Uiso with zero starting values
    for name in ('Tb', 'Ti', 'O1', 'O2'):
        s.atom_sites[name].adp_type = 'Uiso'
        s.atom_sites[name].adp_iso = 0.0

    # Free parameters for isotropic fit
    s.atom_sites['O1'].fract_x.free = True
    s.atom_sites['Ti'].occupancy.free = True
    s.atom_sites['O1'].occupancy.free = True
    s.atom_sites['O2'].occupancy.free = True
    for name in ('Tb', 'Ti', 'O1', 'O2'):
        s.atom_sites[name].adp_iso.free = True
    e.linked_crystal.scale.free = True
    e.extinction.radius.free = True

    # Fit isotropic
    project.analysis.fit(verbosity='silent')
    chi2_iso = project.analysis.fit_results.reduced_chi_square
    assert chi2_iso < 20.0

    # Record iso values
    u_iso_tb = s.atom_sites['Tb'].adp_iso.value
    assert u_iso_tb > 0.0

    # Step 2: Switch Tb, Ti, O1 to Uani (O2 stays Uiso)
    for name in ('Tb', 'Ti', 'O1'):
        s.atom_sites[name].adp_type = 'Uani'

    # Free anisotropic parameters
    s.atom_site_aniso['Tb'].adp_11.free = True
    s.atom_site_aniso['Tb'].adp_12.free = True
    s.atom_site_aniso['Ti'].adp_11.free = True
    s.atom_site_aniso['Ti'].adp_12.free = True
    s.atom_site_aniso['O1'].adp_11.free = True
    s.atom_site_aniso['O1'].adp_22.free = True
    s.atom_site_aniso['O1'].adp_23.free = True

    # Fit anisotropic
    project.analysis.fit(verbosity='silent')
    chi2_aniso = project.analysis.fit_results.reduced_chi_square

    # Anisotropic fit should improve (or at least match) chi2
    assert chi2_aniso < chi2_iso + 1.0
    assert chi2_aniso < 10.0

    # Aniso tensor should have non-zero off-diagonal for Tb
    assert abs(s.atom_site_aniso['Tb'].adp_12.value) > 0.0001

    # O2 should still be Uiso
    assert s.atom_sites['O2'].adp_type.value == 'Uiso'

    # CIF should omit O2 from the aniso loop because it remains Uiso
    cif = s.atom_site_aniso.as_cif
    lines = cif.strip().split('\n')
    o2_lines = [l for l in lines if l.strip().startswith('O2')]
    assert not o2_lines


if __name__ == '__main__':
    test_iso_then_aniso_fit()
