# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
CrysFML calculation backend for powder diffraction patterns.

Builds a CrysFML CFL description (``PATTERN_*`` and ``PHASE_*`` blocks)
from the structure and experiment and runs
``cfml_py_utilities.patterns_simulation`` to obtain the calculated
pattern. The backend uses the CFL API exclusively.

Notes
-----
The CFL ``patterns_simulation`` path only supports a uniform calculation
grid (``GEN_PATT xmin step xmax``); the grid is derived from the
experiment x-axis assuming uniform spacing. Constant-wavelength patterns
are fully supported. The upstream CFL simulation currently parses but
does not apply ``Zero_Sy`` when placing CW reflections, so the two-theta
zero is encoded by shifting the calculation grid. Time-of-flight
patterns parse but return zero intensities, because the upstream CFL
simulation does not yet implement the TOF branch.
"""

from __future__ import annotations

import string
from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.analysis.calculators import absorption as absorption_correction
from easydiffraction.analysis.calculators import polarization as polarization_correction
from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
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


def _cfl_label(name: str) -> str:
    """
    Return a whitespace-free label for a CFL block or atom name.

    CFL block headers (``PATTERN_<name>``, ``PHASE_<name>``) and atom
    labels are single whitespace-delimited tokens, so any internal
    whitespace in a user-supplied name is collapsed to underscores.

    Parameters
    ----------
    name : str
        Experiment, structure, or atom name.

    Returns
    -------
    str
        The name with internal whitespace replaced by underscores.
    """
    return '_'.join(str(name).split())


def _fmt(value: float) -> str:
    """
    Format a numeric value for a CFL free-format field.

    Parameters
    ----------
    value : float
        Value to format.

    Returns
    -------
    str
        Compact decimal representation with up to 8 significant figures.
    """
    return f'{float(value):.8g}'


# CrysFML's CFL default is 5 FWHM, which truncates pseudo-Voigt tails
# relative to the FullProf verification profiles.
_CW_BRAGG_WINDOW_FWHM = 30.0


@CalculatorFactory.register
class CrysfmlCalculator(CalculatorBase):
    """Wrapper for Crysfml library."""

    type_info = TypeInfo(
        tag='crysfml',
        description='CrysFML library for crystallographic calculations',
    )
    engine_imported: bool = cfml_py_utilities is not None and hasattr(
        cfml_py_utilities, 'patterns_simulation'
    )
    url: str = 'https://code.ill.fr/scientific-software/crysfml'

    def __init__(self) -> None:
        """Initialize CrysFML calculator state."""
        super().__init__()
        self._cw_doublet_fallback_warned = False

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

        x = np.asarray(experiment.data.x, dtype=float)
        if x.size == 0:
            return np.asarray([])

        cfl = self._crysfml_cfl(structure, experiment)
        try:
            y = self._calculate_adjusted_pattern(cfl, experiment)
        except (KeyError, IndexError):
            log.warning('[CrysfmlCalculator] No calculated data')
            y = []
        except RuntimeError as exc:
            # CrysFML signals an unsupported calculation by raising. The
            # CFL simulation cannot generate time-of-flight reflections,
            # so return a flat zero pattern (matching the experiment
            # length) instead of crashing the caller's pattern sum.
            log.warning(
                f'[CrysfmlCalculator] CrysFML could not simulate this pattern '
                f'(returning zeros). Time-of-flight data is not supported by '
                f'the CFL backend. Details: {exc}'
            )
            y = [0.0] * int(x.size)
        y = absorption_correction.apply(y, experiment)
        y = polarization_correction.apply(y, experiment)
        return np.asarray(y)

    def _calculate_adjusted_pattern(
        self,
        cfl: list[str],
        experiment: ExperimentBase,
    ) -> list[float]:
        """Calculate a Crysfml pattern and match experiment length."""
        if self._cw_doublet_is_active(experiment):
            y = self._calculate_cw_doublet_pattern(cfl, experiment)
        else:
            y = self._calculate_raw_pattern(cfl)
        if y is None or len(y) == 0:
            return []
        return self._adjust_pattern_length(list(y), len(experiment.data.x))

    def _calculate_cw_doublet_pattern(
        self,
        cfl: list[str],
        experiment: ExperimentBase,
    ) -> list[float] | None:
        """Calculate an active CW doublet pattern through CrysFML."""
        if not self._cw_doublet_fallback_warned:
            self._cw_doublet_fallback_warned = True
            log.warning(
                '[CrysfmlCalculator] Native CrysFML CW doublet is disabled; '
                'using two single-wavelength CFL simulations.'
            )
        return self._calculate_cw_doublet_from_single_wavelengths(cfl, experiment)

    def _calculate_cw_doublet_from_single_wavelengths(
        self,
        cfl: list[str],
        experiment: ExperimentBase,
    ) -> list[float] | None:
        """Calculate a CW doublet as weighted single-wavelength runs."""
        instrument = getattr(experiment, 'instrument', None)
        wavelength_1, wavelength_2, wavelength_ratio = self._cw_wavelengths(instrument)
        y_1 = self._calculate_raw_pattern(
            self._cfl_with_lambda(cfl, wavelength_1, wavelength_1, 0.0)
        )
        y_2 = self._calculate_raw_pattern(
            self._cfl_with_lambda(cfl, wavelength_2, wavelength_2, 0.0)
        )
        if y_1 is None or y_2 is None or len(y_1) == 0 or len(y_2) == 0:
            return None
        y_1_array = np.asarray(y_1, dtype=float)
        y_2_array = np.asarray(y_2, dtype=float)
        return list(y_1_array + wavelength_ratio * y_2_array)

    def _cw_doublet_is_active(self, experiment: ExperimentBase) -> bool:
        """Return whether a CW doublet is active."""
        beam_mode = experiment.experiment_type.beam_mode.value
        if beam_mode != BeamModeEnum.CONSTANT_WAVELENGTH:
            return False
        instrument = getattr(experiment, 'instrument', None)
        _wavelength_1, wavelength_2, wavelength_ratio = self._cw_wavelengths(instrument)
        return wavelength_2 > 0.0 and wavelength_ratio > 0.0

    @staticmethod
    def _cfl_with_lambda(
        cfl: list[str],
        wavelength_1: float,
        wavelength_2: float,
        wavelength_ratio: float,
    ) -> list[str]:
        """Return CFL lines with a replacement ``LAMBDA`` directive."""
        lambda_line = (
            f'  LAMBDA  {_fmt(wavelength_1)}  {_fmt(wavelength_2)}  {_fmt(wavelength_ratio)}'
        )
        return [
            lambda_line if line.lstrip().upper().startswith('LAMBDA') else line for line in cfl
        ]

    @staticmethod
    def _calculate_raw_pattern(cfl: list[str]) -> list[float] | None:
        """Run CrysFML and return first pattern y."""
        patterns = cfml_py_utilities.patterns_simulation(cfl)
        if not patterns:
            return None
        return patterns[0]['y']

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

    # ------------------------------------------------------------------
    #  CFL assembly
    # ------------------------------------------------------------------

    def _crysfml_cfl(
        self,
        structure: Structure,
        experiment: ExperimentBase,
    ) -> list[str]:
        """
        Build the CFL description for one structure-experiment pair.

        Parameters
        ----------
        structure : Structure
            The structure to serialise as a ``PHASE_*`` block.
        experiment : ExperimentBase
            The experiment to serialise as a ``PATTERN_*`` block.

        Returns
        -------
        list[str]
            The CFL file content as a list of lines.
        """
        return [
            *self._pattern_block(experiment),
            '',
            *self._phase_block(structure),
        ]

    def _pattern_block(self, experiment: ExperimentBase) -> list[str]:
        """Build the ``PATTERN_*`` block for the experiment."""
        name = _cfl_label(experiment.name)
        radiation = self._radiation_keyword(experiment)
        beam_mode = experiment.experiment_type.beam_mode.value

        if beam_mode == BeamModeEnum.TIME_OF_FLIGHT:
            patt_type = f'{radiation} Powder TOF'
            conditions = self._tof_condition_lines(experiment)
            xmin, step, xmax = self._x_grid(experiment)
        else:
            patt_type = f'{radiation} Powder CW'
            conditions = self._cw_condition_lines(experiment)
            xmin, step, xmax = self._cw_x_grid(experiment)

        return [
            f'PATTERN_{name}  1',
            f'  Patt_Type  {patt_type}',
            *conditions,
            f'  GEN_PATT  {_fmt(xmin)}  {_fmt(step)}  {_fmt(xmax)}',
            f'END_PATTERN_{name}',
        ]

    @staticmethod
    def _radiation_keyword(experiment: ExperimentBase) -> str:
        """Return the CFL ``Patt_Type`` radiation keyword."""
        probe = experiment.experiment_type.radiation_probe.value
        if probe == RadiationProbeEnum.XRAY:
            return 'X-rays'
        return 'Neutrons'

    def _cw_condition_lines(self, experiment: ExperimentBase) -> list[str]:
        """Build the constant-wavelength condition lines."""
        instrument = getattr(experiment, 'instrument', None)
        peak = getattr(experiment, 'peak', None)
        wavelength_1, wavelength_2, wavelength_ratio = self._cw_wavelengths(instrument)
        u = self._param(peak, 'broad_gauss_u', 0.0)
        v = self._param(peak, 'broad_gauss_v', 0.0)
        w = self._param(peak, 'broad_gauss_w', 0.0)
        x = self._param(peak, 'broad_lorentz_x', 0.0)
        y = self._param(peak, 'broad_lorentz_y', 0.0)
        asym1 = self._param(peak, 'asym_fcj_1', 0.0)
        asym2 = self._param(peak, 'asym_fcj_2', 0.0)
        return [
            '  Zero_Sy  0.0  0.0  0.0',
            f'  WDT  {_fmt(_CW_BRAGG_WINDOW_FWHM)}',
            '  Profile_function  TCH_pVoigt',
            f'  ASYM  {_fmt(asym1)}  {_fmt(asym2)}',
            (f'  LAMBDA  {_fmt(wavelength_1)}  {_fmt(wavelength_2)}  {_fmt(wavelength_ratio)}'),
            f'  UVWXY  {_fmt(u)}  {_fmt(v)}  {_fmt(w)}  {_fmt(x)}  {_fmt(y)}',
        ]

    def _cw_wavelengths(self, instrument: object | None) -> tuple[float, float, float]:
        """Return CrysFML CW wavelengths and relative intensity."""
        wavelength_1 = self._param(instrument, 'setup_wavelength', 0.0)
        wavelength_2 = self._param(instrument, 'setup_wavelength_2', 0.0)
        wavelength_ratio = self._param(
            instrument,
            'setup_wavelength_2_to_1_ratio',
            0.0,
        )
        if wavelength_2 > 0.0:
            return wavelength_1, wavelength_2, wavelength_ratio
        if wavelength_ratio > 0.0:
            msg = (
                'setup_wavelength_2_to_1_ratio requires a positive '
                'setup_wavelength_2 value for CrysFML CW patterns.'
            )
            raise ValueError(msg)
        return wavelength_1, wavelength_1, 0.0

    def _tof_condition_lines(self, experiment: ExperimentBase) -> list[str]:
        """Build the time-of-flight condition lines."""
        instrument = getattr(experiment, 'instrument', None)
        zero = self._param(instrument, 'calib_d_to_tof_offset', 0.0)
        dtt1 = self._param(instrument, 'calib_d_to_tof_linear', 0.0)
        dtt2 = self._param(instrument, 'calib_d_to_tof_quadratic', 0.0)
        return [f'  D2TOF  {_fmt(zero)}  {_fmt(dtt1)}  {_fmt(dtt2)}']

    @staticmethod
    def _x_grid(experiment: ExperimentBase) -> tuple[float, float, float]:
        """
        Return ``(xmin, step, xmax)`` for the uniform CFL grid.

        The step is derived assuming uniform spacing of the experiment
        x-axis; ``GEN_PATT`` then regenerates the same number of points.
        """
        x = np.asarray(experiment.data.x, dtype=float)
        xmin = float(x[0])
        xmax = float(x[-1])
        step = (xmax - xmin) / (len(x) - 1) if len(x) > 1 else 1.0
        return xmin, step, xmax

    def _cw_x_grid(self, experiment: ExperimentBase) -> tuple[float, float, float]:
        """Return the CW grid with two-theta zero encoded in x."""
        xmin, step, xmax = self._x_grid(experiment)
        instrument = getattr(experiment, 'instrument', None)
        zero = self._param(instrument, 'calib_twotheta_offset', 0.0)
        return xmin - zero, step, xmax - zero

    def _phase_block(self, structure: Structure) -> list[str]:
        """Build the ``PHASE_*`` block for the structure."""
        name = _cfl_label(structure.name)
        cell = structure.cell
        lines = [
            f'PHASE_{name}  1',
            (
                f'  Cell  {_fmt(cell.length_a.value)}  {_fmt(cell.length_b.value)}  '
                f'{_fmt(cell.length_c.value)}  {_fmt(cell.angle_alpha.value)}  '
                f'{_fmt(cell.angle_beta.value)}  {_fmt(cell.angle_gamma.value)}'
            ),
            f'  SPGR  {structure.space_group.name_h_m.value}',
        ]
        lines.extend(self._atom_line(atom, structure) for atom in structure.atom_sites)
        lines.extend([
            '  Contributes_to_patterns  1',
            '  Scale_Factors  1.0',
            f'END_PHASE_{name}',
        ])
        return lines

    def _atom_line(self, atom: object, structure: Structure) -> str:
        """Build one CFL ``Atom`` line."""
        occupancy = self._normalized_occupancy(atom, structure)
        return (
            f'  Atom  {_cfl_label(atom.id.value)}  '
            f'{_element_symbol(atom.type_symbol.value)}  '
            f'{_fmt(atom.fract_x.value)}  {_fmt(atom.fract_y.value)}  '
            f'{_fmt(atom.fract_z.value)}  {_fmt(atom.adp_iso_as_b)}  '
            f'{_fmt(occupancy)}'
        )

    def _normalized_occupancy(self, atom: object, structure: Structure) -> float:
        """
        Return FullProf occupancy for a CFL ``Atom`` line.

        CFL expects a site-normalized occupancy, whereas the model
        stores plain crystallographic occupancy. When the multiplicities
        cannot be resolved (untabulated space group), the plain
        occupancy is used and a warning is emitted.

        Parameters
        ----------
        atom : object
            The atom site whose occupancy is converted.
        structure : Structure
            The parent structure, used for the space group.

        Returns
        -------
        float
            The occupancy value to write in the CFL ``Atom`` line.
        """
        occupancy = atom.occupancy.value
        factor = self._occupancy_multiplicity_factor(atom, structure)
        if factor is None:
            log.warning(
                f'[CrysfmlCalculator] Could not resolve site multiplicity for '
                f"atom '{atom.id.value}' in space group "
                f"'{structure.space_group.name_h_m.value}'; using unnormalized "
                f'occupancy, which may scale this phase incorrectly.'
            )
            return occupancy
        return occupancy * factor

    @staticmethod
    def _occupancy_multiplicity_factor(
        atom: object,
        structure: Structure,
    ) -> float | None:
        """
        Return ``site_multiplicity / general_multiplicity`` or ``None``.

        Returns ``None`` when the space group is untabulated or the site
        multiplicity cannot be determined.
        """
        space_group = structure.space_group
        name_hm = space_group.name_h_m.value
        coord_code = space_group.coord_system_code.value
        table = ecr.space_group_wyckoff_table(name_hm, coord_code)
        if not table:
            return None
        general_mult = max(int(position['multiplicity']) for position in table.values())
        if general_mult <= 0:
            return None

        site_mult = atom.multiplicity.value
        if site_mult is None:
            position = ecr.detect_wyckoff_position(
                name_hm,
                coord_code,
                (atom.fract_x.value, atom.fract_y.value, atom.fract_z.value),
            )
            site_mult = position.multiplicity if position is not None else None
        if site_mult is None:
            return None
        return site_mult / general_mult

    @staticmethod
    def _param(source: object, attribute_name: str, default: float) -> float:
        """Return a numeric ``value`` or default."""
        if source is None or not hasattr(source, attribute_name):
            return default
        return getattr(source, attribute_name).value
