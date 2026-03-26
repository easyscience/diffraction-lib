# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Total scattering / pair distribution function (PDF) peak-profile
component classes.

This module provides classes that add broadening and asymmetry
parameters. They are composed into concrete peak classes elsewhere via
multiple inheritance.
"""

from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler


class TotalBroadeningMixin:
    """PDF broadening/damping/sharpening parameters."""

    def __init__(self):
        super().__init__()

        self._damp_q = Parameter(
            name='damp_q',
            description='Instrumental Q-resolution damping factor '
            '(affects high-r PDF peak amplitude)',
            units='Å⁻¹',
            value_spec=AttributeSpec(
                default=0.05,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.damp_q']),
        )
        self._broad_q = Parameter(
            name='broad_q',
            description='Quadratic PDF peak broadening coefficient '
            '(thermal and model uncertainty contribution)',
            units='Å⁻²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_q']),
        )
        self._cutoff_q = Parameter(
            name='cutoff_q',
            description='Q-value cutoff applied to model PDF for Fourier '
            'transform (controls real-space resolution)',
            units='Å⁻¹',
            value_spec=AttributeSpec(
                default=25.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.cutoff_q']),
        )
        self._sharp_delta_1 = Parameter(
            name='sharp_delta_1',
            description='PDF peak sharpening coefficient (1/r dependence)',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.sharp_delta_1']),
        )
        self._sharp_delta_2 = Parameter(
            name='sharp_delta_2',
            description='PDF peak sharpening coefficient (1/r² dependence)',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.sharp_delta_2']),
        )
        self._damp_particle_diameter = Parameter(
            name='damp_particle_diameter',
            description='Particle diameter for spherical envelope damping correction in PDF',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.damp_particle_diameter']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def damp_q(self) -> Parameter:
        """Instrumental Q-resolution damping factor (affects high-r PDF
        peak amplitude).

        Returns:
            Parameter: Instrumental Q-resolution damping factor (affects high-r PDF peak amplitude) (Å⁻¹).
        """
        return self._damp_q

    @damp_q.setter
    def damp_q(self, value: float) -> None:
        """Set the instrumental Q-resolution damping factor (affects
        high-r PDF peak amplitude).

        Args:
            value (float): Instrumental Q-resolution damping factor (affects high-r PDF peak amplitude) (Å⁻¹).
        """
        self._damp_q.value = value

    @property
    def broad_q(self) -> Parameter:
        """Quadratic PDF peak broadening coefficient (thermal and model
        uncertainty contribution).

        Returns:
            Parameter: Quadratic PDF peak broadening coefficient (thermal and model uncertainty contribution) (Å⁻²).
        """
        return self._broad_q

    @broad_q.setter
    def broad_q(self, value: float) -> None:
        """Set the quadratic PDF peak broadening coefficient (thermal
        and model uncertainty contribution).

        Args:
            value (float): Quadratic PDF peak broadening coefficient (thermal and model uncertainty contribution) (Å⁻²).
        """
        self._broad_q.value = value

    @property
    def cutoff_q(self) -> Parameter:
        """Q-value cutoff applied to model PDF for Fourier transform
        (controls real-space resolution).

        Returns:
            Parameter: Q-value cutoff applied to model PDF for Fourier transform (controls real-space resolution) (Å⁻¹).
        """
        return self._cutoff_q

    @cutoff_q.setter
    def cutoff_q(self, value: float) -> None:
        """Set the q-value cutoff applied to model PDF for Fourier
        transform (controls real-space resolution).

        Args:
            value (float): Q-value cutoff applied to model PDF for Fourier transform (controls real-space resolution) (Å⁻¹).
        """
        self._cutoff_q.value = value

    @property
    def sharp_delta_1(self) -> Parameter:
        """PDF peak sharpening coefficient (1/r dependence).

        Returns:
            Parameter: PDF peak sharpening coefficient (1/r dependence) (Å).
        """
        return self._sharp_delta_1

    @sharp_delta_1.setter
    def sharp_delta_1(self, value: float) -> None:
        """Set the pDF peak sharpening coefficient (1/r dependence).

        Args:
            value (float): PDF peak sharpening coefficient (1/r dependence) (Å).
        """
        self._sharp_delta_1.value = value

    @property
    def sharp_delta_2(self) -> Parameter:
        """PDF peak sharpening coefficient (1/r² dependence).

        Returns:
            Parameter: PDF peak sharpening coefficient (1/r² dependence) (Å²).
        """
        return self._sharp_delta_2

    @sharp_delta_2.setter
    def sharp_delta_2(self, value: float) -> None:
        """Set the pDF peak sharpening coefficient (1/r² dependence).

        Args:
            value (float): PDF peak sharpening coefficient (1/r² dependence) (Å²).
        """
        self._sharp_delta_2.value = value

    @property
    def damp_particle_diameter(self) -> Parameter:
        """Particle diameter for spherical envelope damping correction
        in PDF.

        Returns:
            Parameter: Particle diameter for spherical envelope damping correction in PDF (Å).
        """
        return self._damp_particle_diameter

    @damp_particle_diameter.setter
    def damp_particle_diameter(self, value: float) -> None:
        """Set the particle diameter for spherical envelope damping
        correction in PDF.

        Args:
            value (float): Particle diameter for spherical envelope damping correction in PDF (Å).
        """
        self._damp_particle_diameter.value = value
