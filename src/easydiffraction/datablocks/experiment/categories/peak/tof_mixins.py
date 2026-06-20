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

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import TagSpec


class TofGaussianBroadeningMixin:
    """
    TOF Gaussian broadening parameters σ₀, σ₁, σ₂.

    The constant term σ₀ defaults nonzero so every TOF profile has a
    finite peak width out of the box; σ₁ and σ₂ default to 0.
    """

    def __init__(self) -> None:
        """Initialize the TOF Gaussian broadening parameters."""
        super().__init__()

        self._broad_gauss_sigma_0 = Parameter(
            name='broad_gauss_sigma_0',
            description='Gaussian broadening (instrumental resolution)',
            units='microseconds_squared',
            display_handler=DisplayHandler(
                display_units='μs²',
                latex_units=r'$\mu\mathrm{s}^2$',
            ),
            value_spec=AttributeSpec(
                default=7.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_sigma_0'],
                cif_names=['_easydiffraction_peak.broad_gauss_sigma_0'],
            ),
        )
        self._broad_gauss_sigma_1 = Parameter(
            name='broad_gauss_sigma_1',
            description='Gaussian broadening (dependent on d-spacing)',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_sigma_1'],
                cif_names=['_easydiffraction_peak.broad_gauss_sigma_1'],
            ),
        )
        self._broad_gauss_sigma_2 = Parameter(
            name='broad_gauss_sigma_2',
            description='Gaussian broadening (instrument-dependent term)',
            units='microseconds_squared_per_angstrom_squared',
            display_handler=DisplayHandler(
                display_units='μs²/Å²',
                latex_units=r'$\mu\mathrm{s}^2/\mathrm{\AA}^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_sigma_2'],
                cif_names=['_easydiffraction_peak.broad_gauss_sigma_2'],
            ),
        )
        self._broad_gauss_size_g = Parameter(
            name='broad_gauss_size_g',
            description='Gaussian isotropic size broadening (adds to sigma2)',
            units='microseconds_squared_per_angstrom_squared',
            display_handler=DisplayHandler(
                display_units='μs²/Å²',
                latex_units=r'$\mu\mathrm{s}^2/\mathrm{\AA}^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_size_g'],
                cif_names=['_easydiffraction_peak.broad_gauss_size_g'],
            ),
        )
        self._broad_gauss_strain_g = Parameter(
            name='broad_gauss_strain_g',
            description='Gaussian isotropic strain broadening (adds to sigma1)',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_strain_g'],
                cif_names=['_easydiffraction_peak.broad_gauss_strain_g'],
            ),
        )
        self._cutoff_fwhm = NumericDescriptor(
            name='cutoff_fwhm',
            description='Peak-range cutoff in FWHMs (speed vs accuracy; '
            'FullProf "WDT"). Larger is more accurate but slower.',
            units='',
            display_handler=DisplayHandler(
                display_name='Cutoff (FWHM)',
                latex_name='WDT',
            ),
            value_spec=AttributeSpec(
                default=10.0,
                validator=RangeValidator(gt=0.0),
            ),
            tags=TagSpec(
                edi_names=['_peak.cutoff_fwhm'],
                cif_names=['_easydiffraction_peak.cutoff_fwhm'],
            ),
        )

    @property
    def cutoff_fwhm(self) -> NumericDescriptor:
        """
        Peak-range cutoff in FWHMs (speed vs accuracy).

        The profile is evaluated only within this many FWHMs of each
        peak; larger values are more accurate but slower. Mirrors
        FullProf's ``WDT``. Reading returns the underlying descriptor;
        assigning updates its value.
        """
        return self._cutoff_fwhm

    @cutoff_fwhm.setter
    def cutoff_fwhm(self, value: float) -> None:
        """Set the peak-range cutoff (FWHMs)."""
        self._cutoff_fwhm.value = value

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
        """Set Gaussian broadening (instrumental resolution) (μs²)."""
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
        """Set Gaussian broadening (dependent on d-spacing) (μs/Å)."""
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
        """Set Gaussian broadening (instrument term) (μs²/Å²)."""
        self._broad_gauss_sigma_2.value = value

    @property
    def broad_gauss_size_g(self) -> Parameter:
        """Gaussian isotropic size broadening, additive to σ₂ (μs²/Å²)."""
        return self._broad_gauss_size_g

    @broad_gauss_size_g.setter
    def broad_gauss_size_g(self, value: float) -> None:
        """Set Gaussian isotropic size broadening, additive to σ₂ (μs²/Å²)."""
        self._broad_gauss_size_g.value = value

    @property
    def broad_gauss_strain_g(self) -> Parameter:
        """Gaussian isotropic strain broadening, additive to σ₁ (μs/Å)."""
        return self._broad_gauss_strain_g

    @broad_gauss_strain_g.setter
    def broad_gauss_strain_g(self, value: float) -> None:
        """Set Gaussian isotropic strain broadening, additive to σ₁ (μs/Å)."""
        self._broad_gauss_strain_g.value = value


