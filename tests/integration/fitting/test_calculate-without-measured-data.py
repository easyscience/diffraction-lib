# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""End-to-end calculate-without-measured-data integration tests.

Covers the full engine x beam-mode matrix the calculation-without-
measured-data plan requires: both the ``cryspy`` and ``crysfml``
calculators in both constant-wavelength and time-of-flight beam modes.
Each case builds a structure and a data-file-free experiment, sets a
``data_range``, calculates over the generated grid, and confirms the
calculated curve exists while the measured loop stays absent and the
calc-only display path auto-includes the calculated content.
"""

import numpy as np
import pytest

from easydiffraction import Project
from easydiffraction import StructureFactory


def _lbco_structure():
    """Build the LBCO cubic perovskite structure model."""
    model = StructureFactory.from_scratch(name='lbco')
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.88
    model.atom_sites.create(
        id='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.1,
    )
    return model


def _si_structure():
    """Build the silicon structure model (used for the TOF cases)."""
    model = StructureFactory.from_scratch(name='si')
    model.space_group.name_h_m = 'F d -3 m'
    model.space_group.coord_system_code = '2'
    model.cell.length_a = 5.4315
    model.atom_sites.create(
        id='Si',
        type_symbol='Si',
        fract_x=0.125,
        fract_y=0.125,
        fract_z=0.125,
        wyckoff_letter='a',
        adp_iso=0.529,
    )
    return model


def _cwl_calc_only_project():
    """Build a CWL powder project with no measured data."""
    project = Project()
    project.verbosity = 'silent'
    project.structures.add(_lbco_structure())
    project.experiments.create(
        name='sim',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
    )
    experiment = project.experiments['sim']
    experiment.instrument.setup_wavelength = 1.494
    experiment.peak.broad_gauss_u = 0.1
    experiment.peak.broad_gauss_v = -0.1
    experiment.peak.broad_gauss_w = 0.2
    experiment.background.create(id='1', position=10, intensity=20)
    experiment.background.create(id='2', position=60, intensity=20)
    experiment.data_range.two_theta_min = 20.0
    experiment.data_range.two_theta_max = 60.0
    experiment.data_range.two_theta_inc = 0.1
    experiment.linked_structures.create(structure_id='lbco', scale=10.0)
    return project


def _tof_calc_only_project():
    """Build a TOF powder project with no measured data."""
    project = Project()
    project.verbosity = 'silent'
    project.structures.add(_si_structure())
    project.experiments.create(
        name='sim',
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
    )
    experiment = project.experiments['sim']
    experiment.instrument.setup_twotheta_bank = 144.845
    experiment.instrument.calib_d_to_tof_offset = 0.0
    experiment.instrument.calib_d_to_tof_linear = 7476.91
    experiment.instrument.calib_d_to_tof_quadratic = -1.54
    experiment.peak.broad_gauss_sigma_0 = 3.0
    experiment.peak.broad_gauss_sigma_1 = 40.0
    experiment.peak.broad_gauss_sigma_2 = 2.0
    experiment.peak.decay_beta_0 = 0.04221
    experiment.peak.decay_beta_1 = 0.00946
    experiment.peak.rise_alpha_0 = 0.0
    experiment.peak.rise_alpha_1 = 0.5971
    experiment.background.type = 'line-segment'
    experiment.background.create(id='1', position=5000, intensity=20)
    experiment.background.create(id='2', position=15000, intensity=20)
    experiment.data_range.time_of_flight_min = 5000.0
    experiment.data_range.time_of_flight_max = 15000.0
    experiment.data_range.time_of_flight_inc = 5.0
    experiment.linked_structures.create(structure_id='si', scale=10.0)
    return project


def _assert_calc_only(project, *, expt_name, axis_min, axis_max):
    """Calculate and assert calc-only state for one experiment."""
    experiment = project.experiments[expt_name]

    # No measured scan exists for a data-file-free experiment.
    assert experiment._has_measured_data() is False

    project.analysis.calculate()

    # The generated grid spans the requested data_range window.
    x = np.asarray(experiment.data.x, dtype=float)
    assert x.size > 0
    np.testing.assert_array_almost_equal(np.sort(x), x)
    assert x.min() >= axis_min - 1e-6
    assert x.max() <= axis_max + 1e-6

    # A calculated curve is produced over the full generated grid...
    y_calc = np.asarray(experiment.data.intensity_calc, dtype=float)
    assert y_calc.size == x.size
    assert np.all(np.isfinite(y_calc))
    assert np.nanmax(y_calc) > 0.0

    # ...while the measured loop stays absent (no phantom zero-filled
    # measured curve).
    assert experiment._has_measured_data() is False

    # The calc-only display path auto-includes the calculated content
    # and never offers measured content.
    statuses = {
        status.name: status for status in project.display._pattern_option_statuses(expt_name)
    }
    assert statuses['calculated'].available is True
    assert statuses['calculated'].auto_included is True
    assert statuses['measured'].available is False

    # The two-panel calc-only pattern renders without a measured scan.
    project.display.pattern(expt_name=expt_name)


@pytest.mark.parametrize('engine', ['cryspy', 'crysfml'])
def test_calc_only_powder_cwl(engine) -> None:
    if engine == 'crysfml':
        from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

        # Fail clearly if the crysfml backend is not importable.
        assert CrysfmlCalculator.engine_imported is True

    project = _cwl_calc_only_project()
    project.experiments['sim'].calculator.type = engine
    assert project.experiments['sim'].calculator.type == engine

    _assert_calc_only(project, expt_name='sim', axis_min=20.0, axis_max=60.0)


@pytest.mark.parametrize('engine', ['cryspy', 'crysfml'])
def test_calc_only_powder_tof(engine) -> None:
    if engine == 'crysfml':
        from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

        # Fail clearly if the crysfml backend is not importable.
        assert CrysfmlCalculator.engine_imported is True

    project = _tof_calc_only_project()
    project.experiments['sim'].calculator.type = engine
    assert project.experiments['sim'].calculator.type == engine

    _assert_calc_only(project, expt_name='sim', axis_min=5000.0, axis_max=15000.0)


if __name__ == '__main__':
    test_calc_only_powder_cwl('cryspy')
    test_calc_only_powder_cwl('crysfml')
    test_calc_only_powder_tof('cryspy')
    test_calc_only_powder_tof('crysfml')
