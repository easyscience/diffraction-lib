# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Total scattering / pair distribution function (PDF) peak-profile
component classes.

This module provides classes that add broadening and asymmetry
parameters. They are composed into concrete peak classes elsewhere via
multiple inheritance.
"""

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
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
    def damp_q(self):
        return self._damp_q

    @damp_q.setter
    def damp_q(self, value):
        self._damp_q.value = value

    @property
    def broad_q(self):
        return self._broad_q

    @broad_q.setter
    def broad_q(self, value):
        self._broad_q.value = value

    @property
    def cutoff_q(self) -> Parameter:
        return self._cutoff_q

    @cutoff_q.setter
    def cutoff_q(self, value):
        self._cutoff_q.value = value

    @property
    def sharp_delta_1(self) -> Parameter:
        return self._sharp_delta_1

    @sharp_delta_1.setter
    def sharp_delta_1(self, value):
        self._sharp_delta_1.value = value

    @property
    def sharp_delta_2(self):
        return self._sharp_delta_2

    @sharp_delta_2.setter
    def sharp_delta_2(self, value):
        self._sharp_delta_2.value = value

    @property
    def damp_particle_diameter(self):
        return self._damp_particle_diameter

    @damp_particle_diameter.setter
    def damp_particle_diameter(self, value):
        self._damp_particle_diameter.value = value
