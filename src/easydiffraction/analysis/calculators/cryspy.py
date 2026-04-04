# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import contextlib
import copy
import io
from typing import Any

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.structure.item.base import Structure

try:
    import cryspy
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln
    from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary

    # TODO: Add the following print to debug mode
    # print("✅ 'cryspy' calculation engine is successfully imported.")
except ImportError:
    # TODO: Add the following print to debug mode
    # print("⚠️ 'cryspy' module not found. This calculation engine will
    # not be available.")
    cryspy = None


@CalculatorFactory.register
class CryspyCalculator(CalculatorBase):
    """
    Cryspy-based diffraction calculator.

    Converts EasyDiffraction models into Cryspy objects and computes
    patterns.
    """

    type_info = TypeInfo(
        tag='cryspy',
        description='CrysPy library for crystallographic calculations',
    )
    engine_imported: bool = cryspy is not None

    @property
    def name(self) -> str:
        """Short identifier of this calculator engine."""
        return 'cryspy'

    def __init__(self) -> None:
        super().__init__()
        self._cryspy_dicts: dict[str, dict[str, Any]] = {}

    def calculate_structure_factors(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        called_by_minimizer: bool = False,
    ) -> None:
        """
        Raise NotImplementedError as HKL calculation is not implemented.

        Parameters
        ----------
        structure : Structure
            The structure to calculate structure factors for.
        experiment : ExperimentBase
            The experiment associated with the sample models.
        called_by_minimizer : bool, default=False
            Whether the calculation is called by a minimizer.
        """
        combined_name = f'{structure.name}_{experiment.name}'

        if called_by_minimizer:
            if self._cryspy_dicts and combined_name in self._cryspy_dicts:
                cryspy_dict = self._recreate_cryspy_dict(structure, experiment)
            else:
                cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
                cryspy_dict = cryspy_obj.get_dictionary()
        else:
            cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
            cryspy_dict = cryspy_obj.get_dictionary()

        self._cryspy_dicts[combined_name] = copy.deepcopy(cryspy_dict)

        cryspy_in_out_dict: dict[str, Any] = {}

        # Calculate the pattern using Cryspy
        # TODO: Redirect stderr to suppress Cryspy warnings.
        #  This is a temporary solution to avoid cluttering the output.
        #  E.g. cryspy/A_functions_base/powder_diffraction_tof.py:106:
        #  RuntimeWarning: overflow encountered in exp
        #  Remove this when Cryspy is updated to handle warnings better.
        with contextlib.redirect_stderr(io.StringIO()):
            rhochi_calc_chi_sq_by_dictionary(
                cryspy_dict,
                dict_in_out=cryspy_in_out_dict,
                flag_use_precalculated_data=False,
                flag_calc_analytical_derivatives=False,
            )

        cryspy_block_name = f'diffrn_{experiment.name}'

        try:
            y_calc = cryspy_in_out_dict[cryspy_block_name]['intensity_calc']
            stol = cryspy_in_out_dict[cryspy_block_name]['sthovl']
        except KeyError:
            print(f'[CryspyCalculator] Error: No calculated data for {cryspy_block_name}')
            return [], []

        return stol, y_calc

    def calculate_pattern(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        called_by_minimizer: bool = False,
    ) -> np.ndarray | list[float]:
        """
        Calculate the diffraction pattern using Cryspy.

        We only recreate the cryspy_obj if this method is - NOT called
        by the minimizer, or - the cryspy_dict is NOT yet created. In
        other cases, we are modifying the existing cryspy_dict This
        allows significantly speeding up the calculation

        Parameters
        ----------
        structure : Structure
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
        combined_name = f'{structure.name}_{experiment.name}'

        if called_by_minimizer:
            if self._cryspy_dicts and combined_name in self._cryspy_dicts:
                cryspy_dict = self._recreate_cryspy_dict(structure, experiment)
            else:
                cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
                cryspy_dict = cryspy_obj.get_dictionary()
        else:
            cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
            cryspy_dict = cryspy_obj.get_dictionary()

        self._cryspy_dicts[combined_name] = copy.deepcopy(cryspy_dict)

        cryspy_in_out_dict: dict[str, Any] = {}

        # Calculate the pattern using Cryspy
        # TODO: Redirect stderr to suppress Cryspy warnings.
        #  This is a temporary solution to avoid cluttering the output.
        #  E.g. cryspy/A_functions_base/powder_diffraction_tof.py:106:
        #  RuntimeWarning: overflow encountered in exp
        #  Remove this when Cryspy is updated to handle warnings better.
        with contextlib.redirect_stderr(io.StringIO()):
            rhochi_calc_chi_sq_by_dictionary(
                cryspy_dict,
                dict_in_out=cryspy_in_out_dict,
                flag_use_precalculated_data=False,
                flag_calc_analytical_derivatives=False,
            )

        prefixes = {
            BeamModeEnum.CONSTANT_WAVELENGTH: 'pd',
            BeamModeEnum.TIME_OF_FLIGHT: 'tof',
        }
        beam_mode = experiment.type.beam_mode.value
        if beam_mode in prefixes:
            cryspy_block_name = f'{prefixes[beam_mode]}_{experiment.name}'
        else:
            print(f'[CryspyCalculator] Error: Unknown beam mode {experiment.type.beam_mode.value}')
            return []

        try:
            signal_plus = cryspy_in_out_dict[cryspy_block_name]['signal_plus']
            signal_minus = cryspy_in_out_dict[cryspy_block_name]['signal_minus']
            y_calc = signal_plus + signal_minus
        except KeyError:
            print(f'[CryspyCalculator] Error: No calculated data for {cryspy_block_name}')
            return []

        return y_calc

    def _recreate_cryspy_dict(
        self,
        structure: Structure,
        experiment: ExperimentBase,
    ) -> dict[str, Any]:
        """
        Recreate the Cryspy dictionary for structure and experiment.

        Parameters
        ----------
        structure : Structure
            The structure to update.
        experiment : ExperimentBase
            The experiment to update.

        Returns
        -------
        dict[str, Any]
            The updated Cryspy dictionary.
        """
        combined_name = f'{structure.name}_{experiment.name}'
        cryspy_dict = copy.deepcopy(self._cryspy_dicts[combined_name])

        cryspy_model_id = f'crystal_{structure.name}'
        self._update_structure_in_cryspy_dict(cryspy_dict[cryspy_model_id], structure)
        self._update_experiment_in_cryspy_dict(cryspy_dict, experiment)

        return cryspy_dict

    @staticmethod
    def _update_structure_in_cryspy_dict(
        cryspy_model_dict: dict[str, Any],
        structure: Structure,
    ) -> None:
        """
        Update structure parameters in the Cryspy model dictionary.

        Parameters
        ----------
        cryspy_model_dict : dict[str, Any]
            The ``crystal_<name>`` sub-dict.
        structure : Structure
            The source structure.
        """
        # Cell
        cryspy_cell = cryspy_model_dict['unit_cell_parameters']
        cryspy_cell[0] = structure.cell.length_a.value
        cryspy_cell[1] = structure.cell.length_b.value
        cryspy_cell[2] = structure.cell.length_c.value
        cryspy_cell[3] = np.deg2rad(structure.cell.angle_alpha.value)
        cryspy_cell[4] = np.deg2rad(structure.cell.angle_beta.value)
        cryspy_cell[5] = np.deg2rad(structure.cell.angle_gamma.value)

        # Atomic coordinates
        cryspy_xyz = cryspy_model_dict['atom_fract_xyz']
        for idx, atom_site in enumerate(structure.atom_sites):
            cryspy_xyz[0][idx] = atom_site.fract_x.value
            cryspy_xyz[1][idx] = atom_site.fract_y.value
            cryspy_xyz[2][idx] = atom_site.fract_z.value

        # Atomic occupancies
        cryspy_occ = cryspy_model_dict['atom_occupancy']
        for idx, atom_site in enumerate(structure.atom_sites):
            cryspy_occ[idx] = atom_site.occupancy.value

        # Atomic ADPs - Biso only for now
        cryspy_biso = cryspy_model_dict['atom_b_iso']
        for idx, atom_site in enumerate(structure.atom_sites):
            cryspy_biso[idx] = atom_site.b_iso.value

    @staticmethod
    def _update_experiment_in_cryspy_dict(
        cryspy_dict: dict[str, Any],
        experiment: ExperimentBase,
    ) -> None:
        """
        Update experiment parameters in the Cryspy dictionary.

        Parameters
        ----------
        cryspy_dict : dict[str, Any]
            The full Cryspy dictionary.
        experiment : ExperimentBase
            The source experiment.
        """
        if experiment.type.sample_form.value == SampleFormEnum.POWDER:
            if experiment.type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
                cryspy_expt_name = f'pd_{experiment.name}'
                cryspy_expt_dict = cryspy_dict[cryspy_expt_name]

                # Instrument
                cryspy_expt_dict['offset_ttheta'][0] = np.deg2rad(
                    experiment.instrument.calib_twotheta_offset.value
                )
                cryspy_expt_dict['wavelength'][0] = experiment.instrument.setup_wavelength.value

                # Peak
                cryspy_resolution = cryspy_expt_dict['resolution_parameters']
                cryspy_resolution[0] = experiment.peak.broad_gauss_u.value
                cryspy_resolution[1] = experiment.peak.broad_gauss_v.value
                cryspy_resolution[2] = experiment.peak.broad_gauss_w.value
                cryspy_resolution[3] = experiment.peak.broad_lorentz_x.value
                cryspy_resolution[4] = experiment.peak.broad_lorentz_y.value

            elif experiment.type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
                cryspy_expt_name = f'tof_{experiment.name}'
                cryspy_expt_dict = cryspy_dict[cryspy_expt_name]

                # Instrument
                cryspy_expt_dict['zero'][0] = experiment.instrument.calib_d_to_tof_offset.value
                cryspy_expt_dict['dtt1'][0] = experiment.instrument.calib_d_to_tof_linear.value
                cryspy_expt_dict['dtt2'][0] = experiment.instrument.calib_d_to_tof_quad.value
                cryspy_expt_dict['ttheta_bank'] = np.deg2rad(
                    experiment.instrument.setup_twotheta_bank.value
                )

                # Peak
                cryspy_sigma = cryspy_expt_dict['profile_sigmas']
                cryspy_sigma[0] = experiment.peak.broad_gauss_sigma_0.value
                cryspy_sigma[1] = experiment.peak.broad_gauss_sigma_1.value
                cryspy_sigma[2] = experiment.peak.broad_gauss_sigma_2.value

                cryspy_beta = cryspy_expt_dict['profile_betas']
                cryspy_beta[0] = experiment.peak.broad_mix_beta_0.value
                cryspy_beta[1] = experiment.peak.broad_mix_beta_1.value

                cryspy_alpha = cryspy_expt_dict['profile_alphas']
                cryspy_alpha[0] = experiment.peak.asym_alpha_0.value
                cryspy_alpha[1] = experiment.peak.asym_alpha_1.value

        if experiment.type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL:
            cryspy_expt_name = f'diffrn_{experiment.name}'
            cryspy_expt_dict = cryspy_dict[cryspy_expt_name]

            # Instrument
            if experiment.type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
                cryspy_expt_dict['wavelength'][0] = experiment.instrument.setup_wavelength.value

            # Extinction
            cryspy_expt_dict['extinction_radius'][0] = experiment.extinction.radius.value
            cryspy_expt_dict['extinction_mosaicity'][0] = experiment.extinction.mosaicity.value

    def _recreate_cryspy_obj(
        self,
        structure: Structure,
        experiment: ExperimentBase,
    ) -> object:
        """
        Recreate the Cryspy object for structure and experiment.

        Parameters
        ----------
        structure : Structure
            The structure to recreate.
        experiment : ExperimentBase
            The experiment to recreate.

        Returns
        -------
        object
            The recreated Cryspy object.
        """
        cryspy_obj = str_to_globaln('')

        cryspy_structure_cif = self._convert_structure_to_cryspy_cif(structure)
        cryspy_structure_obj = str_to_globaln(cryspy_structure_cif)
        cryspy_obj.add_items(cryspy_structure_obj.items)

        # Add single experiment to cryspy_obj
        cryspy_experiment_cif = self._convert_experiment_to_cryspy_cif(
            experiment,
            linked_structure=structure,
        )

        cryspy_experiment_obj = str_to_globaln(cryspy_experiment_cif)
        cryspy_obj.add_items(cryspy_experiment_obj.items)

        return cryspy_obj

    def _convert_structure_to_cryspy_cif(  # noqa: PLR6301
        self,
        structure: Structure,
    ) -> str:
        """
        Convert a structure to a Cryspy CIF string.

        Parameters
        ----------
        structure : Structure
            The structure to convert.

        Returns
        -------
        str
            The Cryspy CIF string representation of the structure.
        """
        return structure.as_cif

    def _convert_experiment_to_cryspy_cif(  # noqa: PLR6301
        self,
        experiment: ExperimentBase,
        linked_structure: object,
    ) -> str:
        """
        Convert an experiment to a Cryspy CIF string.

        Parameters
        ----------
        experiment : ExperimentBase
            The experiment to convert.
        linked_structure : object
            The structure linked to the experiment.

        Returns
        -------
        str
            The Cryspy CIF string representation of the experiment.
        """
        expt_type = getattr(experiment, 'type', None)
        instrument = getattr(experiment, 'instrument', None)
        peak = getattr(experiment, 'peak', None)
        extinction = getattr(experiment, 'extinction', None)

        cif_lines = [f'data_{experiment.name}']

        # Experiment metadata sections
        _cif_radiation_probe(cif_lines, expt_type)
        _cif_instrument_section(cif_lines, expt_type, instrument)
        _cif_peak_section(cif_lines, expt_type, peak)
        _cif_extinction_section(cif_lines, expt_type, extinction)

        # Powder range data (also returns min/max for background)
        twotheta_min, twotheta_max = _cif_range_section(cif_lines, expt_type, experiment)

        # Structure sections
        _cif_orient_matrix_section(cif_lines, expt_type)
        _cif_phase_section(cif_lines, expt_type, linked_structure)
        _cif_background_section(cif_lines, expt_type, twotheta_min, twotheta_max)

        # Measured data
        _cif_measured_data_section(cif_lines, expt_type, experiment)

        return '\n'.join(cif_lines)


def _cif_radiation_probe(
    cif_lines: list[str],
    expt_type: object | None,
) -> None:
    """Append radiation probe line to CIF."""
    if expt_type is None:
        return
    cif_lines.append('')
    radiation_probe = expt_type.radiation_probe.value
    radiation_probe = radiation_probe.replace('neutron', 'neutrons')
    radiation_probe = radiation_probe.replace('xray', 'X-rays')
    cif_lines.append(f'_setup_radiation {radiation_probe}')


def _cif_instrument_section(
    cif_lines: list[str],
    expt_type: object | None,
    instrument: object | None,
) -> None:
    """Append instrument attribute lines to CIF."""
    if not instrument:
        return

    instrument_mapping: dict[str, str] = {}
    if expt_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
        if expt_type.sample_form.value == SampleFormEnum.POWDER:
            instrument_mapping = {
                'setup_wavelength': '_setup_wavelength',
                'calib_twotheta_offset': '_setup_offset_2theta',
            }
        elif expt_type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL:
            instrument_mapping = {'setup_wavelength': '_setup_wavelength'}
            cif_lines.extend(('', '_setup_field 0.0'))
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        if expt_type.sample_form.value == SampleFormEnum.POWDER:
            instrument_mapping = {
                'setup_twotheta_bank': '_tof_parameters_2theta_bank',
                'calib_d_to_tof_offset': '_tof_parameters_Zero',
                'calib_d_to_tof_linear': '_tof_parameters_Dtt1',
                'calib_d_to_tof_quad': '_tof_parameters_dtt2',
            }
        elif expt_type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL:
            instrument_mapping = {}  # TODO: Check this mapping!
            cif_lines.extend(('', '_setup_field 0.0'))

    cif_lines.append('')
    for local_attr_name, engine_key_name in instrument_mapping.items():
        attr_obj = getattr(instrument, local_attr_name)
        if attr_obj is not None:
            cif_lines.append(f'{engine_key_name} {attr_obj.value}')


def _cif_peak_section(
    cif_lines: list[str],
    expt_type: object | None,
    peak: object | None,
) -> None:
    """Append peak profile lines to CIF."""
    if not peak:
        return

    peak_mapping: dict[str, str] = {}
    if expt_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
        peak_mapping = {
            'broad_gauss_u': '_pd_instr_resolution_U',
            'broad_gauss_v': '_pd_instr_resolution_V',
            'broad_gauss_w': '_pd_instr_resolution_W',
            'broad_lorentz_x': '_pd_instr_resolution_X',
            'broad_lorentz_y': '_pd_instr_resolution_Y',
        }
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        peak_mapping = {
            'broad_gauss_sigma_0': '_tof_profile_sigma0',
            'broad_gauss_sigma_1': '_tof_profile_sigma1',
            'broad_gauss_sigma_2': '_tof_profile_sigma2',
            'broad_mix_beta_0': '_tof_profile_beta0',
            'broad_mix_beta_1': '_tof_profile_beta1',
            'asym_alpha_0': '_tof_profile_alpha0',
            'asym_alpha_1': '_tof_profile_alpha1',
        }
        cif_lines.append('_tof_profile_peak_shape Gauss')

    cif_lines.append('')
    for local_attr_name, engine_key_name in peak_mapping.items():
        attr_obj = getattr(peak, local_attr_name)
        if attr_obj is not None:
            cif_lines.append(f'{engine_key_name} {attr_obj.value}')


def _cif_extinction_section(
    cif_lines: list[str],
    expt_type: object | None,
    extinction: object | None,
) -> None:
    """Append extinction lines to CIF (single crystal only)."""
    if not extinction or expt_type.sample_form.value != SampleFormEnum.SINGLE_CRYSTAL:
        return
    extinction_mapping = {
        'mosaicity': '_extinction_mosaicity',
        'radius': '_extinction_radius',
    }
    cif_lines.extend(('', '_extinction_model gauss'))
    for local_attr_name, engine_key_name in extinction_mapping.items():
        attr_obj = getattr(extinction, local_attr_name)
        if attr_obj is not None:
            cif_lines.append(f'{engine_key_name} {attr_obj.value}')


def _cif_range_section(
    cif_lines: list[str],
    expt_type: object | None,
    experiment: ExperimentBase,
) -> tuple[str, str]:
    """
    Append range lines to CIF and return (min, max) strings.

    Parameters
    ----------
    cif_lines : list[str]
        Accumulator list of CIF lines (mutated in place).
    expt_type : object | None
        Experiment type metadata with ``sample_form`` and ``beam_mode``.
    experiment : ExperimentBase
        Experiment whose data range is queried.

    Returns
    -------
    tuple[str, str]
        Formatted min and max strings (empty if not powder).
    """
    if expt_type.sample_form.value != SampleFormEnum.POWDER:
        return '', ''

    x_data = experiment.data.x
    twotheta_min = f'{np.round(x_data.min(), 5):.5f}'
    twotheta_max = f'{np.round(x_data.max(), 5):.5f}'
    cif_lines.append('')
    if expt_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
        cif_lines.extend((
            f'_range_2theta_min {twotheta_min}',
            f'_range_2theta_max {twotheta_max}',
        ))
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        cif_lines.extend((
            f'_range_time_min {twotheta_min}',
            f'_range_time_max {twotheta_max}',
        ))
    return twotheta_min, twotheta_max


def _cif_orient_matrix_section(
    cif_lines: list[str],
    expt_type: object | None,
) -> None:
    """Append hardcoded orientation matrix for single crystal."""
    if expt_type.sample_form.value != SampleFormEnum.SINGLE_CRYSTAL:
        return
    cif_lines.extend(('', '_diffrn_orient_matrix_type CCSL'))
    for tag, val in [
        ('ub_11', '-0.088033'),
        ('ub_12', '-0.088004'),
        ('ub_13', ' 0.069970'),
        ('ub_21', ' 0.034058'),
        ('ub_22', '-0.188170'),
        ('ub_23', '-0.013039'),
        ('ub_31', ' 0.223600'),
        ('ub_32', ' 0.125751'),
        ('ub_33', ' 0.029490'),
    ]:
        cif_lines.append(f'_diffrn_orient_matrix_{tag} {val}')


def _cif_phase_section(
    cif_lines: list[str],
    expt_type: object | None,
    linked_structure: object,
) -> None:
    """Append phase label/scale to CIF."""
    cif_lines.append('')
    if expt_type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL:
        cif_lines.extend((
            f'_phase_label {linked_structure.name}',
            '_phase_scale 1.0',
        ))
    elif expt_type.sample_form.value == SampleFormEnum.POWDER:
        cif_lines.extend((
            'loop_',
            '_phase_label',
            '_phase_scale',
            f'{linked_structure.name} 1.0',
        ))


def _cif_background_section(
    cif_lines: list[str],
    expt_type: object | None,
    twotheta_min: str,
    twotheta_max: str,
) -> None:
    """Append background loop for powder data."""
    if expt_type.sample_form.value != SampleFormEnum.POWDER:
        return
    cif_lines.extend(('', 'loop_'))
    if expt_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
        cif_lines.extend((
            '_pd_background_2theta',
            '_pd_background_intensity',
        ))
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        cif_lines.extend((
            '_tof_backgroundpoint_time',  # TODO: !!!!????
            '_tof_backgroundpoint_intensity',  # TODO: !!!!????
        ))
    cif_lines.extend((
        f'{twotheta_min} 0.0',  # TODO: !!!!????
        f'{twotheta_max} 0.0',  # TODO: !!!!????
    ))


def _cif_measured_data_section(
    cif_lines: list[str],
    expt_type: object | None,
    experiment: ExperimentBase,
) -> None:
    """Append measured data loop to CIF."""
    if expt_type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL:
        _cif_measured_data_sc(cif_lines, expt_type, experiment)
    elif expt_type.sample_form.value == SampleFormEnum.POWDER:
        _cif_measured_data_pd(cif_lines, expt_type, experiment)


def _cif_measured_data_sc(
    cif_lines: list[str],
    expt_type: object | None,
    experiment: ExperimentBase,
) -> None:
    """Append single crystal measured data loop."""
    data = experiment.data
    cif_lines.extend((
        '',
        'loop_',
        '_diffrn_refln_index_h',
        '_diffrn_refln_index_k',
        '_diffrn_refln_index_l',
        '_diffrn_refln_intensity',
        '_diffrn_refln_intensity_sigma',
    ))

    is_tof = expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT
    if is_tof:
        cif_lines.append('_diffrn_refln_wavelength')

    for i in range(len(data.index_h)):
        line = (
            f'{data.index_h[i]:4.0f}{data.index_k[i]:4.0f}{data.index_l[i]:4.0f}'
            f'   {data.intensity_meas[i]:.5f}   {data.intensity_meas_su[i]:.5f}'
        )
        if is_tof:
            line += f'   {data.wavelength[i]:.5f}'
        cif_lines.append(line)


def _cif_measured_data_pd(
    cif_lines: list[str],
    expt_type: object | None,
    experiment: ExperimentBase,
) -> None:
    """Append powder measured data loop."""
    cif_lines.extend(('', 'loop_'))
    if expt_type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH:
        cif_lines.extend((
            '_pd_meas_2theta',
            '_pd_meas_intensity',
            '_pd_meas_intensity_sigma',
        ))
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        cif_lines.extend((
            '_tof_meas_time',
            '_tof_meas_intensity',
            '_tof_meas_intensity_sigma',
        ))

    x_data = experiment.data.x
    y_data = experiment.data.intensity_meas
    sy_data = experiment.data.intensity_meas_su
    for x_val, y_val, sy_val in zip(x_data, y_data, sy_data, strict=True):
        cif_lines.append(f'  {x_val:.5f}   {y_val:.5f}   {sy_val:.5f}')
