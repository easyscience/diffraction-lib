# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""CrysFML calculation backend for powder diffraction patterns."""

from __future__ import annotations

import string
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.analysis.calculators import absorption as absorption_correction
from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.collection import Experiments
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.structure.collection import Structures
    from easydiffraction.datablocks.structure.item.base import Structure

try:
    from crysfml import cfml_py_utilities

    # TODO: Add the following print to debug mode
    # print("✅ 'crysfml' calculation engine is successfully
    # imported.")
except ImportError:
    # TODO: Add the following print to debug mode
    # print("⚠️ 'pycrysfml' module not found. This calculation engine
    # will not be available.")
    cfml_py_utilities = None


_INSTRUMENT_ATTRIBUTE_MAP: tuple[tuple[str, str], ...] = (
    ('setup_wavelength', '_diffrn_radiation_wavelength'),
    ('calib_twotheta_offset', '_pd_meas_2theta_offset'),
    # crysfml has no SyCos/SySin equivalent, so the CWL
    # calib_sample_displacement and calib_sample_transparency
    # corrections are intentionally left unmapped here.
    ('calib_d_to_tof_offset', '_pd_meas_tof_offset'),
    ('calib_d_to_tof_linear', '_pd_meas_tof_dtt1'),
    ('calib_d_to_tof_quadratic', '_pd_meas_tof_dtt2'),
    ('setup_twotheta_bank', '_pd_meas_tof_bank_angle'),
)

_PEAK_ATTRIBUTE_MAP: tuple[tuple[str, str], ...] = (
    ('broad_gauss_u', '_pd_instr_resolution_u'),
    ('broad_gauss_v', '_pd_instr_resolution_v'),
    ('broad_gauss_w', '_pd_instr_resolution_w'),
    ('broad_lorentz_x', '_pd_instr_resolution_x'),
    ('broad_lorentz_y', '_pd_instr_resolution_y'),
    ('asym_fcj_1', '_pd_instr_reflex_s_l'),
    ('asym_fcj_2', '_pd_instr_reflex_d_l'),
    ('asym_empir_1', '_pd_instr_reflex_asymmetry_p1'),
    ('asym_empir_2', '_pd_instr_reflex_asymmetry_p2'),
    ('asym_empir_3', '_pd_instr_reflex_asymmetry_p3'),
    ('asym_empir_4', '_pd_instr_reflex_asymmetry_p4'),
    ('broad_gauss_sigma_0', '_pd_jorg_vondreele_sigma0'),
    ('broad_gauss_sigma_1', '_pd_jorg_vondreele_sigma1'),
    ('broad_gauss_sigma_2', '_pd_jorg_vondreele_sigma2'),
    ('broad_lorentz_gamma_0', '_pd_jorg_vondreele_gamma0'),
    ('broad_lorentz_gamma_1', '_pd_jorg_vondreele_gamma1'),
    ('broad_lorentz_gamma_2', '_pd_jorg_vondreele_gamma2'),
    ('decay_beta_0', '_pd_jorg_vondreele_beta0'),
    ('decay_beta_1', '_pd_jorg_vondreele_beta1'),
    ('rise_alpha_0', '_pd_jorg_vondreele_alpha0'),
    ('rise_alpha_1', '_pd_jorg_vondreele_alpha1'),
)


def _element_symbol(type_symbol: str) -> str:
    """
    Strip a leading isotope number from an atom type symbol.

    CrysFML resolves scattering by element and does not understand
    isotope prefixes such as ``11B`` or ``2H`` (cryspy does). Returning
    the bare element symbol lets one model drive both engines.

    Parameters
    ----------
    type_symbol : str
        Atom type symbol, optionally isotope-prefixed (e.g. ``11B``).

    Returns
    -------
    str
        The symbol with any leading digits removed (e.g. ``B``).
    """
    return type_symbol.lstrip(string.digits)


