# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength (CWL) peak-profile mixins.

This module provides mixins that add broadening and asymmetry parameters
for constant-wavelength powder diffraction peak profiles. They are
composed into concrete peak classes elsewhere.
"""

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class CwlBroadeningMixin:
    """Mixin that adds CWL Gaussian and Lorentz broadening
    parameters.
    """

    # TODO: Rename to cwl. Check other mixins for naming consistency.
    def _add_constant_wavelength_broadening(self) -> None:
        """Create CWL broadening parameters and attach them to the
        class.

        Defines Gaussian (U, V, W) and Lorentz (X, Y) terms
        often used in the TCH formulation. Values are stored as
        ``Parameter`` objects.
        """
        self._broad_gauss_u: Parameter = Parameter(
            name='broad_gauss_u',
            description='Gaussian broadening coefficient (dependent on '
            'sample size and instrument resolution)',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(names=['_peak.broad_gauss_u']),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            value_spec=AttributeSpec(
                default=-0.01,
                validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(names=['_peak.broad_gauss_v']),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(names=['_peak.broad_gauss_w']),
        )
        self._broad_lorentz_x: Parameter = Parameter(
            name='broad_lorentz_x',
            description='Lorentzian broadening coefficient (dependent on sample strain effects)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_peak.broad_lorentz_x']),
        )
        self._broad_lorentz_y: Parameter = Parameter(
            name='broad_lorentz_y',
            description='Lorentzian broadening coefficient (dependent on '
            'microstructural defects and strain)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_peak.broad_lorentz_y']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def broad_gauss_u(self) -> Parameter:
        return self._broad_gauss_u

    @broad_gauss_u.setter
    def broad_gauss_u(self, value) -> None:
        self._broad_gauss_u.value = value

    @property
    def broad_gauss_v(self) -> Parameter:
        return self._broad_gauss_v

    @broad_gauss_v.setter
    def broad_gauss_v(self, value) -> None:
        self._broad_gauss_v.value = value

    @property
    def broad_gauss_w(self) -> Parameter:
        return self._broad_gauss_w

    @broad_gauss_w.setter
    def broad_gauss_w(self, value) -> None:
        self._broad_gauss_w.value = value

    @property
    def broad_lorentz_x(self) -> Parameter:
        return self._broad_lorentz_x

    @broad_lorentz_x.setter
    def broad_lorentz_x(self, value) -> None:
        self._broad_lorentz_x.value = value

    @property
    def broad_lorentz_y(self) -> Parameter:
        return self._broad_lorentz_y

    @broad_lorentz_y.setter
    def broad_lorentz_y(self, value) -> None:
        self._broad_lorentz_y.value = value


class EmpiricalAsymmetryMixin:
    """Mixin that adds empirical CWL peak asymmetry parameters."""

    def _add_empirical_asymmetry(self) -> None:
        """Create empirical asymmetry parameters p1..p4."""
        self._asym_empir_1: Parameter = Parameter(
            name='asym_empir_1',
            description='Empirical asymmetry coefficient p1',
            value_spec=AttributeSpec(
                default=0.1,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_empir_1']),
        )
        self._asym_empir_2: Parameter = Parameter(
            name='asym_empir_2',
            description='Empirical asymmetry coefficient p2',
            value_spec=AttributeSpec(
                default=0.2,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_empir_2']),
        )
        self._asym_empir_3: Parameter = Parameter(
            name='asym_empir_3',
            description='Empirical asymmetry coefficient p3',
            value_spec=AttributeSpec(
                default=0.3,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_empir_3']),
        )
        self._asym_empir_4: Parameter = Parameter(
            name='asym_empir_4',
            description='Empirical asymmetry coefficient p4',
            value_spec=AttributeSpec(
                default=0.4,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_empir_4']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def asym_empir_1(self) -> Parameter:
        return self._asym_empir_1

    @asym_empir_1.setter
    def asym_empir_1(self, value) -> None:
        self._asym_empir_1.value = value

    @property
    def asym_empir_2(self) -> Parameter:
        return self._asym_empir_2

    @asym_empir_2.setter
    def asym_empir_2(self, value) -> None:
        self._asym_empir_2.value = value

    @property
    def asym_empir_3(self) -> Parameter:
        return self._asym_empir_3

    @asym_empir_3.setter
    def asym_empir_3(self, value) -> None:
        self._asym_empir_3.value = value

    @property
    def asym_empir_4(self) -> Parameter:
        return self._asym_empir_4

    @asym_empir_4.setter
    def asym_empir_4(self, value) -> None:
        self._asym_empir_4.value = value


class FcjAsymmetryMixin:
    """Mixin that adds Finger–Cox–Jephcoat (FCJ) asymmetry params."""

    def _add_fcj_asymmetry(self) -> None:
        """Create FCJ asymmetry parameters."""
        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='Finger-Cox-Jephcoat asymmetry parameter 1',
            value_spec=AttributeSpec(
                default=0.01,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_fcj_1']),
        )
        self._asym_fcj_2: Parameter = Parameter(
            name='asym_fcj_2',
            description='Finger-Cox-Jephcoat asymmetry parameter 2',
            value_spec=AttributeSpec(
                default=0.02,
                validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(names=['_peak.asym_fcj_2']),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def asym_fcj_1(self) -> Parameter:
        return self._asym_fcj_1

    @asym_fcj_1.setter
    def asym_fcj_1(self, value) -> None:
        self._asym_fcj_1.value = value

    @property
    def asym_fcj_2(self) -> Parameter:
        return self._asym_fcj_2

    @asym_fcj_2.setter
    def asym_fcj_2(self, value) -> None:
        self._asym_fcj_2.value = value