class TofLorentzianBroadeningMixin:
    """TOF Lorentzian broadening parameters γ₀, γ₁, γ₂."""

    def __init__(self) -> None:
        """Initialize the TOF Lorentzian broadening parameters."""
        super().__init__()

        self._broad_lorentz_gamma_0 = Parameter(
            name='broad_lorentz_gamma_0',
            description='Lorentzian broadening (microstrain effects)',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_gamma_0'],
                cif_names=['_easydiffraction_peak.broad_lorentz_gamma_0'],
            ),
        )
        self._broad_lorentz_gamma_1 = Parameter(
            name='broad_lorentz_gamma_1',
            description='Lorentzian broadening (dependent on d-spacing)',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_gamma_1'],
                cif_names=['_easydiffraction_peak.broad_lorentz_gamma_1'],
            ),
        )
        self._broad_lorentz_gamma_2 = Parameter(
            name='broad_lorentz_gamma_2',
            description='Lorentzian broadening (instrument-dependent term)',
            units='microseconds_squared_per_angstrom_squared',
            display_handler=DisplayHandler(
                display_units='μs²/Å²',
                latex_units=r'$\mu\mathrm{s}^2/\mathrm{\AA}^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_gamma_2'],
                cif_names=['_easydiffraction_peak.broad_lorentz_gamma_2'],
            ),
        )
        self._broad_lorentz_size_l = Parameter(
            name='broad_lorentz_size_l',
            description='Lorentzian isotropic size broadening (adds to gamma2)',
            units='microseconds_squared_per_angstrom_squared',
            display_handler=DisplayHandler(
                display_units='μs²/Å²',
                latex_units=r'$\mu\mathrm{s}^2/\mathrm{\AA}^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_size_l'],
                cif_names=['_easydiffraction_peak.broad_lorentz_size_l'],
            ),
        )
        self._broad_lorentz_strain_l = Parameter(
            name='broad_lorentz_strain_l',
            description='Lorentzian isotropic strain broadening (adds to gamma1)',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_strain_l'],
                cif_names=['_easydiffraction_peak.broad_lorentz_strain_l'],
            ),
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
        """Set Lorentzian broadening (microstrain effects) (μs)."""
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
        """
        Set Lorentzian broadening (dependent on d-spacing) (μs/Å).
        """
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
        """
        Set Lorentzian broadening (instrument-dependent) (μs²/Å²).
        """
        self._broad_lorentz_gamma_2.value = value

    @property
    def broad_lorentz_size_l(self) -> Parameter:
        """Lorentzian isotropic size broadening, additive to γ₂ (μs²/Å²)."""
        return self._broad_lorentz_size_l

    @broad_lorentz_size_l.setter
    def broad_lorentz_size_l(self, value: float) -> None:
        """Set Lorentzian isotropic size broadening, additive to γ₂ (μs²/Å²)."""
        self._broad_lorentz_size_l.value = value

    @property
    def broad_lorentz_strain_l(self) -> Parameter:
        """Lorentzian isotropic strain broadening, additive to γ₁ (μs/Å)."""
        return self._broad_lorentz_strain_l

    @broad_lorentz_strain_l.setter
    def broad_lorentz_strain_l(self, value: float) -> None:
        """Set Lorentzian isotropic strain broadening, additive to γ₁ (μs/Å)."""
        self._broad_lorentz_strain_l.value = value


