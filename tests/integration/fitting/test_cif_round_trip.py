# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration tests for experiment CIF round-trip (as_cif → from_cif_str)."""

from __future__ import annotations

import tempfile

from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction import download_data
from easydiffraction.core.variable import Parameter

TEMP_DIR = tempfile.gettempdir()


def _build_fully_configured_experiment() -> ExperimentFactory:
    """
    Create a fully configured powder CWL neutron experiment.

    Includes instrument, peak profile, background, excluded regions,
    linked phases, and measured data.

    Returns
    -------
    ExperimentBase
        A complete experiment ready for CIF round-trip testing.
    """
    data_path = download_data(id=3, destination=TEMP_DIR)
    expt = ExperimentFactory.from_data_path(
        name='hrpt',
        data_path=data_path,
    )
    # Instrument
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0.6225

    # Peak profile
    expt.peak.broad_gauss_u = 0.0834
    expt.peak.broad_gauss_v = -0.1168
    expt.peak.broad_gauss_w = 0.123
    expt.peak.broad_lorentz_x = 0.0
    expt.peak.broad_lorentz_y = 0.0797

    # Background
    expt.background.create(id='1', x=10, y=170)
    expt.background.create(id='2', x=80, y=160)
    expt.background.create(id='3', x=165, y=170)

    # Excluded regions
    expt.excluded_regions.create(id='1', start=0, end=5)
    expt.excluded_regions.create(id='2', start=165, end=180)

    # Linked phases
    expt.linked_phases.create(id='lbco', scale=9.0)

    # Free parameters
    expt.instrument.calib_twotheta_offset.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.background['1'].y.free = True
    expt.background['2'].y.free = True
    expt.background['3'].y.free = True

    return expt


def _collect_param_values(expt: object) -> dict[str, object]:
    """
    Collect all parameter values from an experiment.

    Returns a dict keyed by unique_name with the parameter value.
    Skips raw data parameters (pd_data.*) since those are large arrays.
    """
    result = {}
    for p in expt.parameters:
        uname = getattr(p, 'unique_name', None)
        if uname is None:
            continue
        # Skip raw data arrays
        if 'pd_data.' in uname:
            continue
        result[uname] = p.value
    return result


def _collect_free_flags(expt: object) -> dict[str, bool]:
    """Return {unique_name: free} for fittable parameters."""
    return {
        p.unique_name: p.free
        for p in expt.parameters
        if isinstance(p, Parameter) and not p.unique_name.startswith('pd_data.')
    }


# ------------------------------------------------------------------
#  Test 1: Experiment CIF round-trip preserves all parameter values
# ------------------------------------------------------------------


def test_experiment_cif_round_trip_preserves_parameters() -> None:
    """
    Every parameter value must survive an as_cif → from_cif_str cycle.

    Creates a fully configured experiment, serialises it to CIF,
    reconstructs from CIF, and compares all parameter values.
    """
    original = _build_fully_configured_experiment()

    # Serialise
    cif_str = original.as_cif

    # Reconstruct
    loaded = ExperimentFactory.from_cif_str(cif_str)

    # Compare parameter values
    orig_params = _collect_param_values(original)
    loaded_params = _collect_param_values(loaded)

    for name, orig_val in orig_params.items():
        assert name in loaded_params, f'Parameter {name} missing after round-trip'
        loaded_val = loaded_params[name]
        if isinstance(orig_val, float):
            assert_almost_equal(
                loaded_val,
                orig_val,
                decimal=4,
                err_msg=f'Value mismatch for {name}',
            )
        else:
            assert loaded_val == orig_val, (
                f'Value mismatch for {name}: expected {orig_val!r}, got {loaded_val!r}'
            )


# ------------------------------------------------------------------
#  Test 2: Free flags survive the round-trip
# ------------------------------------------------------------------


def test_experiment_cif_round_trip_preserves_free_flags() -> None:
    """
    Free flags must survive an as_cif → from_cif_str cycle.

    Parameters marked as free on the original experiment must also be
    free on the reconstructed experiment.
    """
    original = _build_fully_configured_experiment()

    cif_str = original.as_cif
    loaded = ExperimentFactory.from_cif_str(cif_str)

    orig_free = _collect_free_flags(original)
    loaded_free = _collect_free_flags(loaded)

    for name, orig_flag in orig_free.items():
        if name in loaded_free:
            assert loaded_free[name] == orig_flag, (
                f'Free flag mismatch for {name}: expected {orig_flag}, got {loaded_free[name]}'
            )