@CalculatorFactory.register
class CrysfmlCalculator(CalculatorBase):
    """Wrapper for Crysfml library."""

    type_info = TypeInfo(
        tag='crysfml',
        description='CrysFML library for crystallographic calculations',
    )
    engine_imported: bool = cfml_py_utilities is not None
    url: str = 'https://code.ill.fr/scientific-software/crysfml'

    @property
    def name(self) -> str:
        """Short identifier of this calculator engine."""
        return 'crysfml'

    def calculate_structure_factors(
        self,
        structures: Structures,
        experiments: Experiments,
    ) -> None:
        """
        Call Crysfml to calculate structure factors.

        Parameters
        ----------
        structures : Structures
            The structures to calculate structure factors for.
        experiments : Experiments
            The experiments associated with the sample models.

        Raises
        ------
        NotImplementedError
            HKL calculation is not implemented for CrysfmlCalculator.
        """
        msg = 'HKL calculation is not implemented for CrysfmlCalculator.'
        raise NotImplementedError(msg)

    def calculate_pattern(
        self,
        structure: Structures,
        experiment: ExperimentBase,
        *,
        called_by_minimizer: bool = False,
    ) -> np.ndarray | list[float]:
        """
        Calculate the diffraction pattern using Crysfml.

        Parameters
        ----------
        structure : Structures
            The structure to calculate the pattern for.
        experiment : ExperimentBase
            The experiment associated with the structure.
        called_by_minimizer : bool, default=False
            Whether the calculation is called by a minimizer.

        Returns
        -------
        np.ndarray | list[float]
            The calculated diffraction pattern as a NumPy array or a
            list of floats.
        """
        # Intentionally unused, required by public API/signature
        del called_by_minimizer

        crysfml_dict = self._crysfml_dict(structure, experiment)
        try:
            y = self._calculate_adjusted_pattern(crysfml_dict, experiment)
        except KeyError:
            log.warning('[CrysfmlCalculator] No calculated data')
            y = []
        return np.asarray(absorption_correction.apply(y, experiment))

    def _calculate_adjusted_pattern(
        self,
        crysfml_dict: dict[str, object],
        experiment: ExperimentBase,
    ) -> list[float]:
        """Calculate a Crysfml pattern and match experiment length."""
        y = self._calculate_raw_pattern(crysfml_dict, experiment)
        if y is None:
            return []
        return self._adjust_pattern_length(y, len(experiment.data.x))

    @staticmethod
    def _calculate_raw_pattern(
        crysfml_dict: dict[str, object],
        experiment: ExperimentBase,
    ) -> list[float] | None:
        """Calculate a Crysfml pattern without length adjustment."""
        if experiment.experiment_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
            _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
            return y
        if experiment.experiment_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
            _, y = cfml_py_utilities.tof_powder_pattern_from_dict(crysfml_dict)
            return y
        log.warning(
            f'[CrysfmlCalculator] Unsupported beam mode '
            f'{experiment.experiment_type.beam_mode.value}'
        )
        return None

    def _adjust_pattern_length(  # noqa: PLR6301
        self,
        pattern: list[float],
        target_length: int,
    ) -> list[float]:
        """
        Adjust the pattern length to match the target length.

        Parameters
        ----------
        pattern : list[float]
            The pattern to adjust.
        target_length : int
            The desired length of the pattern.

        Returns
        -------
        list[float]
            The adjusted pattern.
        """
        # TODO: Check the origin of this discrepancy coming from
        #  CrysFML
        # Safety guard: with the correct step formula (max-min)/(N-1+ε),
        # crysfml should return exactly target_length points. Truncate
        # if over-length; pad with the last value if under-length.
        if len(pattern) > target_length:
            return pattern[:target_length]
        if len(pattern) < target_length:
            pad = target_length - len(pattern)
            return list(pattern) + [pattern[-1]] * pad
        return pattern

    def _crysfml_dict(
        self,
        structure: Structures,
        experiment: ExperimentBase,
    ) -> dict[str, ExperimentBase | Structure]:
        """
        Convert structure and experiment into a Crysfml dictionary.

        Parameters
        ----------
        structure : Structures
            The structure to convert.
        experiment : ExperimentBase
            The experiment to convert.

        Returns
        -------
        dict[str, ExperimentBase | Structure]
            A dictionary representation of the structure and experiment.
        """
        structure_dict = self._convert_structure_to_dict(structure)
        experiment_dict = self._convert_experiment_to_dict(experiment)

        return {
            'phases': [structure_dict],
            'experiments': [experiment_dict],
        }

    def _convert_structure_to_dict(  # noqa: PLR6301
        self,
        structure: Structure,
    ) -> dict[str, Any]:
        """
        Convert a structure into a dictionary format.

        Parameters
        ----------
        structure : Structure
            The structure to convert.

        Returns
        -------
        dict[str, Any]
            A dictionary representation of the structure.
        """
        structure_dict = {
            structure.name: {
                '_space_group_name_H-M_alt': structure.space_group.name_h_m.value,
                '_cell_length_a': structure.cell.length_a.value,
                '_cell_length_b': structure.cell.length_b.value,
                '_cell_length_c': structure.cell.length_c.value,
                '_cell_angle_alpha': structure.cell.angle_alpha.value,
                '_cell_angle_beta': structure.cell.angle_beta.value,
                '_cell_angle_gamma': structure.cell.angle_gamma.value,
                '_atom_site': [],
            }
        }

        for atom in structure.atom_sites:
            atom_site = {
                '_label': atom.id.value,
                '_type_symbol': _element_symbol(atom.type_symbol.value),
                '_fract_x': atom.fract_x.value,
                '_fract_y': atom.fract_y.value,
                '_fract_z': atom.fract_z.value,
                '_occupancy': atom.occupancy.value,
                '_adp_type': str(atom.adp_type.value),
                '_B_iso_or_equiv': atom.adp_iso_as_b,
            }
            structure_dict[structure.name]['_atom_site'].append(atom_site)

        return structure_dict

    def _convert_experiment_to_dict(
        self,
        experiment: ExperimentBase,
    ) -> dict[str, Any]:
        """
        Convert an experiment into a dictionary format.

        Parameters
        ----------
        experiment : ExperimentBase
            The experiment to convert.

        Returns
        -------
        dict[str, Any]
            A dictionary representation of the experiment.
        """
        experiment_dict = {
            '_diffrn_radiation_probe': experiment.experiment_type.radiation_probe.value,
        }
        self._update_experiment_dict_from_instrument(experiment_dict, experiment)
        self._update_experiment_dict_from_peak(experiment_dict, experiment)
        self._update_experiment_dict_from_data(experiment_dict, experiment)

        return {'NPD': experiment_dict}

    def _update_experiment_dict_from_instrument(
        self,
        experiment_dict: dict[str, Any],
        experiment: ExperimentBase,
    ) -> None:
        """
        Add instrument settings to the Crysfml experiment dictionary.
        """
        if not hasattr(experiment, 'instrument'):
            return

        self._copy_present_values(
            experiment.instrument,
            experiment_dict,
            _INSTRUMENT_ATTRIBUTE_MAP,
        )
        # if hasattr(experiment.instrument,
        #            'calib_d_to_tof_reciprocal'):
        #    ??? = experiment.instrument.calib_d_to_tof_reciprocal.value

    def _update_experiment_dict_from_peak(
        self,
        experiment_dict: dict[str, Any],
        experiment: ExperimentBase,
    ) -> None:
        """
        Add peak profile settings to the Crysfml experiment dictionary.
        """
        if not hasattr(experiment, 'peak'):
            return

        self._copy_present_values(experiment.peak, experiment_dict, _PEAK_ATTRIBUTE_MAP)

    @staticmethod
    def _update_experiment_dict_from_data(
        experiment_dict: dict[str, Any],
        experiment: ExperimentBase,
    ) -> None:
        """
        Add scan data to the Crysfml experiment dictionary.
        """
        if not hasattr(experiment, 'data'):
            return

        data = experiment.data
        x_data = data.x

        # Do not pass x_min, x_max, and x_inc; instead, always pass
        # the full x_data to support non-uniform x spacing.
        # x_min = float(x_data.min())
        # x_max = float(x_data.max())
        # x_inc = (x_max - x_min) / (len(x_data) - 1 + 1e-9)

        if hasattr(data, 'two_theta'):
            # experiment_dict['_pd_meas_2theta_range_min'] = x_min
            # experiment_dict['_pd_meas_2theta_range_max'] = x_max
            # experiment_dict['_pd_meas_2theta_range_inc'] = x_inc
            experiment_dict['_pd_meas_2theta_scan'] = x_data.tolist()

        if hasattr(data, 'time_of_flight'):
            # experiment_dict['_pd_meas_tof_range_min'] = x_min
            # experiment_dict['_pd_meas_tof_range_max'] = x_max
            # experiment_dict['_pd_meas_tof_range_inc'] = x_inc
            experiment_dict['_pd_meas_time_of_flight'] = x_data.tolist()

    @staticmethod
    def _copy_present_values(
        source: object,
        target: dict[str, Any],
        attribute_map: tuple[tuple[str, str], ...],
    ) -> None:
        """Copy mapped values into a dictionary."""
        for attribute_name, crysfml_key in attribute_map:
            if hasattr(source, attribute_name):
                target[crysfml_key] = getattr(source, attribute_name).value
