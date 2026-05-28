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
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler


class CwlBroadeningMixin:
    """CWL Gaussian and Lorentz broadening parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._broad_gauss_u: Parameter = Parameter(
            name='broad_gauss_u',
            description='Gaussian broadening from sample size and resolution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='U',
                display_units='deg^2',
                latex_name=r'$U$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.broad_gauss_u'],
                iucr_name='_easydiffraction_peak.broad_gauss_u',
            ),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening instrumental contribution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='V',
                display_units='deg^2',
                latex_name=r'$V$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=-0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.broad_gauss_v'],
                iucr_name='_easydiffraction_peak.broad_gauss_v',
            ),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening instrumental contribution',
            units='degrees_squared',
            display_handler=DisplayHandler(
                display_name='W',
                display_units='deg^2',
                latex_name=r'$W$',
                latex_units=r'\mathrm{deg}^2',
            ),
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.broad_gauss_w'],
                iucr_name='_easydiffraction_peak.broad_gauss_w',
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
            cif_handler=CifHandler(
                names=['_peak.broad_lorentz_x'],
                iucr_name='_easydiffraction_peak.broad_lorentz_x',
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
            cif_handler=CifHandler(
                names=['_peak.broad_lorentz_y'],
                iucr_name='_easydiffraction_peak.broad_lorentz_y',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def broad_gauss_u(self) -> Parameter:
        """
        Gaussian broadening from sample size and resolution (deg^2).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_u

    @broad_gauss_u.setter
    def broad_gauss_u(self, value: float) -> None:
        self._broad_gauss_u.value = value

    @property
    def broad_gauss_v(self) -> Parameter:
        """
        Gaussian broadening instrumental contribution (deg^2).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_v

    @broad_gauss_v.setter
    def broad_gauss_v(self, value: float) -> None:
        self._broad_gauss_v.value = value

    @property
    def broad_gauss_w(self) -> Parameter:
        """
        Gaussian broadening instrumental contribution (deg^2).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._broad_gauss_w

    @broad_gauss_w.setter
    def broad_gauss_w(self, value: float) -> None:
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
        self._broad_lorentz_y.value = value


class EmpiricalAsymmetryMixin:
    """Empirical CWL peak asymmetry parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._asym_empir_1: Parameter = Parameter(
            name='asym_empir_1',
            description='Empirical asymmetry coefficient p1',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.asym_empir_1'],
                iucr_name='_easydiffraction_peak.asym_empir_1',
            ),
        )
        self._asym_empir_2: Parameter = Parameter(
            name='asym_empir_2',
            description='Empirical asymmetry coefficient p2',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.asym_empir_2'],
                iucr_name='_easydiffraction_peak.asym_empir_2',
            ),
        )
        self._asym_empir_3: Parameter = Parameter(
            name='asym_empir_3',
            description='Empirical asymmetry coefficient p3',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.asym_empir_3'],
                iucr_name='_easydiffraction_peak.asym_empir_3',
            ),
        )
        self._asym_empir_4: Parameter = Parameter(
            name='asym_empir_4',
            description='Empirical asymmetry coefficient p4',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.asym_empir_4'],
                iucr_name='_easydiffraction_peak.asym_empir_4',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def asym_empir_1(self) -> Parameter:
        """
        Empirical asymmetry coefficient p1.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_empir_1

    @asym_empir_1.setter
    def asym_empir_1(self, value: float) -> None:
        self._asym_empir_1.value = value

    @property
    def asym_empir_2(self) -> Parameter:
        """
        Empirical asymmetry coefficient p2.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_empir_2

    @asym_empir_2.setter
    def asym_empir_2(self, value: float) -> None:
        self._asym_empir_2.value = value

    @property
    def asym_empir_3(self) -> Parameter:
        """
        Empirical asymmetry coefficient p3.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_empir_3

    @asym_empir_3.setter
    def asym_empir_3(self, value: float) -> None:
        self._asym_empir_3.value = value

    @property
    def asym_empir_4(self) -> Parameter:
        """
        Empirical asymmetry coefficient p4.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._asym_empir_4

    @asym_empir_4.setter
    def asym_empir_4(self, value: float) -> None:
        self._asym_empir_4.value = value


class FcjAsymmetryMixin:
    """Finger-Cox-Jephcoat (FCJ) asymmetry parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='Finger-Cox-Jephcoat asymmetry parameter 1',
            units='none',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_peak.asym_fcj_1'],
                iucr_name='_easydiffraction_peak.asym_fcj_1',
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
            cif_handler=CifHandler(
                names=['_peak.asym_fcj_2'],
                iucr_name='_easydiffraction_peak.asym_fcj_2',
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
        self._asym_fcj_2.value = value