# ------------------------------------------------------------------
#  Test 3: Categories survive the round-trip
# ------------------------------------------------------------------


def test_experiment_cif_round_trip_preserves_categories() -> None:
    """
    Category collections (background, excluded regions, linked phases)
    must preserve their item count after a round-trip.
    """
    original = _build_fully_configured_experiment()

    cif_str = original.as_cif
    loaded = ExperimentFactory.from_cif_str(cif_str)

    # Background points
    assert len(loaded.background) == len(original.background), (
        f'Background count mismatch: '
        f'expected {len(original.background)}, got {len(loaded.background)}'
    )

    # Excluded regions
    assert len(loaded.excluded_regions) == len(original.excluded_regions), (
        f'Excluded regions count mismatch: '
        f'expected {len(original.excluded_regions)}, '
        f'got {len(loaded.excluded_regions)}'
    )

    # Linked phases
    assert len(loaded.linked_phases) == len(original.linked_phases), (
        f'Linked phases count mismatch: '
        f'expected {len(original.linked_phases)}, '
        f'got {len(loaded.linked_phases)}'
    )


# ------------------------------------------------------------------
#  Test 4: Data points survive the round-trip
# ------------------------------------------------------------------


def test_experiment_cif_round_trip_preserves_data() -> None:
    """
    Measured data points must survive an as_cif → from_cif_str cycle.

    The number of data points and the first/last values must match.
    """
    original = _build_fully_configured_experiment()

    cif_str = original.as_cif
    loaded = ExperimentFactory.from_cif_str(cif_str)

    # Number of data points
    assert len(loaded.data) == len(original.data), (
        f'Data point count mismatch: expected {len(original.data)}, got {len(loaded.data)}'
    )

    # First and last data point two_theta and intensity_meas
    orig_first = next(iter(original.data.values()))
    loaded_first = next(iter(loaded.data.values()))
    orig_last = list(original.data.values())[-1]
    loaded_last = list(loaded.data.values())[-1]

    assert_almost_equal(
        loaded_first.two_theta.value,
        orig_first.two_theta.value,
        decimal=4,
        err_msg='First data point two_theta mismatch',
    )
    assert_almost_equal(
        loaded_last.two_theta.value,
        orig_last.two_theta.value,
        decimal=4,
        err_msg='Last data point two_theta mismatch',
    )
    assert_almost_equal(
        loaded_first.intensity_meas.value,
        orig_first.intensity_meas.value,
        decimal=2,
        err_msg='First data point intensity_meas mismatch',
    )


# ------------------------------------------------------------------
#  Test 5: Structure CIF round-trip preserves all parameter values
# ------------------------------------------------------------------


def test_structure_cif_round_trip_preserves_parameters() -> None:
    """
    Every structure parameter must survive an as_cif → from_cif_str
    cycle, including atom sites with symmetry constraints.
    """
    original = StructureFactory.from_scratch(name='lbco')
    original.space_group.name_h_m = 'P m -3 m'
    original.cell.length_a = 3.8909
    original.atom_sites.create(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.5,
    )
    original.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.5,
    )
    original.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.5,
    )
    # Apply symmetry constraints before serialisation
    original._update_categories()

    cif_str = original.as_cif
    loaded = StructureFactory.from_cif_str(cif_str)
    # Apply symmetry on loaded to match original state
    loaded._update_categories()

    # Compare cell parameters
    assert_almost_equal(
        loaded.cell.length_a.value,
        original.cell.length_a.value,
        decimal=6,
    )

    # Compare space group
    assert loaded.space_group.name_h_m.value == original.space_group.name_h_m.value

    # Compare atom sites count and values
    assert len(loaded.atom_sites) == len(original.atom_sites)
    for label in ['La', 'Co', 'O']:
        orig_site = original.atom_sites[label]
        loaded_site = loaded.atom_sites[label]
        assert_almost_equal(
            loaded_site.fract_x.value,
            orig_site.fract_x.value,
            decimal=6,
            err_msg=f'fract_x mismatch for {label}',
        )
        assert_almost_equal(
            loaded_site.adp_iso.value,
            orig_site.adp_iso.value,
            decimal=4,
            err_msg=f'adp_iso mismatch for {label}',
        )
