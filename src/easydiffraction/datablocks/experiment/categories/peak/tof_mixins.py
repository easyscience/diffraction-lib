# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Time-of-flight (TOF) peak-profile mixin classes.

Defines parameter mixins for TOF peak shapes based on the Jorgensen
back-to-back exponential (BBE) formalism:

- ``TofGaussianBroadeningMixin`` — σ₀, σ₁, σ₂
- ``TofLorentzianBroadeningMixin`` — γ₀, γ₁, γ₂
- ``TofBackToBackExponentialMixin`` — α₀, α₁ (rise), β₀, β₁ (decay)
- ``TofDoubleExponentialMixin`` — α₁, α₂ (rise), β₀₀, β₀₁, β₁₀ (decay),
  r₀₁, r₀₂, r₀₃ (switching function) for double-BBE (Z-Rietveld type0m)

These are composed into concrete peak classes in ``tof.py``.
"""

from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler


class TofGaussianBroadeningMixin:
    """TOF Gaussian broadening parameters σ₀, σ₁, σ₂."""

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


class TofLorentzianBroadeningMixin:
    """TOF Lorentzian broadening parameters γ₀, γ₁, γ₂."""

    def __init__(self) -> None:
        super().__init__()

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


class TofBackToBackExponentialMixin:
    """
    Back-to-back exponential (BBE) rise and decay parameters.

    Rise parameters α₀, α₁ and decay parameters β₀, β₁ follow Von
    Dreele, Jorgensen & Windsor, J. Appl. Cryst. 15, 581 (1982).
    """

    def __init__(self) -> None:
        super().__init__()

        self._exp_rise_alpha_0 = Parameter(
            name='rise_alpha_0',
            description='Back-to-back exponential rise α₀',
            units='μs',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.rise_alpha_0']),
        )
        self._exp_rise_alpha_1 = Parameter(
            name='rise_alpha_1',
            description='Back-to-back exponential rise α₁',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.rise_alpha_1']),
        )
        self._exp_decay_beta_0 = Parameter(
            name='decay_beta_0',
            description='Back-to-back exponential decay β₀',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.decay_beta_0']),
        )
        self._exp_decay_beta_1 = Parameter(
            name='decay_beta_1',
            description='Back-to-back exponential decay β₁',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.decay_beta_1']),
        )

    @property
    def exp_rise_alpha_0(self) -> Parameter:
        """
        Back-to-back exponential rise α₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._exp_rise_alpha_0

    @exp_rise_alpha_0.setter
    def exp_rise_alpha_0(self, value: float) -> None:
        self._exp_rise_alpha_0.value = value

    @property
    def exp_rise_alpha_1(self) -> Parameter:
        """
        Back-to-back exponential rise α₁ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._exp_rise_alpha_1

    @exp_rise_alpha_1.setter
    def exp_rise_alpha_1(self, value: float) -> None:
        self._exp_rise_alpha_1.value = value

    @property
    def exp_decay_beta_0(self) -> Parameter:
        """
        Back-to-back exponential decay β₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._exp_decay_beta_0

    @exp_decay_beta_0.setter
    def exp_decay_beta_0(self, value: float) -> None:
        self._exp_decay_beta_0.value = value

    @property
    def exp_decay_beta_1(self) -> Parameter:
        """
        Back-to-back exponential decay β₁ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._exp_decay_beta_1

    @exp_decay_beta_1.setter
    def exp_decay_beta_1(self, value: float) -> None:
        self._exp_decay_beta_1.value = value


class TofDoubleExponentialMixin:
    """
    Double back-to-back exponential parameters for Z-Rietveld type0m.

    Rise parameters α₁, α₂, decay parameters β₀₀, β₀₁, β₁₀ for two
    exponential regimes, and switching-function parameters r₀₁, r₀₂,
    r₀₃.
    """

    def __init__(self) -> None:
        super().__init__()

        self._dexp_rise_alpha_1 = Parameter(
            name='dexp_rise_alpha_1',
            description='Double-exp rise parameter α₁',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_rise_alpha_1']),
        )
        self._dexp_rise_alpha_2 = Parameter(
            name='dexp_rise_alpha_2',
            description='Double-exp rise parameter α₂',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_rise_alpha_2']),
        )
        self._dexp_decay_beta_00 = Parameter(
            name='dexp_decay_beta_00',
            description='Double-exp first-regime decay β₀₀',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_decay_beta_00']),
        )
        self._dexp_decay_beta_01 = Parameter(
            name='dexp_decay_beta_01',
            description='Double-exp first-regime decay β₀₁',
            units='μs/Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_decay_beta_01']),
        )
        self._dexp_decay_beta_10 = Parameter(
            name='dexp_decay_beta_10',
            description='Double-exp second-regime decay β₁₀',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_decay_beta_10']),
        )
        self._dexp_switch_r_01 = Parameter(
            name='dexp_switch_r_01',
            description='Double-exp switching function r₀₁',
            units='',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_switch_r_01']),
        )
        self._dexp_switch_r_02 = Parameter(
            name='dexp_switch_r_02',
            description='Double-exp switching function r₀₂',
            units='',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_switch_r_02']),
        )
        self._dexp_switch_r_03 = Parameter(
            name='dexp_switch_r_03',
            description='Double-exp switching function r₀₃',
            units='',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.dexp_switch_r_03']),
        )

    @property
    def dexp_rise_alpha_1(self) -> Parameter:
        """
        Double-exp rise parameter α₁ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_rise_alpha_1

    @dexp_rise_alpha_1.setter
    def dexp_rise_alpha_1(self, value: float) -> None:
        self._dexp_rise_alpha_1.value = value

    @property
    def dexp_rise_alpha_2(self) -> Parameter:
        """
        Double-exp rise parameter α₂ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_rise_alpha_2

    @dexp_rise_alpha_2.setter
    def dexp_rise_alpha_2(self, value: float) -> None:
        self._dexp_rise_alpha_2.value = value

    @property
    def dexp_decay_beta_00(self) -> Parameter:
        """
        Double-exp first-regime decay β₀₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_decay_beta_00

    @dexp_decay_beta_00.setter
    def dexp_decay_beta_00(self, value: float) -> None:
        self._dexp_decay_beta_00.value = value

    @property
    def dexp_decay_beta_01(self) -> Parameter:
        """
        Double-exp first-regime decay β₀₁ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_decay_beta_01

    @dexp_decay_beta_01.setter
    def dexp_decay_beta_01(self, value: float) -> None:
        self._dexp_decay_beta_01.value = value

    @property
    def dexp_decay_beta_10(self) -> Parameter:
        """
        Double-exp second-regime decay β₁₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_decay_beta_10

    @dexp_decay_beta_10.setter
    def dexp_decay_beta_10(self, value: float) -> None:
        self._dexp_decay_beta_10.value = value

    @property
    def dexp_switch_r_01(self) -> Parameter:
        """
        Double-exp switching function r₀₁.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_switch_r_01

    @dexp_switch_r_01.setter
    def dexp_switch_r_01(self, value: float) -> None:
        self._dexp_switch_r_01.value = value

    @property
    def dexp_switch_r_02(self) -> Parameter:
        """
        Double-exp switching function r₀₂.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_switch_r_02

    @dexp_switch_r_02.setter
    def dexp_switch_r_02(self, value: float) -> None:
        self._dexp_switch_r_02.value = value

    @property
    def dexp_switch_r_03(self) -> Parameter:
        """
        Double-exp switching function r₀₃.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._dexp_switch_r_03

    @dexp_switch_r_03.setter
    def dexp_switch_r_03(self, value: float) -> None:
        self._dexp_switch_r_03.value = value
