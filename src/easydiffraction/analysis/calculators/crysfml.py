# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any
from typing import Dict
from typing import List
from typing import Union

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
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
        structures
            The structures to calculate structure factors for.
        experiments
            The experiments associated with the sample models.
        """
        raise NotImplementedError('HKL calculation is not implemented for CrysfmlCalculator.')

    def calculate_pattern(
        self,
        structure: Structures,
        experiment: ExperimentBase,
        called_by_minimizer: bool = False,
    ) -> Union[np.ndarray, List[float]]:
        """
        Calculates the diffraction pattern using Crysfml for the given structure
        and experiment.

        Parameters
        ----------
        structure
            The structure to calculate the pattern for.
        experiment
            The experiment associated with the structure.
        called_by_minimizer
            Whether the calculation is called by a minimizer.

        Returns
        -------
            The calculated diffraction pattern as a NumPy array or a list of
            floats.
        """
        # Intentionally unused, required by public API/signature
        del called_by_minimizer

        crysfml_dict = self._crysfml_dict(structure, experiment)
        try:
            _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
            y = self._adjust_pattern_length(y, len(experiment.data.x))
        except KeyError:
            print('[CrysfmlCalculator] Error: No calculated data')
            y = []
        return y

    def _adjust_pattern_length(
        self,
        pattern: List[float],
        target_length: int,
    ) -> List[float]:
        """
        Adjusts the length of the pattern to match the target length.

        Parameters
        ----------
        pattern
            The pattern to adjust.
        target_length
            The desired length of the pattern.

        Returns
        -------
            The adjusted pattern.
        """
        # TODO: Check the origin of this discrepancy coming from
        #  PyCrysFML
        if len(pattern) > target_length:
            return pattern[:target_length]
        return pattern

    def _crysfml_dict(
        self,
        structure: Structures,
        experiment: ExperimentBase,
    ) -> Dict[str, Union[ExperimentBase, Structure]]:
        """
        Converts the structure and experiment into a dictionary format for
        Crysfml.

        Parameters
        ----------
        structure
            The structure to convert.
        experiment
            The experiment to convert.

        Returns
        -------
            A dictionary representation of the structure and experiment.
        """
        structure_dict = self._convert_structure_to_dict(structure)
        experiment_dict = self._convert_experiment_to_dict(experiment)
        return {
            'phases': [structure_dict],
            'experiments': [experiment_dict],
        }

    def _convert_structure_to_dict(
        self,
        structure: Structure,
    ) -> Dict[str, Any]:
        """
        Converts a structure into a dictionary format.

        Parameters
        ----------
        structure
            The structure to convert.

        Returns
        -------
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
                '_adp_type': 'Biso',  # Assuming Biso for simplicity
                '_B_iso_or_equiv': atom.b_iso.value,
            }
            structure_dict[structure.name]['_atom_site'].append(atom_site)

        return structure_dict

    def _convert_experiment_to_dict(
        self,
        experiment: ExperimentBase,
    ) -> Dict[str, Any]:
        """
        Converts an experiment into a dictionary format.

        Parameters
        ----------
        experiment
            The experiment to convert.

        Returns
        -------
            A dictionary representation of the experiment.
        """
        expt_type = getattr(experiment, 'type', None)
        instrument = getattr(experiment, 'instrument', None)
        peak = getattr(experiment, 'peak', None)

        x_data = experiment.data.x
        twotheta_min = float(x_data.min())
        twotheta_max = float(x_data.max())

        # TODO: Process default values on the experiment creation
        #  instead of here
        exp_dict = {
            'NPD': {
                '_diffrn_radiation_probe': expt_type.radiation_probe.value
                if expt_type
                else 'neutron',
                '_diffrn_radiation_wavelength': instrument.setup_wavelength.value
                if instrument
                else 1.0,
                '_pd_instr_resolution_u': peak.broad_gauss_u.value if peak else 0.0,
                '_pd_instr_resolution_v': peak.broad_gauss_v.value if peak else 0.0,
                '_pd_instr_resolution_w': peak.broad_gauss_w.value if peak else 0.0,
                '_pd_instr_resolution_x': peak.broad_lorentz_x.value if peak else 0.0,
                '_pd_instr_resolution_y': peak.broad_lorentz_y.value if peak else 0.0,
                '_pd_meas_2theta_offset': instrument.calib_twotheta_offset.value
                if instrument
                else 0.0,
                '_pd_meas_2theta_range_min': twotheta_min,
                '_pd_meas_2theta_range_max': twotheta_max,
                '_pd_meas_2theta_range_inc': (twotheta_max - twotheta_min) / len(x_data),
            }
        }

        return exp_dict
