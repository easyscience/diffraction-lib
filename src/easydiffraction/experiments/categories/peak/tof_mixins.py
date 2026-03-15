# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight (TOF) peak-profile mixins.

Defines mixins that add Gaussian/Lorentz broadening, mixing, and
Ikeda–Carpenter asymmetry parameters used by TOF peak shapes.
"""

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class TofBroadeningMixin:
    """Mixin that adds TOF Gaussian/Lorentz broadening and mixing
    terms.
    """

    def _add_time_of_flight_broadening(self) -> None:
        """Create TOF broadening and mixing parameters."""
        self._broad_gauss_sigma_0 = Parameter(
            name='gauss_sigma_0',
            description='Gaussian broadening coefficient (instrumental resolution)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs²',
            cif_handler=CifHandler(names=['_peak.gauss_sigma_0']),
        )
        self._broad_gauss_sigma_1 = Parameter(
            name='gauss_sigma_1',
            description='Gaussian broadening coefficient (dependent on d-spacing)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs/Å',
            cif_handler=CifHandler(names=['_peak.gauss_sigma_1']),
        )
        self._broad_gauss_sigma_2 = Parameter(
            name='gauss_sigma_2',
            description='Gaussian broadening coefficient (instrument-dependent term)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs²/Å²',
            cif_handler=CifHandler(names=['_peak.gauss_sigma_2']),
        )
        self._broad_lorentz_gamma_0 = Parameter(
            name='lorentz_gamma_0',
            description='Lorentzian broadening coefficient (dependent on microstrain effects)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs',
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_0']),
        )
        self._broad_lorentz_gamma_1 = Parameter(
            name='lorentz_gamma_1',
            description='Lorentzian broadening coefficient (dependent on d-spacing)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs/Å',
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_1']),
        )
        self._broad_lorentz_gamma_2 = Parameter(
            name='lorentz_gamma_2',
            description='Lorentzian broadening coefficient (instrument-dependent term)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='µs²/Å²',
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_2']),
        )
        self._broad_mix_beta_0 = Parameter(
            name='mix_beta_0',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_peak.mix_beta_0']),
        )
        self._broad_mix_beta_1 = Parameter(
            name='mix_beta_1',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_peak.mix_beta_1']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def broad_gauss_sigma_0(self):
        return self._broad_gauss_sigma_0

    @broad_gauss_sigma_0.setter
    def broad_gauss_sigma_0(self, value) -> None:
        self._broad_gauss_sigma_0.value = value

    @property
    def broad_gauss_sigma_1(self):
        return self._broad_gauss_sigma_1

    @broad_gauss_sigma_1.setter
    def broad_gauss_sigma_1(self, value) -> None:
        self._broad_gauss_sigma_1.value = value

    @property
    def broad_gauss_sigma_2(self):
        return self._broad_gauss_sigma_2

    @broad_gauss_sigma_2.setter
    def broad_gauss_sigma_2(self, value) -> None:
        """Set Gaussian sigma_2 parameter."""
        self._broad_gauss_sigma_2.value = value

    @property
    def broad_lorentz_gamma_0(self):
        return self._broad_lorentz_gamma_0

    @broad_lorentz_gamma_0.setter
    def broad_lorentz_gamma_0(self, value) -> None:
        self._broad_lorentz_gamma_0.value = value

    @property
    def broad_lorentz_gamma_1(self):
        return self._broad_lorentz_gamma_1

    @broad_lorentz_gamma_1.setter
    def broad_lorentz_gamma_1(self, value) -> None:
        self._broad_lorentz_gamma_1.value = value

    @property
    def broad_lorentz_gamma_2(self):
        return self._broad_lorentz_gamma_2

    @broad_lorentz_gamma_2.setter
    def broad_lorentz_gamma_2(self, value) -> None:
        self._broad_lorentz_gamma_2.value = value

    @property
    def broad_mix_beta_0(self):
        return self._broad_mix_beta_0

    @broad_mix_beta_0.setter
    def broad_mix_beta_0(self, value) -> None:
        self._broad_mix_beta_0.value = value

    @property
    def broad_mix_beta_1(self):
        return self._broad_mix_beta_1

    @broad_mix_beta_1.setter
    def broad_mix_beta_1(self, value) -> None:
        self._broad_mix_beta_1.value = value


class IkedaCarpenterAsymmetryMixin:
    """Mixin that adds Ikeda–Carpenter asymmetry parameters."""

    def _add_ikeda_carpenter_asymmetry(self) -> None:
        """Create Ikeda–Carpenter asymmetry parameters alpha_0 and
        alpha_1.
        """
        self._asym_alpha_0 = Parameter(
            name='asym_alpha_0',
            description='Ikeda-Carpenter asymmetry parameter α₀',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_alpha_0']),
        )
        self._asym_alpha_1 = Parameter(
            name='asym_alpha_1',
            description='Ikeda-Carpenter asymmetry parameter α₁',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_alpha_1']),
        )

    @property
    def asym_alpha_0(self) -> Parameter:
        return self._asym_alpha_0

    @asym_alpha_0.setter
    def asym_alpha_0(self, value) -> None:
        self._asym_alpha_0.value = value

    @property
    def asym_alpha_1(self) -> Parameter:
        return self._asym_alpha_1

    @asym_alpha_1.setter
    def asym_alpha_1(self, value) -> None:
        self._asym_alpha_1.value = value
