# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.structure.collection import Structures
from easydiffraction.datablocks.structure.item.base import Structure

try:
    from pycrysfml import cfml_py_utilities

    # TODO: Add the following print to debug mode
    # print("✅ 'pycrysfml' calculation engine is successfully
    # imported.")
except ImportError:
    # TODO: Add the following print to debug mode
    # print("⚠️ 'pycrysfml' module not found. This calculation engine
    # will not be available.")
    cfml_py_utilities = None


@CalculatorFactory.register
class CrysfmlCalculator(CalculatorBase):
    """Wrapper for Crysfml library."""

    type_info = TypeInfo(
        tag='crysfml',
        description='CrysFML library for crystallographic calculations',
    )
    engine_imported: bool = cfml_py_utilities is not None

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
            if experiment.type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
                _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
            elif experiment.type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
                _, y = cfml_py_utilities.tof_powder_pattern_from_dict(crysfml_dict)
            else:
                print(f'[CrysfmlCalculator] Error: '
                      f'Unsupported beam mode {experiment.type.beam_mode.value}')
                return np.array([])
            y = self._adjust_pattern_length(y, len(experiment.data.x))
        except KeyError:
            print('[CrysfmlCalculator] Error: No calculated data')
            y = []
        return np.asarray(y)

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
        #  PyCrysFML
        # Safety guard: with the correct step formula (max-min)/(N-1+ε),
        # pycrysfml should return exactly target_length points. Truncate
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
                '_label': atom.label.value,
                '_type_symbol': atom.type_symbol.value,
                '_fract_x': atom.fract_x.value,
                '_fract_y': atom.fract_y.value,
                '_fract_z': atom.fract_z.value,
                '_occupancy': atom.occupancy.value,
                '_adp_type': str(atom.adp_type.value),
                '_B_iso_or_equiv': atom.adp_iso_as_b,
            }
            structure_dict[structure.name]['_atom_site'].append(atom_site)

        return structure_dict

    def _convert_experiment_to_dict(  # noqa: PLR6301
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
        expt_type = experiment.type

        # Category: expt_type
        experiment_dict = {
            '_diffrn_radiation_probe': expt_type.radiation_probe.value,
        }

        # Category: instrument
        if hasattr(experiment, 'instrument'):
            instrument = experiment.instrument

            # CWL
            if hasattr(experiment.instrument, 'setup_wavelength'):
                experiment_dict['_diffrn_radiation_wavelength'] = instrument.setup_wavelength.value
            if hasattr(experiment.instrument, 'calib_twotheta_offset'):
                experiment_dict['_pd_meas_2theta_offset'] = instrument.calib_twotheta_offset.value

            # TOF
            if hasattr(experiment.instrument, 'calib_d_to_tof_offset'):
                experiment_dict['_pd_meas_tof_offset'] = instrument.calib_d_to_tof_offset.value
            if hasattr(experiment.instrument, 'calib_d_to_tof_linear'):
                experiment_dict['_pd_meas_tof_dtt1'] = instrument.calib_d_to_tof_linear.value
            if hasattr(experiment.instrument, 'calib_d_to_tof_quad'):
                experiment_dict['_pd_meas_tof_dtt2'] = instrument.calib_d_to_tof_quad.value
            # if hasattr(experiment.instrument, 'calib_d_to_tof_recip'):
            #    ??? = instrument.calib_d_to_tof_recip.value

            if hasattr(experiment.instrument, 'setup_twotheta_bank'):
                experiment_dict['_pd_meas_tof_bank_angle'] = instrument.setup_twotheta_bank.value

        # Category: peak
        if hasattr(experiment, 'peak'):
            peak = experiment.peak

            # CWL
            if hasattr(experiment.peak, 'broad_gauss_u'):
                experiment_dict['_pd_instr_resolution_u'] = peak.broad_gauss_u.value
            if hasattr(experiment.peak, 'broad_gauss_v'):
                experiment_dict['_pd_instr_resolution_v'] = peak.broad_gauss_v.value
            if hasattr(experiment.peak, 'broad_gauss_w'):
                experiment_dict['_pd_instr_resolution_w'] = peak.broad_gauss_w.value
            if hasattr(experiment.peak, 'broad_lorentz_x'):
                experiment_dict['_pd_instr_resolution_x'] = peak.broad_lorentz_x.value
            if hasattr(experiment.peak, 'broad_lorentz_y'):
                experiment_dict['_pd_instr_resolution_y'] = peak.broad_lorentz_y.value

            if hasattr(experiment.peak, 'asym_fcj_1'):
                experiment_dict['_pd_instr_reflex_s_l'] = peak.asym_fcj_1.value
            if hasattr(experiment.peak, 'asym_fcj_2'):
                experiment_dict['_pd_instr_reflex_d_l'] = peak.asym_fcj_2.value

            if hasattr(experiment.peak, 'asym_empir_1'):
                experiment_dict['_pd_instr_reflex_asymmetry_p1'] = peak.asym_empir_1.value
            if hasattr(experiment.peak, 'asym_empir_2'):
                experiment_dict['_pd_instr_reflex_asymmetry_p2'] = peak.asym_empir_2.value
            if hasattr(experiment.peak, 'asym_empir_3'):
                experiment_dict['_pd_instr_reflex_asymmetry_p3'] = peak.asym_empir_3.value
            if hasattr(experiment.peak, 'asym_empir_4'):
                experiment_dict['_pd_instr_reflex_asymmetry_p4'] = peak.asym_empir_4.value

            # TOF
            if hasattr(experiment.peak, 'broad_gauss_sigma_0'):
                experiment_dict['_pd_jorg_vondreele_sigma0'] = peak.broad_gauss_sigma_0.value
            if hasattr(experiment.peak, 'broad_gauss_sigma_1'):
                experiment_dict['_pd_jorg_vondreele_sigma1'] = peak.broad_gauss_sigma_1.value
            if hasattr(experiment.peak, 'broad_gauss_sigma_2'):
                experiment_dict['_pd_jorg_vondreele_sigma2'] = peak.broad_gauss_sigma_2.value

            if hasattr(experiment.peak, 'broad_lorentz_gamma_0'):
                experiment_dict['_pd_jorg_vondreele_gamma0'] = peak.broad_lorentz_gamma_0.value
            if hasattr(experiment.peak, 'broad_lorentz_gamma_1'):
                experiment_dict['_pd_jorg_vondreele_gamma1'] = peak.broad_lorentz_gamma_1.value
            if hasattr(experiment.peak, 'broad_lorentz_gamma_2'):
                experiment_dict['_pd_jorg_vondreele_gamma2'] = peak.broad_lorentz_gamma_2.value

            if hasattr(experiment.peak, 'exp_decay_beta_0'):
                experiment_dict['_pd_jorg_vondreele_beta0'] = peak.exp_decay_beta_0.value
            if hasattr(experiment.peak, 'exp_decay_beta_1'):
                experiment_dict['_pd_jorg_vondreele_beta1'] = peak.exp_decay_beta_1.value

            if hasattr(experiment.peak, 'exp_rise_alpha_0'):
                experiment_dict['_pd_jorg_vondreele_alpha0'] = peak.exp_rise_alpha_0.value
            if hasattr(experiment.peak, 'exp_rise_alpha_1'):
                experiment_dict['_pd_jorg_vondreele_alpha1'] = peak.exp_rise_alpha_1.value

        # Category: data
        if hasattr(experiment, 'data'):
            x_data = experiment.data.x

            # CWL
            if hasattr(experiment.data, 'two_theta'):
                # twotheta_min = float(x_data.min())
                # twotheta_max = float(x_data.max())
                # twotheta_inc = ((twotheta_max - twotheta_min) /
                #                 (len(x_data) - 1 + 1e-9))
                # experiment_dict['_pd_meas_2theta_range_min'] = (
                #     twotheta_min)
                # experiment_dict['_pd_meas_2theta_range_max'] = (
                #     twotheta_max)
                # experiment_dict['_pd_meas_2theta_range_inc'] = (
                #     twotheta_inc)

                x_data = x_data.tolist()
                experiment_dict['_pd_meas_2theta_scan'] = x_data

            # TOF
            if hasattr(experiment.data, 'time_of_flight'):
                x_min = float(x_data.min())
                x_max = float(x_data.max())
                x_inc = (x_max - x_min) / (len(x_data) - 1 + 1e-9)
                experiment_dict['_pd_meas_tof_range_min'] = x_min
                experiment_dict['_pd_meas_tof_range_max'] = x_max
                experiment_dict['_pd_meas_tof_range_inc'] = x_inc

                # x_data = x_data.tolist()
                # experiment_dict['_pd_meas_time_of_flight'] = x_data

        return {'NPD': experiment_dict}
