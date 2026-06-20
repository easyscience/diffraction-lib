# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Constant-wavelength (CWL) peak-profile component classes.

This module provides classes that add broadening and asymmetry
parameters. They are composed into concrete peak classes elsewhere via
multiple inheritance.
"""

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import TagSpec


class CwlBroadeningMixin:
    """CWL Gaussian and Lorentz broadening parameters."""

    def __init__(self) -> None:
        """Initialize the CWL broadening parameters."""
        super().__init__()

        self._broad_gauss_u: Parameter = Parameter(
            name='broad_gauss_u',
            description='Gaussian broadening from sample size and resolution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='U',
                display_units='deg²',
                latex_name=r'$U$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_u'],
                cif_names=['_easydiffraction_peak.broad_gauss_u'],
            ),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening instrumental contribution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='V',
                display_units='deg²',
                latex_name=r'$V$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=-0.01,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_v'],
                cif_names=['_easydiffraction_peak.broad_gauss_v'],
            ),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening instrumental contribution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='W',
                display_units='deg²',
                latex_name=r'$W$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_gauss_w'],
                cif_names=['_easydiffraction_peak.broad_gauss_w'],
            ),
        )
        self._broad_lorentz_x: Parameter = Parameter(
            name='broad_lorentz_x',
            description='Lorentzian broadening from sample strain effects',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='X',
                display_units='deg',
                latex_name=r'$X$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_x'],
                cif_names=['_easydiffraction_peak.broad_lorentz_x'],
            ),
        )
        self._broad_lorentz_y: Parameter = Parameter(
            name='broad_lorentz_y',
            description='Lorentzian broadening from microstructural defects',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='Y',
                display_units='deg',
                latex_name=r'$Y$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.broad_lorentz_y'],
                cif_names=['_easydiffraction_peak.broad_lorentz_y'],
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
                default=80.0,
                validator=RangeValidator(gt=0.0),
            ),
            tags=TagSpec(
                edi_names=['_peak.cutoff_fwhm'],
                cif_names=['_easydiffraction_peak.cutoff_fwhm'],
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

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
    def broad_gauss_u(self) -> Parameter:
        """
        Gaussian broadening from sample size and resolution (deg²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_u

    @broad_gauss_u.setter
    def broad_gauss_u(self, value: float) -> None:
        """Set Gaussian broadening from size/resolution (deg²)."""
        self._broad_gauss_u.value = value

    @property
    def broad_gauss_v(self) -> Parameter:
        """
        Gaussian broadening instrumental contribution (deg²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_v

    @broad_gauss_v.setter
    def broad_gauss_v(self, value: float) -> None:
        """Set Gaussian broadening instrumental contribution (deg²)."""
        self._broad_gauss_v.value = value

    @property
    def broad_gauss_w(self) -> Parameter:
        """
        Gaussian broadening instrumental contribution (deg²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_w

    @broad_gauss_w.setter
    def broad_gauss_w(self, value: float) -> None:
        """Set Gaussian broadening instrumental contribution (deg²)."""
        self._broad_gauss_w.value = value

    @property
    def broad_lorentz_x(self) -> Parameter:
        """
        Lorentzian broadening (sample strain effects) (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_lorentz_x

    @broad_lorentz_x.setter
    def broad_lorentz_x(self, value: float) -> None:
        """Set Lorentzian broadening from strain effects (deg)."""
        self._broad_lorentz_x.value = value

    @property
    def broad_lorentz_y(self) -> Parameter:
        """
        Lorentzian broadening from microstructural defects (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_lorentz_y

    @broad_lorentz_y.setter
    def broad_lorentz_y(self, value: float) -> None:
        """Set Lorentzian broadening from defects (deg)."""
        self._broad_lorentz_y.value = value


class BerarBaldinozziAsymmetryMixin:
    """Berar-Baldinozzi empirical CWL peak asymmetry parameters."""

    def __init__(self) -> None:
        """Initialize the Berar-Baldinozzi peak asymmetry parameters."""
        super().__init__()

        self._asym_beba_a0: Parameter = Parameter(
            name='asym_beba_a0',
            description='Berar-Baldinozzi asymmetry coefficient A0 (Fa/tan theta)',
            units='none',
            display_handler=DisplayHandler(
                display_name='A₀',
                latex_name=r'$A_0$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_beba_a0'],
                cif_names=['_easydiffraction_peak.asym_beba_a0'],
            ),
        )
        self._asym_beba_b0: Parameter = Parameter(
            name='asym_beba_b0',
            description='Berar-Baldinozzi asymmetry coefficient B0 (Fb/tan theta)',
            units='none',
            display_handler=DisplayHandler(
                display_name='B₀',
                latex_name=r'$B_0$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_beba_b0'],
                cif_names=['_easydiffraction_peak.asym_beba_b0'],
            ),
        )
        self._asym_beba_a1: Parameter = Parameter(
            name='asym_beba_a1',
            description='Berar-Baldinozzi asymmetry coefficient A1 (Fa/tan 2theta)',
            units='none',
            display_handler=DisplayHandler(
                display_name='A₁',
                latex_name=r'$A_1$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_beba_a1'],
                cif_names=['_easydiffraction_peak.asym_beba_a1'],
            ),
        )
        self._asym_beba_b1: Parameter = Parameter(
            name='asym_beba_b1',
            description='Berar-Baldinozzi asymmetry coefficient B1 (Fb/tan 2theta)',
            units='none',
            display_handler=DisplayHandler(
                display_name='B₁',
                latex_name=r'$B_1$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_beba_b1'],
                cif_names=['_easydiffraction_peak.asym_beba_b1'],
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def asym_beba_a0(self) -> Parameter:
        """
        Berar-Baldinozzi asymmetry coefficient A0 (Fa/tan theta).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_beba_a0

    @asym_beba_a0.setter
    def asym_beba_a0(self, value: float) -> None:
        """Set Berar-Baldinozzi asymmetry coefficient A0."""
        self._asym_beba_a0.value = value

    @property
    def asym_beba_b0(self) -> Parameter:
        """
        Berar-Baldinozzi asymmetry coefficient B0 (Fb/tan theta).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_beba_b0

    @asym_beba_b0.setter
    def asym_beba_b0(self, value: float) -> None:
        """Set Berar-Baldinozzi asymmetry coefficient B0."""
        self._asym_beba_b0.value = value

    @property
    def asym_beba_a1(self) -> Parameter:
        """
        Berar-Baldinozzi asymmetry coefficient A1 (Fa/tan 2theta).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_beba_a1

    @asym_beba_a1.setter
    def asym_beba_a1(self, value: float) -> None:
        """Set Berar-Baldinozzi asymmetry coefficient A1."""
        self._asym_beba_a1.value = value

    @property
    def asym_beba_b1(self) -> Parameter:
        """
        Berar-Baldinozzi asymmetry coefficient B1 (Fb/tan 2theta).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_beba_b1

    @asym_beba_b1.setter
    def asym_beba_b1(self, value: float) -> None:
        """Set Berar-Baldinozzi asymmetry coefficient B1."""
        self._asym_beba_b1.value = value


class FcjAsymmetryMixin:
    """Finger-Cox-Jephcoat (FCJ) asymmetry parameters."""

    def __init__(self) -> None:
        """Initialize the Finger-Cox-Jephcoat asymmetry parameters."""
        super().__init__()

        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='Finger-Cox-Jephcoat asymmetry parameter 1',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_fcj_1'], cif_names=['_easydiffraction_peak.asym_fcj_1']
            ),
        )
        self._asym_fcj_2: Parameter = Parameter(
            name='asym_fcj_2',
            description='Finger-Cox-Jephcoat asymmetry parameter 2',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_peak.asym_fcj_2'], cif_names=['_easydiffraction_peak.asym_fcj_2']
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def asym_fcj_1(self) -> Parameter:
        """
        Finger-Cox-Jephcoat asymmetry parameter 1.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_fcj_1

    @asym_fcj_1.setter
    def asym_fcj_1(self, value: float) -> None:
        """Set the Finger-Cox-Jephcoat asymmetry parameter 1."""
        self._asym_fcj_1.value = value

    @property
    def asym_fcj_2(self) -> Parameter:
        """
        Finger-Cox-Jephcoat asymmetry parameter 2.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_fcj_2

    @asym_fcj_2.setter
    def asym_fcj_2(self, value: float) -> None:
        """Set the Finger-Cox-Jephcoat asymmetry parameter 2."""
        self._asym_fcj_2.value = value
