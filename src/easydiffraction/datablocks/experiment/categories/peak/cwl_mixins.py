# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Constant-wavelength (CWL) peak-profile component classes.

This module provides classes that add broadening and asymmetry
parameters. They are composed into concrete peak classes elsewhere via
multiple inheritance.
"""

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
            description='Gaussian broadening (sample size and instrument resolution)',
            units='deg²',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_gauss_u']),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening (instrumental broadening contribution)',
            units='deg²',
            value_spec=AttributeSpec(
                default=-0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_gauss_v']),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening (instrumental broadening contribution)',
            units='deg²',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_gauss_w']),
        )
        self._broad_lorentz_x: Parameter = Parameter(
            name='broad_lorentz_x',
            description='Lorentzian broadening (sample strain effects)',
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_lorentz_x']),
        )
        self._broad_lorentz_y: Parameter = Parameter(
            name='broad_lorentz_y',
            description='Lorentzian broadening (microstructural defects and strain)',
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.broad_lorentz_y']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def broad_gauss_u(self) -> Parameter:
        """
        Gaussian broadening (sample size and instrument resolution)
        (deg²).

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
        Gaussian broadening (instrumental broadening contribution)
        (deg²).

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
        Gaussian broadening (instrumental broadening contribution)
        (deg²).

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
        Lorentzian broadening (microstructural defects and strain)
        (deg).

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
            units='',
            value_spec=AttributeSpec(
                default=0.1,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_empir_1']),
        )
        self._asym_empir_2: Parameter = Parameter(
            name='asym_empir_2',
            description='Empirical asymmetry coefficient p2',
            units='',
            value_spec=AttributeSpec(
                default=0.2,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_empir_2']),
        )
        self._asym_empir_3: Parameter = Parameter(
            name='asym_empir_3',
            description='Empirical asymmetry coefficient p3',
            units='',
            value_spec=AttributeSpec(
                default=0.3,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_empir_3']),
        )
        self._asym_empir_4: Parameter = Parameter(
            name='asym_empir_4',
            description='Empirical asymmetry coefficient p4',
            units='',
            value_spec=AttributeSpec(
                default=0.4,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_empir_4']),
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
    """Finger–Cox–Jephcoat (FCJ) asymmetry parameters."""

    def __init__(self) -> None:
        super().__init__()

        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='Finger-Cox-Jephcoat asymmetry parameter 1',
            units='',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_fcj_1']),
        )
        self._asym_fcj_2: Parameter = Parameter(
            name='asym_fcj_2',
            description='Finger-Cox-Jephcoat asymmetry parameter 2',
            units='',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_peak.asym_fcj_2']),
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
