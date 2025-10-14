# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class CwlBroadeningMixin:
    def _add_constant_wavelength_broadening(self) -> None:
        self._broad_gauss_u: Parameter = Parameter(
            name='broad_gauss_u',
            description='Gaussian broadening coefficient (dependent on '
            'sample size and instrument resolution)',
            value_spec=AttributeSpec(
                value=0.01,
                type_=DataTypes.NUMERIC,
                default=0.01,
                content_validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_u',
                ]
            ),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            value_spec=AttributeSpec(
                value=-0.01,
                type_=DataTypes.NUMERIC,
                default=-0.01,
                content_validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_v',
                ]
            ),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            value_spec=AttributeSpec(
                value=0.02,
                type_=DataTypes.NUMERIC,
                default=0.02,
                content_validator=RangeValidator(),
            ),
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_w',
                ]
            ),
        )
        self._broad_lorentz_x: Parameter = Parameter(
            name='broad_lorentz_x',
            description='Lorentzian broadening coefficient (dependent on sample strain effects)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_lorentz_x',
                ]
            ),
        )
        self._broad_lorentz_y: Parameter = Parameter(
            name='broad_lorentz_y',
            description='Lorentzian broadening coefficient (dependent on '
            'microstructural defects and strain)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_lorentz_y',
                ]
            ),
        )

    @property
    def broad_gauss_u(self) -> Parameter:
        return self._broad_gauss_u

    @broad_gauss_u.setter
    def broad_gauss_u(self, value: float) -> None:
        self._broad_gauss_u.value = value

    @property
    def broad_gauss_v(self) -> Parameter:
        return self._broad_gauss_v

    @broad_gauss_v.setter
    def broad_gauss_v(self, value: float) -> None:
        self._broad_gauss_v.value = value

    @property
    def broad_gauss_w(self) -> Parameter:
        return self._broad_gauss_w

    @broad_gauss_w.setter
    def broad_gauss_w(self, value: float) -> None:
        self._broad_gauss_w.value = value

    @property
    def broad_lorentz_x(self) -> Parameter:
        return self._broad_lorentz_x

    @broad_lorentz_x.setter
    def broad_lorentz_x(self, value: float) -> None:
        self._broad_lorentz_x.value = value

    @property
    def broad_lorentz_y(self) -> Parameter:
        return self._broad_lorentz_y

    @broad_lorentz_y.setter
    def broad_lorentz_y(self, value: float) -> None:
        self._broad_lorentz_y.value = value


class EmpiricalAsymmetryMixin:
    def _add_empirical_asymmetry(self) -> None:
        self._asym_empir_1: Parameter = Parameter(
            name='asym_empir_1',
            description='Empirical asymmetry coefficient p1',
            value_spec=AttributeSpec(
                value=0.1,
                type_=DataTypes.NUMERIC,
                default=0.1,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_1',
                ]
            ),
        )
        self._asym_empir_2: Parameter = Parameter(
            name='asym_empir_2',
            description='Empirical asymmetry coefficient p2',
            value_spec=AttributeSpec(
                value=0.2,
                type_=DataTypes.NUMERIC,
                default=0.2,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_2',
                ]
            ),
        )
        self._asym_empir_3: Parameter = Parameter(
            name='asym_empir_3',
            description='Empirical asymmetry coefficient p3',
            value_spec=AttributeSpec(
                value=0.3,
                type_=DataTypes.NUMERIC,
                default=0.3,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_3',
                ]
            ),
        )
        self._asym_empir_4: Parameter = Parameter(
            name='asym_empir_4',
            description='Empirical asymmetry coefficient p4',
            value_spec=AttributeSpec(
                value=0.4,
                type_=DataTypes.NUMERIC,
                default=0.4,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_4',
                ]
            ),
        )

    @property
    def asym_empir_1(self) -> Parameter:
        return self._asym_empir_1

    @asym_empir_1.setter
    def asym_empir_1(self, value: float) -> None:
        self._asym_empir_1.value = value

    @property
    def asym_empir_2(self) -> Parameter:
        return self._asym_empir_2

    @asym_empir_2.setter
    def asym_empir_2(self, value: float) -> None:
        self._asym_empir_2.value = value

    @property
    def asym_empir_3(self) -> Parameter:
        return self._asym_empir_3

    @asym_empir_3.setter
    def asym_empir_3(self, value: float) -> None:
        self._asym_empir_3.value = value

    @property
    def asym_empir_4(self) -> Parameter:
        return self._asym_empir_4

    @asym_empir_4.setter
    def asym_empir_4(self, value: float) -> None:
        self._asym_empir_4.value = value


class FcjAsymmetryMixin:
    def _add_fcj_asymmetry(self) -> None:
        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='Finger-Cox-Jephcoat asymmetry parameter 1',
            value_spec=AttributeSpec(
                value=0.01,
                type_=DataTypes.NUMERIC,
                default=0.01,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_fcj_1',
                ]
            ),
        )
        self._asym_fcj_2: Parameter = Parameter(
            name='asym_fcj_2',
            description='Finger-Cox-Jephcoat asymmetry parameter 2',
            value_spec=AttributeSpec(
                value=0.02,
                type_=DataTypes.NUMERIC,
                default=0.02,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_fcj_2',
                ]
            ),
        )

    @property
    def asym_fcj_1(self) -> Parameter:
        return self._asym_fcj_1

    @asym_fcj_1.setter
    def asym_fcj_1(self, value: float) -> None:
        self._asym_fcj_1.value = value

    @property
    def asym_fcj_2(self) -> Parameter:
        return self._asym_fcj_2

    @asym_fcj_2.setter
    def asym_fcj_2(self, value: float) -> None:
        self._asym_fcj_2.value = value