class TofBackToBackExponentialMixin:
    """
    Back-to-back exponential (BBE) rise and decay parameters.

    Rise parameters α₀, α₁ and decay parameters β₀, β₁ follow Von
    Dreele, Jorgensen & Windsor, J. Appl. Cryst. 15, 581 (1982).

    The rise α₁ and decay β₀ default nonzero so the profile is
    normalisable and the peak is visible; refine per instrument.
    """

    def __init__(self) -> None:
        """Initialize the back-to-back exponential parameters."""
        super().__init__()

        self._rise_alpha_0 = Parameter(
            name='rise_alpha_0',
            description='Back-to-back exponential rise α₀',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.rise_alpha_0'],
                cif_names=['_easydiffraction_peak.rise_alpha_0'],
            ),
        )
        self._rise_alpha_1 = Parameter(
            name='rise_alpha_1',
            description='Back-to-back exponential rise α₁',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.2,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.rise_alpha_1'],
                cif_names=['_easydiffraction_peak.rise_alpha_1'],
            ),
        )
        self._decay_beta_0 = Parameter(
            name='decay_beta_0',
            description='Back-to-back exponential decay β₀',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.04,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.decay_beta_0'],
                cif_names=['_easydiffraction_peak.decay_beta_0'],
            ),
        )
        self._decay_beta_1 = Parameter(
            name='decay_beta_1',
            description='Back-to-back exponential decay β₁',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.decay_beta_1'],
                cif_names=['_easydiffraction_peak.decay_beta_1'],
            ),
        )

    @property
    def rise_alpha_0(self) -> Parameter:
        """
        Back-to-back exponential rise α₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._rise_alpha_0

    @rise_alpha_0.setter
    def rise_alpha_0(self, value: float) -> None:
        """Set the back-to-back exponential rise α₀ (μs)."""
        self._rise_alpha_0.value = value

    @property
    def rise_alpha_1(self) -> Parameter:
        """
        Back-to-back exponential rise α₁ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._rise_alpha_1

    @rise_alpha_1.setter
    def rise_alpha_1(self, value: float) -> None:
        """Set the back-to-back exponential rise α₁ (μs/Å)."""
        self._rise_alpha_1.value = value

    @property
    def decay_beta_0(self) -> Parameter:
        """
        Back-to-back exponential decay β₀ (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._decay_beta_0

    @decay_beta_0.setter
    def decay_beta_0(self, value: float) -> None:
        """Set the back-to-back exponential decay β₀ (μs)."""
        self._decay_beta_0.value = value

    @property
    def decay_beta_1(self) -> Parameter:
        """
        Back-to-back exponential decay β₁ (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._decay_beta_1

    @decay_beta_1.setter
    def decay_beta_1(self, value: float) -> None:
        """Set the back-to-back exponential decay β₁ (μs/Å)."""
        self._decay_beta_1.value = value


class TofDoubleExponentialMixin:
    """
    Double back-to-back exponential parameters for Z-Rietveld type0m.

    Rise parameters α₁, α₂, decay parameters β₀₀, β₀₁, β₁₀ for two
    exponential regimes, and switching-function parameters r₀₁, r₀₂,
    r₀₃.

    α₁, β₀₀, β₁₀ and r₀₁ default nonzero so both regimes stay finite and
    blended; an all-zero set produces NaN. Refine per instrument.
    """

    def __init__(self) -> None:
        """Initialize the double back-to-back exponential parameters."""
        super().__init__()

        self._dexp_rise_alpha_1 = Parameter(
            name='dexp_rise_alpha_1',
            description='Double-exp rise parameter α₁',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.25,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_rise_alpha_1'],
                cif_names=['_easydiffraction_peak.dexp_rise_alpha_1'],
            ),
        )
        self._dexp_rise_alpha_2 = Parameter(
            name='dexp_rise_alpha_2',
            description='Double-exp rise parameter α₂',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_rise_alpha_2'],
                cif_names=['_easydiffraction_peak.dexp_rise_alpha_2'],
            ),
        )
        self._dexp_decay_beta_00 = Parameter(
            name='dexp_decay_beta_00',
            description='Double-exp first-regime decay β₀₀',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=4.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_decay_beta_00'],
                cif_names=['_easydiffraction_peak.dexp_decay_beta_00'],
            ),
        )
        self._dexp_decay_beta_01 = Parameter(
            name='dexp_decay_beta_01',
            description='Double-exp first-regime decay β₀₁',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_units='μs/Å',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_decay_beta_01'],
                cif_names=['_easydiffraction_peak.dexp_decay_beta_01'],
            ),
        )
        self._dexp_decay_beta_10 = Parameter(
            name='dexp_decay_beta_10',
            description='Double-exp second-regime decay β₁₀',
            units='microseconds',
            display_handler=DisplayHandler(
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=2.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_decay_beta_10'],
                cif_names=['_easydiffraction_peak.dexp_decay_beta_10'],
            ),
        )
        self._dexp_switch_r_01 = Parameter(
            name='dexp_switch_r_01',
            description='Double-exp switching function r₀₁',
            units='none',
            value_spec=AttributeSpec(
                default=0.5,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_switch_r_01'],
                cif_names=['_easydiffraction_peak.dexp_switch_r_01'],
            ),
        )
        self._dexp_switch_r_02 = Parameter(
            name='dexp_switch_r_02',
            description='Double-exp switching function r₀₂',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_switch_r_02'],
                cif_names=['_easydiffraction_peak.dexp_switch_r_02'],
            ),
        )
        self._dexp_switch_r_03 = Parameter(
            name='dexp_switch_r_03',
            description='Double-exp switching function r₀₃',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.dexp_switch_r_03'],
                cif_names=['_easydiffraction_peak.dexp_switch_r_03'],
            ),
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
        """Set the double-exp rise parameter α₁ (μs)."""
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
        """Set the double-exp rise parameter α₂ (μs/Å)."""
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
        """Set the double-exp first-regime decay β₀₀ (μs)."""
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
        """Set the double-exp first-regime decay β₀₁ (μs/Å)."""
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
        """Set the double-exp second-regime decay β₁₀ (μs)."""
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
        """Set the double-exp switching function r₀₁."""
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
        """Set the double-exp switching function r₀₂."""
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
        """Set the double-exp switching function r₀₃."""
        self._dexp_switch_r_03.value = value
