# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""CrysPy calculation backend for diffraction patterns."""

from __future__ import annotations

import contextlib
import copy
import io
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.base import PowderReflnRecord
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import sin_theta_over_lambda_to_d_spacing

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
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


EXPECTED_HKL_INDEX_ROWS = 3


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
    url: str = 'https://www.cryspy.fr'

    @property
    def name(self) -> str:
        """Short identifier of this calculator engine."""
        return 'cryspy'

    def __init__(self) -> None:
        """Initialize the calculator with empty cryspy caches."""
        super().__init__()
        self._cryspy_dicts: dict[str, dict[str, Any]] = {}
        self._cached_peak_types: dict[str, str] = {}
        self._cached_adp_types: dict[str, tuple[str, ...]] = {}
        self._cached_pref_orient: dict[str, tuple] = {}
        self._last_powder_phase_blocks: dict[str, dict[str, Any] | None] = {}

    def _invalidate_stale_cache(
        self,
        combined_name: str,
        experiment: ExperimentBase,
        structure: Structure | None = None,
    ) -> None:
        """
        Drop cached dict when experiment or structure config changed.

        Checks the peak profile type, the per-atom ADP types, and the
        preferred-orientation row identities. When any changes the cached
        dictionary is stale and must be rebuilt from a fresh cryspy
        object.
        """
        if 'peak' in type(experiment)._public_attrs():
            current_type = experiment.peak.type_info.tag
            if self._cached_peak_types.get(combined_name) != current_type:
                self._cryspy_dicts.pop(combined_name, None)
            self._cached_peak_types[combined_name] = current_type

        # Preferred-orientation row set/identity. Adding or removing a
        # row, or changing a row's phase_id or h/k/l, changes the emitted
        # texture loop's shape and must rebuild the dict. The refinable
        # r/fraction values are patched in place, so they are excluded.
        # Constant-wavelength only, matching the texture-loop emission
        # scope; TOF emits no texture and is not tracked here.
        supports_texture = (
            'preferred_orientation' in type(experiment)._public_attrs()
            and experiment.type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH
        )
        if supports_texture:
            current_pref_orient = tuple(
                (
                    item.phase_id.value,
                    item.index_h.value,
                    item.index_k.value,
                    item.index_l.value,
                )
                for item in experiment.preferred_orientation
            )
            if self._cached_pref_orient.get(combined_name) != current_pref_orient:
                self._cryspy_dicts.pop(combined_name, None)
            self._cached_pref_orient[combined_name] = current_pref_orient

        if structure is not None:
            current_adp = tuple(atom.adp_type.value for atom in structure.atom_sites)
            if self._cached_adp_types.get(combined_name) != current_adp:
                self._cryspy_dicts.pop(combined_name, None)
            self._cached_adp_types[combined_name] = current_adp

    def calculate_structure_factors(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
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
        self._invalidate_stale_cache(combined_name, experiment, structure)

        if called_by_minimizer:
            if self._cryspy_dicts and combined_name in self._cryspy_dicts:
                cryspy_dict = self._recreate_cryspy_dict(structure, experiment)
            else:
                cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
                cryspy_dict = cryspy_obj.get_dictionary()
                self._update_structure_in_cryspy_dict(
                    cryspy_dict[f'crystal_{structure.name}'],
                    structure,
                )
                self._update_experiment_in_cryspy_dict(cryspy_dict, experiment)
        else:
            cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
            cryspy_dict = cryspy_obj.get_dictionary()
            self._update_structure_in_cryspy_dict(
                cryspy_dict[f'crystal_{structure.name}'],
                structure,
            )
            self._update_experiment_in_cryspy_dict(cryspy_dict, experiment)

        self._cryspy_dicts[combined_name] = copy.deepcopy(cryspy_dict)

        cryspy_in_out_dict: dict[str, Any] = {}

        # TODO: This is temporary solution to mark all structures as
        #  nuclear-only. Once magnetic structure is implemented, we
        #  would need to auto-detect it.
        cryspy_dict[f'crystal_{structure.name}']['flag_only_nuclear'] = True

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
            log.warning(f'[CryspyCalculator] No calculated data for {cryspy_block_name}')
            return [], []

        return stol, y_calc

    def calculate_pattern(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
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
        self._invalidate_stale_cache(combined_name, experiment, structure)
        self._last_powder_phase_blocks[combined_name] = None

        if called_by_minimizer:
            if self._cryspy_dicts and combined_name in self._cryspy_dicts:
                cryspy_dict = self._recreate_cryspy_dict(structure, experiment)
            else:
                cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
                cryspy_dict = cryspy_obj.get_dictionary()
                self._update_structure_in_cryspy_dict(
                    cryspy_dict[f'crystal_{structure.name}'],
                    structure,
                )
                self._update_experiment_in_cryspy_dict(cryspy_dict, experiment)
        else:
            cryspy_obj = self._recreate_cryspy_obj(structure, experiment)
            cryspy_dict = cryspy_obj.get_dictionary()
            self._update_structure_in_cryspy_dict(
                cryspy_dict[f'crystal_{structure.name}'],
                structure,
            )
            self._update_experiment_in_cryspy_dict(cryspy_dict, experiment)

        self._cryspy_dicts[combined_name] = copy.deepcopy(cryspy_dict)

        cryspy_in_out_dict: dict[str, Any] = {}

        # TODO: This is temporary solution to mark all structures as
        #  nuclear-only. Once magnetic structure is implemented, we
        #  would need to auto-detect it.
        cryspy_dict[f'crystal_{structure.name}']['flag_only_nuclear'] = True

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
            log.warning(f'[CryspyCalculator] Unknown beam mode {experiment.type.beam_mode.value}')
            return []

        try:
            powder_block = cryspy_in_out_dict[cryspy_block_name]
            signal_plus = powder_block['signal_plus']
            signal_minus = powder_block['signal_minus']
            y_calc = signal_plus + signal_minus
            self._last_powder_phase_blocks[combined_name] = powder_block.get(
                f'dict_in_out_{structure.name}'
            )
        except KeyError:
            log.warning(f'[CryspyCalculator] No calculated data for {cryspy_block_name}')
            return []

        return y_calc

    def last_powder_refln_records(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
        phase_id: str,
    ) -> list[PowderReflnRecord] | None:
        """
        Return powder reflection records from the latest pattern run.
        """
        combined_name = f'{structure.name}_{experiment.name}'
        phase_block = self._last_powder_phase_blocks.get(combined_name)
        if phase_block is None:
            return None

        core_arrays = self._powder_refln_core_arrays(phase_block)
        if core_arrays is None:
            return None
        x_values = self._powder_refln_x_values(phase_block, experiment.type.beam_mode.value)
        if x_values is None:
            return None

        indices, sin_theta_over_lambda, f_nucl = core_arrays
        d_spacing = self._powder_refln_d_spacing(phase_block, sin_theta_over_lambda)
        f_calc = np.abs(f_nucl)
        f_squared_calc = f_calc**2

        return [
            self._powder_refln_record(
                phase_id=phase_id,
                beam_mode=experiment.type.beam_mode.value,
                hkl=(index_h, index_k, index_l),
                values=(sthovl, d_value, x_value, f_value, f_sq_value),
            )
            for index_h, index_k, index_l, sthovl, d_value, x_value, f_value, f_sq_value in zip(
                indices[0],
                indices[1],
                indices[2],
                sin_theta_over_lambda,
                d_spacing,
                x_values,
                f_calc,
                f_squared_calc,
                strict=True,
            )
        ]

    @staticmethod
    def _powder_refln_core_arrays(
        phase_block: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        """
        Extract HKL indices, sin(theta)/lambda and structure factors.

        Returns ``None`` when the phase block lacks the required arrays
        or the HKL indices do not have the expected number of rows.
        """
        try:
            indices = np.asarray(phase_block['index_hkl'], dtype=int)
            sin_theta_over_lambda = np.asarray(phase_block['sthovl'], dtype=float)
        except KeyError:
            return None

        structure_factor = phase_block.get('f_nucl')
        if structure_factor is None:
            structure_factor = phase_block.get('f_charge')
        if structure_factor is None:
            return None
        structure_factor = np.asarray(structure_factor)

        if indices.shape[0] != EXPECTED_HKL_INDEX_ROWS:
            return None
        return indices, sin_theta_over_lambda, structure_factor

    @staticmethod
    def _powder_refln_d_spacing(
        phase_block: dict[str, Any],
        sin_theta_over_lambda: np.ndarray,
    ) -> np.ndarray:
        """
        Return d-spacings, deriving them from sin(theta)/lambda.

        Uses the ``d_hkl`` array from the phase block when present and
        otherwise converts the supplied sin(theta)/lambda values.
        """
        d_spacing_raw = phase_block.get('d_hkl')
        if d_spacing_raw is None:
            return np.asarray(
                sin_theta_over_lambda_to_d_spacing(sin_theta_over_lambda),
                dtype=float,
            )
        return np.asarray(d_spacing_raw, dtype=float)

    @staticmethod
    def _powder_refln_x_values(
        phase_block: dict[str, Any],
        beam_mode: BeamModeEnum,
    ) -> np.ndarray | None:
        """
        Return reflection x positions for the given beam mode.

        Reads two-theta (converted to degrees) for constant wavelength
        and time-of-flight values otherwise, returning ``None`` when no
        values are available.
        """
        x_values = None
        if beam_mode == BeamModeEnum.CONSTANT_WAVELENGTH:
            x_raw = phase_block.get('ttheta_hkl')
            if x_raw is not None:
                x_values = np.degrees(np.asarray(x_raw, dtype=float))
        elif beam_mode == BeamModeEnum.TIME_OF_FLIGHT:
            x_raw = phase_block.get('time_hkl')
            if x_raw is not None:
                x_values = np.asarray(x_raw, dtype=float)

        if x_values is None or x_values.size == 0:
            return None
        return x_values

    @staticmethod
    def _powder_refln_record(
        *,
        phase_id: str,
        beam_mode: BeamModeEnum,
        hkl: tuple[int, int, int],
        values: tuple[float, float, float, float, float],
    ) -> PowderReflnRecord:
        """
        Build a single powder reflection record.

        Stores the x position as two-theta for constant wavelength and
        as time-of-flight for the time-of-flight beam mode.
        """
        index_h, index_k, index_l = hkl
        sin_theta_over_lambda, d_spacing, x_value, f_calc, f_squared_calc = values
        x_kwargs = {'two_theta': float(x_value)}
        if beam_mode == BeamModeEnum.TIME_OF_FLIGHT:
            x_kwargs = {'time_of_flight': float(x_value)}

        return PowderReflnRecord(
            phase_id=phase_id,
            d_spacing=float(d_spacing),
            sin_theta_over_lambda=float(sin_theta_over_lambda),
            index_h=int(index_h),
            index_k=int(index_k),
            index_l=int(index_l),
            f_calc=float(f_calc),
            f_squared_calc=float(f_squared_calc),
            **x_kwargs,
        )

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

        # Atomic multiplicities
        if 'atom_multiplicity' in cryspy_model_dict:
            CryspyCalculator._update_atom_multiplicity(
                cryspy_model_dict,
                structure,
            )

        # Atomic ADPs - isotropic
        # For anisotropic atoms the full ADP lives in the β tensor;
        # setting b_iso to zero avoids double-counting in cryspy's DWF
        # which sums both the isotropic and anisotropic contributions.
        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        aniso_types = {
            AdpTypeEnum.BANI.value,
            AdpTypeEnum.UANI.value,
            AdpTypeEnum.BETA.value,
        }
        cryspy_biso = cryspy_model_dict['atom_b_iso']
        for idx, atom_site in enumerate(structure.atom_sites):
            if atom_site.adp_type.value in aniso_types:
                cryspy_biso[idx] = 0.0
            else:
                cryspy_biso[idx] = atom_site.adp_iso_as_b

        # Atomic ADPs - anisotropic (update β tensor when present)
        if 'atom_beta' in cryspy_model_dict:
            CryspyCalculator._update_aniso_beta(
                cryspy_model_dict,
                structure,
            )

    @staticmethod
    def _update_atom_multiplicity(
        cryspy_model_dict: dict[str, Any],
        structure: Structure,
    ) -> None:
        """
        Update cryspy atom multiplicities from the model.

        CrysPy normalizes fractional coordinates into the ``[0, 1)``
        interval while parsing CIF.  For sites such as ``(x, -x, z)``,
        that can turn ``-x`` into ``1 - x`` before the Wyckoff
        multiplicity is inferred, making special positions look like
        general positions.  EasyDiffraction's Wyckoff detection already
        stores the correct per-site multiplicity, so use it; when a site
        has no detected multiplicity (untabulated space group), keep the
        backend's inferred value.
        """
        if cryspy is None:
            return

        multiplicity = cryspy_model_dict['atom_multiplicity']
        for idx, atom_site in enumerate(structure.atom_sites):
            site_multiplicity = atom_site.multiplicity.value
            if site_multiplicity is not None:
                multiplicity[idx] = site_multiplicity

    @staticmethod
    def _update_aniso_beta(
        cryspy_model_dict: dict[str, Any],
        structure: Structure,
    ) -> None:
        """
        Update cryspy ``atom_beta`` from anisotropic ADP values.

        Converts B or U tensor components to cryspy's internal β
        representation using β_ij = 2π²·U_ij·a*_i·a*_j. Atoms already
        stored as the dimensionless β tensor (``adp_type == 'beta'``)
        are passed straight through, since β is cryspy's native
        convention.

        Parameters
        ----------
        cryspy_model_dict : dict[str, Any]
            The ``crystal_<name>`` sub-dict.
        structure : Structure
            The source structure.
        """
        from cryspy.A_functions_base.function_1_atomic_vibrations import (  # noqa: PLC0415
            calc_beta_by_u,
        )
        from cryspy.A_functions_base.unit_cell import (  # noqa: PLC0415
            calc_reciprocal_by_unit_cell_parameters,
        )

        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        aniso_index = cryspy_model_dict.get('atom_site_aniso_index')
        if aniso_index is None:
            return

        cryspy_beta = cryspy_model_dict['atom_beta']
        cell_params = cryspy_model_dict['unit_cell_parameters']

        # Compute reciprocal lengths from cell parameters (with angles
        # already in radians as stored by cryspy).
        recip_params, _ = calc_reciprocal_by_unit_cell_parameters(cell_params)

        class _CellLike:
            """Adapter exposing reciprocal cell lengths to cryspy."""

            reciprocal_length_a = recip_params[0]
            reciprocal_length_b = recip_params[1]
            reciprocal_length_c = recip_params[2]

        cell_like = _CellLike()
        factor = 8.0 * np.pi**2

        for col, atom_idx in enumerate(aniso_index):
            atom = list(structure.atom_sites)[atom_idx]
            adp_enum = AdpTypeEnum(atom.adp_type.value)
            if adp_enum not in {AdpTypeEnum.BANI, AdpTypeEnum.UANI, AdpTypeEnum.BETA}:
                continue

            aniso = structure.atom_site_aniso[atom.label.value]
            components = [
                aniso.adp_11.value,
                aniso.adp_22.value,
                aniso.adp_33.value,
                aniso.adp_12.value,
                aniso.adp_13.value,
                aniso.adp_23.value,
            ]

            if adp_enum is AdpTypeEnum.BETA:
                # Already dimensionless β (cryspy's native convention);
                # pass straight through without a U→β transform.
                betas = components
            else:
                # Convert to U if stored as B, then map U → β.
                u_vals = (
                    [v / factor for v in components]
                    if adp_enum == AdpTypeEnum.BANI
                    else components
                )
                betas = calc_beta_by_u(u_vals, cell_like)

            for k in range(6):
                cryspy_beta[k][col] = betas[k]

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

                # Sample-displacement (SyCos) and transparency
                # (SySin) peak-position corrections (cryspy PR #46).
                # cryspy applies numpy.radians() to these internally,
                # so the dict stores plain degrees here (unlike
                # offset_ttheta, which is pre-converted to radians).
                # The keys are absent on cryspy releases without PR
                # #46, so guard before each set.
                if 'offset_sycos' in cryspy_expt_dict:
                    cryspy_expt_dict['offset_sycos'][0] = (
                        experiment.instrument.calib_sample_displacement.value
                    )
                if 'offset_sysin' in cryspy_expt_dict:
                    cryspy_expt_dict['offset_sysin'][0] = (
                        experiment.instrument.calib_sample_transparency.value
                    )

                # Peak
                cryspy_resolution = cryspy_expt_dict['resolution_parameters']
                cryspy_resolution[0] = experiment.peak.broad_gauss_u.value
                cryspy_resolution[1] = experiment.peak.broad_gauss_v.value
                cryspy_resolution[2] = experiment.peak.broad_gauss_w.value
                cryspy_resolution[3] = experiment.peak.broad_lorentz_x.value
                cryspy_resolution[4] = experiment.peak.broad_lorentz_y.value

                if 'asymmetry_parameters' in cryspy_expt_dict:
                    cryspy_asymmetry = cryspy_expt_dict['asymmetry_parameters']
                    cryspy_asymmetry[0] = experiment.peak.asym_empir_1.value
                    cryspy_asymmetry[1] = experiment.peak.asym_empir_2.value
                    cryspy_asymmetry[2] = experiment.peak.asym_empir_3.value
                    cryspy_asymmetry[3] = experiment.peak.asym_empir_4.value

                # Preferred orientation (March-Dollase): patch the
                # refinable coefficient (g_1) and random fraction (g_2)
                # in place, matched to each emitted texture row by phase
                # label. h/k/l are fixed descriptors, so texture_axis is
                # never patched. The keys are absent unless a texture
                # loop was emitted, so guard.
                _update_texture_in_cryspy_dict(cryspy_expt_dict, experiment)

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

                # Peak - sigma (common to all TOF profiles)
                cryspy_sigma = cryspy_expt_dict['profile_sigmas']
                cryspy_sigma[0] = experiment.peak.broad_gauss_sigma_0.value
                cryspy_sigma[1] = experiment.peak.broad_gauss_sigma_1.value
                cryspy_sigma[2] = experiment.peak.broad_gauss_sigma_2.value

                _update_tof_peak_in_cryspy_dict(cryspy_expt_dict, experiment.peak)

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

    def _convert_structure_to_cryspy_cif(self, structure: Structure) -> str:
        """
        Convert a structure to a Cryspy CIF string.

        CrysPy uses attribute names that match the CIF convention:
        ``u_11`` for ``U_11``, ``b_11`` for ``B_11``, etc.  Its
        ``apply_space_group_constraint`` always accesses ``u_11``
        regardless of ``adp_type``.  To avoid mismatches the CIF sent to
        cryspy always uses **U** notation: ``Biso`` ⟶ ``Uiso``, ``Bani``
        ⟶ ``Uani``, values divided by 8π².

        Parameters
        ----------
        structure : Structure
            The structure to convert.

        Returns
        -------
        str
            The Cryspy CIF string representation of the structure.
        """
        saved = self._temporarily_convert_to_u_notation(structure)

        try:
            cif = structure.as_cif
        finally:
            self._restore_from_u_notation(structure, saved)

        return cif

    @staticmethod
    def _temporarily_convert_to_u_notation(
        structure: Structure,
    ) -> list[tuple]:
        """
        Temporarily convert B-convention and beta atoms to U notation.

        cryspy's CIF parser and ``apply_space_group_constraint`` only
        understand the U (and B) aniso tags, so a ``beta`` atom is sent
        as a Uani atom (β→U via the reciprocal cell). Its β values are
        written back into cryspy's ``atom_beta`` afterwards by
        :meth:`_update_aniso_beta`. Returns saved state for restoration.
        """
        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        factor = 8.0 * np.pi**2
        suffixes = ('11', '22', '33', '12', '13', '23')
        saved: list[tuple] = []
        beta_pairs: tuple[float, ...] | None = None

        for atom in structure.atom_sites:
            adp_enum = AdpTypeEnum(atom.adp_type.value)
            if adp_enum is AdpTypeEnum.BETA:
                if beta_pairs is None:
                    beta_pairs = CryspyCalculator._beta_reciprocal_pairs(structure)
                saved.append(
                    CryspyCalculator._stash_beta_atom_as_u(structure, atom, beta_pairs, suffixes)
                )
                continue
            is_b = adp_enum in {AdpTypeEnum.BISO, AdpTypeEnum.BANI}
            if not is_b:
                continue

            orig_adp_type = atom._adp_type._value
            orig_iso_val = atom._adp_iso._value
            orig_iso_names = list(atom._adp_iso._cif_handler._names)

            atom._adp_iso._value = orig_iso_val / factor
            atom._adp_iso._cif_handler._names = [
                '_atom_site.U_iso_or_equiv',
                '_atom_site.B_iso_or_equiv',
            ]

            if adp_enum == AdpTypeEnum.BISO:
                atom._adp_type._value = AdpTypeEnum.UISO.value
                saved.append((atom, None, None, None, orig_adp_type, orig_iso_names, orig_iso_val))
            else:
                atom._adp_type._value = AdpTypeEnum.UANI.value
                lbl = atom.label.value
                if lbl in structure.atom_site_aniso:
                    aniso = structure.atom_site_aniso[lbl]
                else:
                    aniso = None
                if aniso is not None:
                    orig_vals = []
                    orig_names = []
                    for s in suffixes:
                        param = getattr(aniso, f'_adp_{s}')
                        orig_vals.append(param._value)
                        orig_names.append(list(param._cif_handler._names))
                        param._value /= factor
                        param._cif_handler._names = [
                            f'_atom_site_aniso.U_{s}',
                            f'_atom_site_aniso.B_{s}',
                        ]
                    saved.append((
                        atom,
                        aniso,
                        orig_vals,
                        orig_names,
                        orig_adp_type,
                        orig_iso_names,
                        orig_iso_val,
                    ))
                else:
                    saved.append((
                        atom,
                        None,
                        None,
                        None,
                        orig_adp_type,
                        orig_iso_names,
                        orig_iso_val,
                    ))

        return saved

    @staticmethod
    def _restore_from_u_notation(
        structure: Structure,  # noqa: ARG004
        saved: list[tuple],
    ) -> None:
        """Restore original B-convention state after CIF generation."""
        suffixes = ('11', '22', '33', '12', '13', '23')

        for (
            atom,
            aniso,
            orig_vals,
            orig_names,
            orig_adp_type,
            orig_iso_names,
            orig_iso_val,
        ) in saved:
            atom._adp_type._value = orig_adp_type
            atom._adp_iso._value = orig_iso_val
            atom._adp_iso._cif_handler._names = orig_iso_names
            if aniso is not None and orig_vals is not None:
                for s, val, names in zip(suffixes, orig_vals, orig_names, strict=False):
                    param = getattr(aniso, f'_adp_{s}')
                    param._value = val
                    param._cif_handler._names = names

    @staticmethod
    def _beta_reciprocal_pairs(structure: Structure) -> tuple[float, ...]:
        """
        Return the ``2π²·a*_i·a*_j`` factors for a β→U conversion.

        The six factors follow the ``(11, 22, 33, 12, 13, 23)``
        component order, so ``U_ij = beta_ij / factor_ij``.
        """
        from easydiffraction.crystallography import crystallography as ecr  # noqa: PLC0415

        cell = structure.cell
        a_star, b_star, c_star = ecr.reciprocal_cell_lengths(
            cell.length_a.value,
            cell.length_b.value,
            cell.length_c.value,
            cell.angle_alpha.value,
            cell.angle_beta.value,
            cell.angle_gamma.value,
        )
        two_pi_sq = 2.0 * np.pi**2
        return (
            two_pi_sq * a_star * a_star,
            two_pi_sq * b_star * b_star,
            two_pi_sq * c_star * c_star,
            two_pi_sq * a_star * b_star,
            two_pi_sq * a_star * c_star,
            two_pi_sq * b_star * c_star,
        )

    @staticmethod
    def _stash_beta_atom_as_u(
        structure: Structure,
        atom: object,
        pairs: tuple[float, ...],
        suffixes: tuple[str, ...],
    ) -> tuple:
        """
        Relabel a β atom as Uani for cryspy and save its original state.

        Converts the stored β components to U (``U_ij = beta_ij /
        (2π²·a*_i·a*_j)``) and points the CIF names at the U tags, so
        the atom serialises as a Uani atom. The returned tuple matches
        the layout consumed by :meth:`_restore_from_u_notation`.
        """
        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        orig_adp_type = atom._adp_type._value
        orig_iso_val = atom._adp_iso._value
        orig_iso_names = list(atom._adp_iso._cif_handler._names)

        # adp_iso already holds the equivalent U for a beta atom; only
        # the CIF tag needs relabelling (cryspy zeroes b_iso for aniso
        # atoms).
        atom._adp_iso._cif_handler._names = [
            '_atom_site.U_iso_or_equiv',
            '_atom_site.B_iso_or_equiv',
        ]
        atom._adp_type._value = AdpTypeEnum.UANI.value

        lbl = atom.label.value
        if lbl not in structure.atom_site_aniso:
            return (atom, None, None, None, orig_adp_type, orig_iso_names, orig_iso_val)
        aniso = structure.atom_site_aniso[lbl]

        orig_vals = []
        orig_names = []
        for s, pair in zip(suffixes, pairs, strict=False):
            param = getattr(aniso, f'_adp_{s}')
            orig_vals.append(param._value)
            orig_names.append(list(param._cif_handler._names))
            param._value /= pair
            param._cif_handler._names = [
                f'_atom_site_aniso.U_{s}',
                f'_atom_site_aniso.B_{s}',
            ]
        return (atom, aniso, orig_vals, orig_names, orig_adp_type, orig_iso_names, orig_iso_val)

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
        attrs = type(experiment)._public_attrs()
        expt_type = experiment.type if 'type' in attrs else None
        instrument = experiment.instrument if 'instrument' in attrs else None
        peak = experiment.peak if 'peak' in attrs else None
        extinction = experiment.extinction if 'extinction' in attrs else None

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
        _cif_pref_orient_section(cif_lines, expt_type, experiment, linked_structure)
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
                'calib_sample_displacement': '_setup_offset_SyCos',
                'calib_sample_transparency': '_setup_offset_SySin',
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


def _update_tof_peak_in_cryspy_dict(
    cryspy_expt_dict: dict[str, Any],
    peak: object,
) -> None:
    """Update TOF peak profile-specific arrays in the cached dict."""
    peak_tag = peak.type_info.tag
    # TODO: Need to improve this logic to be more robust and extensible
    #  for future profiles
    if not hasattr(peak, 'exp_decay_beta_0') and not hasattr(peak, 'dexp_decay_beta_00'):
        cryspy_expt_dict['profile_gammas'][0] = peak.broad_lorentz_gamma_0.value
        cryspy_expt_dict['profile_gammas'][1] = peak.broad_lorentz_gamma_1.value
        cryspy_expt_dict['profile_gammas'][2] = peak.broad_lorentz_gamma_2.value
    elif peak_tag == PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE:
        cryspy_expt_dict['profile_alphas'][0] = peak.dexp_rise_alpha_1.value
        cryspy_expt_dict['profile_alphas'][1] = peak.dexp_rise_alpha_2.value

        cryspy_expt_dict['profile_betas'][0] = peak.dexp_decay_beta_00.value
        cryspy_expt_dict['profile_betas'][1] = peak.dexp_decay_beta_01.value
        cryspy_expt_dict['profile_betas'][2] = peak.dexp_decay_beta_10.value

        cryspy_expt_dict['profile_rs'][0] = peak.dexp_switch_r_01.value
        cryspy_expt_dict['profile_rs'][1] = peak.dexp_switch_r_02.value
        cryspy_expt_dict['profile_rs'][2] = peak.dexp_switch_r_03.value

        cryspy_expt_dict['profile_gammas'][0] = peak.broad_lorentz_gamma_0.value
        cryspy_expt_dict['profile_gammas'][1] = peak.broad_lorentz_gamma_1.value
        cryspy_expt_dict['profile_gammas'][2] = peak.broad_lorentz_gamma_2.value
    else:
        cryspy_expt_dict['profile_betas'][0] = peak.exp_decay_beta_0.value
        cryspy_expt_dict['profile_betas'][1] = peak.exp_decay_beta_1.value

        cryspy_expt_dict['profile_alphas'][0] = peak.exp_rise_alpha_0.value
        cryspy_expt_dict['profile_alphas'][1] = peak.exp_rise_alpha_1.value

        if peak_tag == PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE:
            cryspy_expt_dict['profile_gammas'][0] = peak.broad_lorentz_gamma_0.value
            cryspy_expt_dict['profile_gammas'][1] = peak.broad_lorentz_gamma_1.value
            cryspy_expt_dict['profile_gammas'][2] = peak.broad_lorentz_gamma_2.value


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
            'asym_empir_1': '_pd_instr_reflex_asymmetry_p1',
            'asym_empir_2': '_pd_instr_reflex_asymmetry_p2',
            'asym_empir_3': '_pd_instr_reflex_asymmetry_p3',
            'asym_empir_4': '_pd_instr_reflex_asymmetry_p4',
        }
    elif expt_type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT:
        peak_mapping = {
            'broad_gauss_sigma_0': '_tof_profile_sigma0',
            'broad_gauss_sigma_1': '_tof_profile_sigma1',
            'broad_gauss_sigma_2': '_tof_profile_sigma2',
            'broad_lorentz_gamma_0': '_tof_profile_gamma0',
            'broad_lorentz_gamma_1': '_tof_profile_gamma1',
            'broad_lorentz_gamma_2': '_tof_profile_gamma2',
        }

        if peak.type_info.tag == PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE:
            cif_lines.append('_tof_profile_peak_shape type0m')
            peak_mapping.update({
                'dexp_rise_alpha_1': '_tof_profile_alpha1',
                'dexp_rise_alpha_2': '_tof_profile_alpha2',
                'dexp_decay_beta_00': '_tof_profile_beta00',
                'dexp_decay_beta_01': '_tof_profile_beta01',
                'dexp_decay_beta_10': '_tof_profile_beta10',
                'dexp_switch_r_01': '_tof_profile_r01',
                'dexp_switch_r_02': '_tof_profile_r02',
                'dexp_switch_r_03': '_tof_profile_r03',
            })
        elif hasattr(peak, 'exp_decay_beta_0') and hasattr(peak, 'exp_rise_alpha_0'):
            peak_mapping.update({
                'exp_decay_beta_0': '_tof_profile_beta0',
                'exp_decay_beta_1': '_tof_profile_beta1',
                'exp_rise_alpha_0': '_tof_profile_alpha0',
                'exp_rise_alpha_1': '_tof_profile_alpha1',
            })
            if peak.type_info.tag == PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE:
                cif_lines.append('_tof_profile_peak_shape pseudo-Voigt')
            else:
                cif_lines.append('_tof_profile_peak_shape Gauss')
        else:
            cif_lines.append('_tof_profile_peak_shape non-conv-pseudo-Voigt')

    cif_lines.append('')
    for local_attr_name, engine_key_name in peak_mapping.items():
        attr_obj = getattr(peak, local_attr_name, None)
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
    cif_lines.extend(('', f'_extinction_model {extinction.model.value}'))
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


def _cif_pref_orient_section(
    cif_lines: list[str],
    expt_type: object | None,
    experiment: object,
    linked_structure: object,
) -> None:
    """Append the cryspy texture (March-Dollase) loop for the phase.

    cryspy keys texture to a phase by ``_texture_label``, so only the
    ``pref_orient`` row whose ``phase_id`` matches the phase being
    calculated is emitted. A row with ``r = 1`` is a mathematical
    no-op; an empty collection (the default) emits nothing.
    """
    # Initial support is constant-wavelength only (ADR Deferred Work);
    # the TOF pass-through is not wired, so a TOF texture loop would
    # go stale on refinement. Emit nothing for TOF to keep the scope
    # consistent end to end.
    if (
        expt_type is None
        or expt_type.sample_form.value != SampleFormEnum.POWDER
        or expt_type.beam_mode.value != BeamModeEnum.CONSTANT_WAVELENGTH
    ):
        return
    pref_orient = getattr(experiment, 'preferred_orientation', None)
    if pref_orient is None:
        return
    phase_label = linked_structure.name
    row = next(
        (item for item in pref_orient if item.phase_id.value == phase_label),
        None,
    )
    if row is None:
        return
    cif_lines.extend((
        '',
        'loop_',
        '_texture_label',
        '_texture_g_1',
        '_texture_g_2',
        '_texture_h_ax',
        '_texture_k_ax',
        '_texture_l_ax',
        f'{phase_label} {row.r.value} {row.fraction.value} '
        f'{row.index_h.value} {row.index_k.value} {row.index_l.value}',
    ))


def _update_texture_in_cryspy_dict(
    cryspy_expt_dict: dict[str, Any],
    experiment: object,
) -> None:
    """Patch cryspy texture ``g_1``/``g_2`` from preferred-orientation rows.

    Matches each emitted texture row to a ``pref_orient`` row by phase
    label and writes the refinable coefficient and random fraction in
    place. ``h/k/l`` are fixed descriptors, so ``texture_axis`` is never
    touched. No-op when no texture loop was emitted.
    """
    if 'texture_g1' not in cryspy_expt_dict:
        return
    pref_orient = getattr(experiment, 'preferred_orientation', None)
    if pref_orient is None:
        return
    rows = {item.phase_id.value: item for item in pref_orient}
    for index, label in enumerate(cryspy_expt_dict['texture_name']):
        row = rows.get(str(label))
        if row is not None:
            cryspy_expt_dict['texture_g1'][index] = row.r.value
            cryspy_expt_dict['texture_g2'][index] = row.fraction.value


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
    data = experiment.refln
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
    # A generated (calculate-without-measured-data) grid carries absent
    # (NaN) measured intensities. cryspy only needs the x-grid to
    # compute the pattern, so write finite placeholders rather than
    # 'nan' tokens that the engine input parser would choke on.
    y_data = np.nan_to_num(np.asarray(experiment.data.intensity_meas, dtype=float), nan=0.0)
    sy_raw = np.asarray(experiment.data.intensity_meas_su, dtype=float)
    sy_data = np.where(np.isfinite(sy_raw), sy_raw, 1.0)
    for x_val, y_val, sy_val in zip(x_data, y_data, sy_data, strict=True):
        cif_lines.append(f'  {x_val:.5f}   {y_val:.5f}   {sy_val:.5f}')
