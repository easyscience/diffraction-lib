# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Time-of-flight (TOF) peak-profile component classes.

Defines classes that add Gaussian/Lorentz broadening, mixing, and
Ikeda-Carpenter asymmetry parameters used by TOF peak shapes. This
module provides classes that add broadening and asymmetry parameters.
They are composed into concrete peak classes elsewhere via multiple
inheritance.
"""

from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler


class TofBroadeningMixin:
    """TOF Gaussian/Lorentz broadening and mixing parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._broad_gauss_sigma_0 = Parameter(
            name='gauss_sigma_0',
            description='Gaussian broadening (instrumental resolution)',
            units='μs²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.gauss_sigma_0']),
        )
        self._broad_gauss_sigma_1 = Parameter(
            name='gauss_sigma_1',
            description='Gaussian broadening (dependent on d-spacing)',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.gauss_sigma_1']),
        )
        self._broad_gauss_sigma_2 = Parameter(
            name='gauss_sigma_2',
            description='Gaussian broadening (instrument-dependent term)',
            units='μs²/Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.gauss_sigma_2']),
        )
        self._broad_lorentz_gamma_0 = Parameter(
            name='lorentz_gamma_0',
            description='Lorentzian broadening (microstrain effects)',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_0']),
        )
        self._broad_lorentz_gamma_1 = Parameter(
            name='lorentz_gamma_1',
            description='Lorentzian broadening (dependent on d-spacing)',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_1']),
        )
        self._broad_lorentz_gamma_2 = Parameter(
            name='lorentz_gamma_2',
            description='Lorentzian broadening (instrument-dependent term)',
            units='μs²/Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.lorentz_gamma_2']),
        )
        self._broad_mix_beta_0 = Parameter(
            name='mix_beta_0',
            description='Ratio of Gaussian to Lorentzian contributions',
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.mix_beta_0']),
        )
        self._broad_mix_beta_1 = Parameter(
            name='mix_beta_1',
            description='Ratio of Gaussian to Lorentzian contributions',
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.mix_beta_1']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def broad_gauss_sigma_0(self) -> Parameter:
        """
        Gaussian broadening (instrumental resolution) (μs²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_sigma_0

    @broad_gauss_sigma_0.setter
    def broad_gauss_sigma_0(self, value: float) -> None:
        self._broad_gauss_sigma_0.value = value

    @property
    def broad_gauss_sigma_1(self) -> Parameter:
        """
        Gaussian broadening (dependent on d-spacing) (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_sigma_1

    @broad_gauss_sigma_1.setter
    def broad_gauss_sigma_1(self, value: float) -> None:
        self._broad_gauss_sigma_1.value = value

    @property
    def broad_gauss_sigma_2(self) -> Parameter:
        """
        Gaussian broadening (instrument-dependent term) (μs²/Å²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_sigma_2

    @broad_gauss_sigma_2.setter
    def broad_gauss_sigma_2(self, value: float) -> None:
        self._broad_gauss_sigma_2.value = value

    @property
    def broad_lorentz_gamma_0(self) -> Parameter:
        """
        Lorentzian broadening (microstrain effects) (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_lorentz_gamma_0

    @broad_lorentz_gamma_0.setter
    def broad_lorentz_gamma_0(self, value: float) -> None:
        self._broad_lorentz_gamma_0.value = value

    @property
    def broad_lorentz_gamma_1(self) -> Parameter:
        """
        Lorentzian broadening (dependent on d-spacing) (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_lorentz_gamma_1

    @broad_lorentz_gamma_1.setter
    def broad_lorentz_gamma_1(self, value: float) -> None:
        self._broad_lorentz_gamma_1.value = value

    @property
    def broad_lorentz_gamma_2(self) -> Parameter:
        """
        Lorentzian broadening (instrument-dependent term) (μs²/Å²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_lorentz_gamma_2

    @broad_lorentz_gamma_2.setter
    def broad_lorentz_gamma_2(self, value: float) -> None:
        self._broad_lorentz_gamma_2.value = value

    @property
    def broad_mix_beta_0(self) -> Parameter:
        """
        Ratio of Gaussian to Lorentzian contributions (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_mix_beta_0

    @broad_mix_beta_0.setter
    def broad_mix_beta_0(self, value: float) -> None:
        self._broad_mix_beta_0.value = value

    @property
    def broad_mix_beta_1(self) -> Parameter:
        """
        Ratio of Gaussian to Lorentzian contributions (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_mix_beta_1

    @broad_mix_beta_1.setter
    def broad_mix_beta_1(self, value: float) -> None:
        self._broad_mix_beta_1.value = value


class IkedaCarpenterAsymmetryMixin:
    """Ikeda-Carpenter asymmetry parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._asym_alpha_0 = Parameter(
            name='asym_alpha_0',
            description='Ikeda-Carpenter asymmetry parameter α₀',
            units='',  # TODO
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_alpha_0']),
        )
        self._asym_alpha_1 = Parameter(
            name='asym_alpha_1',
            description='Ikeda-Carpenter asymmetry parameter α₁',
            units='',  # TODO
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_alpha_1']),
        )

    @property
    def asym_alpha_0(self) -> Parameter:
        """
        Ikeda-Carpenter asymmetry parameter α₀.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_alpha_0

    @asym_alpha_0.setter
    def asym_alpha_0(self, value: float) -> None:
        self._asym_alpha_0.value = value

    @property
    def asym_alpha_1(self) -> Parameter:
        """
        Ikeda-Carpenter asymmetry parameter α₁.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_alpha_1

    @asym_alpha_1.setter
    def asym_alpha_1(self, value: float) -> None:
        self._asym_alpha_1.value = value
