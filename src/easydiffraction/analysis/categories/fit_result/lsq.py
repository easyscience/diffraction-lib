# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Least-squares fit-result category."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.base import FitResultBase
from easydiffraction.analysis.categories.fit_result.base import _result_display_handler
from easydiffraction.analysis.categories.fit_result.factory import FitResultFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


def _fit_result_cif_handler(name: str, cif_name: str | None = None) -> CifHandler:
    """
    Return an Edi-first handler for one fit-result descriptor.
    """
    names = [f'_fit_result.{name}']
    if cif_name is None:
        return CifHandler(names=names)
    return CifHandler(
        names=names,
        import_names=[f'_fit_result.{cif_name}'],
    )


class _LeastSquaresCoreProperties:
    """Core deterministic least-squares result descriptors."""

    @property
    def objective_name(self) -> StringDescriptor:
        """
        Objective function name for the persisted deterministic fit.
        """
        return self._objective_name

    def _set_objective_name(self, value: str | None) -> None:
        """Set the persisted objective function name."""
        self._objective_name.value = value

    @property
    def objective_value(self) -> NumericDescriptor:
        """Objective value for the persisted deterministic fit."""
        return self._objective_value

    def _set_objective_value(self, value: float | None) -> None:
        """Set the persisted objective value."""
        self._objective_value.value = value

    @property
    def n_data_points(self) -> NumericDescriptor:
        """
        Number of data points used in the persisted deterministic fit.
        """
        return self._n_data_points

    def _set_n_data_points(self, value: float | None) -> None:
        """Set the persisted number of data points."""
        self._n_data_points.value = value

    @property
    def n_parameters(self) -> NumericDescriptor:
        """Number of parameters in the persisted deterministic fit."""
        return self._n_parameters

    def _set_n_parameters(self, value: float | None) -> None:
        """Set the persisted number of parameters."""
        self._n_parameters.value = value

    @property
    def n_free_parameters(self) -> NumericDescriptor:
        """
        Number of free parameters in the persisted deterministic fit.
        """
        return self._n_free_parameters

    def _set_n_free_parameters(self, value: float | None) -> None:
        """Set the persisted number of free parameters."""
        self._n_free_parameters.value = value

    @property
    def degrees_of_freedom(self) -> NumericDescriptor:
        """Degrees of freedom for the persisted deterministic fit."""
        return self._degrees_of_freedom

    def _set_degrees_of_freedom(self, value: float | None) -> None:
        """Set the persisted degrees of freedom."""
        self._degrees_of_freedom.value = value

    @property
    def covariance_available(self) -> BoolDescriptor:
        """Whether deterministic covariance was available."""
        return self._covariance_available

    def _set_covariance_available(self, *, value: bool | None) -> None:
        """Set whether deterministic covariance was available."""
        self._covariance_available.value = value

    @property
    def correlation_available(self) -> BoolDescriptor:
        """Whether deterministic correlations were available."""
        return self._correlation_available

    def _set_correlation_available(self, *, value: bool | None) -> None:
        """Set whether deterministic correlations were available."""
        self._correlation_available.value = value

    @property
    def exit_reason(self) -> StringDescriptor:
        """Backend exit reason for the persisted deterministic fit."""
        return self._exit_reason

    def _set_exit_reason(self, value: str | None) -> None:
        """Set the persisted backend exit reason."""
        self._exit_reason.value = value


class _LeastSquaresReflectionProperties:
    """Single-crystal reflection aggregate result descriptors."""

    @property
    def r_factor_all(self) -> NumericDescriptor:
        """R factor for all observed data."""
        return self._r_factor_all

    def _set_r_factor_all(self, value: float | None) -> None:
        """Set the R factor for all observed data."""
        self._r_factor_all.value = value

    @property
    def wr_factor_all(self) -> NumericDescriptor:
        """Weighted R factor for all observed data."""
        return self._wr_factor_all

    def _set_wr_factor_all(self, value: float | None) -> None:
        """Set the weighted R factor for all observed data."""
        self._wr_factor_all.value = value

    @property
    def r_factor_gt(self) -> NumericDescriptor:
        """R factor for observations above the threshold."""
        return self._r_factor_gt

    def _set_r_factor_gt(self, value: float | None) -> None:
        """Set the R factor for observations above the threshold."""
        self._r_factor_gt.value = value

    @property
    def wr_factor_gt(self) -> NumericDescriptor:
        """Weighted R factor for observations above the threshold."""
        return self._wr_factor_gt

    def _set_wr_factor_gt(self, value: float | None) -> None:
        """Set the weighted R factor above the threshold."""
        self._wr_factor_gt.value = value

    @property
    def threshold_expression(self) -> StringDescriptor:
        """Expression defining the observed-reflection threshold."""
        return self._threshold_expression

    def _set_threshold_expression(self, value: str | None) -> None:
        """Set the observed-reflection threshold expression."""
        self._threshold_expression.value = value

    @property
    def number_reflns_total(self) -> NumericDescriptor:
        """Total number of reflections represented in the fit."""
        return self._number_reflns_total

    def _set_number_reflns_total(self, value: float | None) -> None:
        """Set the total number of reflections in the fit."""
        self._number_reflns_total.value = value

    @property
    def number_reflns_gt(self) -> NumericDescriptor:
        """Number of reflections above the observed threshold."""
        return self._number_reflns_gt

    def _set_number_reflns_gt(self, value: float | None) -> None:
        """Set the number of reflections above the threshold."""
        self._number_reflns_gt.value = value


class _LeastSquaresPowderProperties:
    """Powder-profile and fit-control aggregate descriptors."""

    @property
    def prof_r_factor(self) -> NumericDescriptor:
        """Profile R factor for powder fits."""
        return self._prof_r_factor

    def _set_prof_r_factor(self, value: float | None) -> None:
        """Set the profile R factor for powder fits."""
        self._prof_r_factor.value = value

    @property
    def prof_wr_factor(self) -> NumericDescriptor:
        """Weighted profile R factor for powder fits."""
        return self._prof_wr_factor

    def _set_prof_wr_factor(self, value: float | None) -> None:
        """Set the weighted profile R factor for powder fits."""
        self._prof_wr_factor.value = value

    @property
    def prof_wr_expected(self) -> NumericDescriptor:
        """Expected weighted profile R factor for powder fits."""
        return self._prof_wr_expected

    def _set_prof_wr_expected(self, value: float | None) -> None:
        """Set the expected weighted profile R factor (powder)."""
        self._prof_wr_expected.value = value

    @property
    def number_restraints(self) -> NumericDescriptor:
        """Number of restraints used in the deterministic fit."""
        return self._number_restraints

    def _set_number_restraints(self, value: float | None) -> None:
        """Set the number of restraints used in the fit."""
        self._number_restraints.value = value

    @property
    def number_constraints(self) -> NumericDescriptor:
        """Number of constraints used in the deterministic fit."""
        return self._number_constraints

    def _set_number_constraints(self, value: float | None) -> None:
        """Set the number of constraints used in the fit."""
        self._number_constraints.value = value

    @property
    def shift_over_su_max(self) -> NumericDescriptor:
        """Maximum absolute parameter shift divided by s.u."""
        return self._shift_over_su_max

    def _set_shift_over_su_max(self, value: float | None) -> None:
        """Set the maximum absolute parameter shift divided by s.u."""
        self._shift_over_su_max.value = value

    @property
    def shift_over_su_mean(self) -> NumericDescriptor:
        """Mean absolute parameter shift divided by s.u."""
        return self._shift_over_su_mean

    def _set_shift_over_su_mean(self, value: float | None) -> None:
        """Set the mean absolute parameter shift divided by s.u."""
        self._shift_over_su_mean.value = value

    @property
    def profile_function(self) -> StringDescriptor:
        """Active profile function names."""
        return self._profile_function

    def _set_profile_function(self, value: str | None) -> None:
        """Set the active profile function names."""
        self._profile_function.value = value

    @property
    def background_function(self) -> StringDescriptor:
        """Active background function names."""
        return self._background_function

    def _set_background_function(self, value: str | None) -> None:
        """Set the active background function names."""
        self._background_function.value = value


@FitResultFactory.register
class LeastSquaresFitResult(
    _LeastSquaresCoreProperties,
    _LeastSquaresReflectionProperties,
    _LeastSquaresPowderProperties,
    FitResultBase,
):
    """Persisted least-squares fit-result metadata."""

    type_info = TypeInfo(
        tag='least_squares',
        description='Persisted least-squares fit-result metadata',
    )
    _result_descriptor_names: ClassVar[tuple[str, ...]] = (
        *FitResultBase._result_descriptor_names,
        'objective_name',
        'objective_value',
        'n_data_points',
        'n_parameters',
        'n_free_parameters',
        'degrees_of_freedom',
        'covariance_available',
        'correlation_available',
        'exit_reason',
        'r_factor_all',
        'wr_factor_all',
        'r_factor_gt',
        'wr_factor_gt',
        'prof_r_factor',
        'prof_wr_factor',
        'prof_wr_expected',
        'number_restraints',
        'number_constraints',
        'shift_over_su_max',
        'shift_over_su_mean',
        'profile_function',
        'background_function',
        'threshold_expression',
        'number_reflns_total',
        'number_reflns_gt',
    )
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = _result_descriptor_names
    _cif_required_descriptor_names: ClassVar[tuple[str, ...]] = (
        *FitResultBase._result_descriptor_names,
        'objective_name',
        'objective_value',
        'n_data_points',
        'n_parameters',
        'n_free_parameters',
        'degrees_of_freedom',
        'covariance_available',
        'correlation_available',
    )
    _cif_reflection_descriptor_names: ClassVar[tuple[str, ...]] = (
        'r_factor_all',
        'wr_factor_all',
        'r_factor_gt',
        'wr_factor_gt',
        'threshold_expression',
        'number_reflns_total',
        'number_reflns_gt',
    )
    _cif_powder_descriptor_names: ClassVar[tuple[str, ...]] = (
        'prof_r_factor',
        'prof_wr_factor',
        'prof_wr_expected',
        'profile_function',
        'background_function',
    )
    _cif_positive_count_descriptor_names: ClassVar[tuple[str, ...]] = (
        'number_restraints',
        'number_constraints',
    )

    def __init__(self) -> None:
        """Initialize the least-squares fit-result descriptors."""
        super().__init__()
        self._objective_name = self._string_result_descriptor(
            'objective_name',
            'Objective function name for the persisted deterministic fit.',
            'Objective function',
        )
        self._objective_value = self._numeric_result_descriptor(
            'objective_value',
            'Objective value for the persisted deterministic fit.',
            'Objective value',
        )
        self._n_data_points = self._integer_result_descriptor(
            'n_data_points',
            'Number of data points used in the persisted deterministic fit.',
            'Number of data points',
        )
        self._n_parameters = self._integer_result_descriptor(
            'n_parameters',
            'Number of parameters considered in the persisted deterministic fit.',
            'Number of parameters',
        )
        self._n_free_parameters = self._integer_result_descriptor(
            'n_free_parameters',
            'Number of free parameters in the persisted deterministic fit.',
            'Number of free parameters',
        )
        self._degrees_of_freedom = self._integer_result_descriptor(
            'degrees_of_freedom',
            'Degrees of freedom for the persisted deterministic fit.',
            'Degrees of freedom',
        )
        self._covariance_available = self._bool_result_descriptor(
            'covariance_available',
            'Whether covariance was available for the persisted deterministic fit.',
            'Covariance available',
        )
        self._correlation_available = self._bool_result_descriptor(
            'correlation_available',
            'Whether correlations were available for the persisted deterministic fit.',
            'Correlation available',
        )
        self._exit_reason = self._string_result_descriptor(
            'exit_reason',
            'Backend exit reason for the persisted deterministic fit.',
            'Exit reason',
        )
        self._r_factor_all = self._numeric_result_descriptor(
            'r_factor_all',
            'R factor for all observed data in the deterministic fit.',
            'R-factor (all)',
            cif_name='R_factor_all',
        )
        self._wr_factor_all = self._numeric_result_descriptor(
            'wr_factor_all',
            'Weighted R factor for all observed data in the fit.',
            'Weighted R-factor (all)',
            cif_name='wR_factor_all',
        )
        self._r_factor_gt = self._numeric_result_descriptor(
            'r_factor_gt',
            'R factor for observations above the threshold.',
            'R-factor (observed)',
            cif_name='R_factor_gt',
        )
        self._wr_factor_gt = self._numeric_result_descriptor(
            'wr_factor_gt',
            'Weighted R factor for observations above the threshold.',
            'Weighted R-factor (observed)',
            cif_name='wR_factor_gt',
        )
        self._prof_r_factor = self._numeric_result_descriptor(
            'prof_r_factor',
            'Profile R factor for powder deterministic fits.',
            'Profile R-factor',
            cif_name='prof_R_factor',
        )
        self._prof_wr_factor = self._numeric_result_descriptor(
            'prof_wr_factor',
            'Weighted profile R factor for powder deterministic fits.',
            'Weighted profile R-factor',
            cif_name='prof_wR_factor',
        )
        self._prof_wr_expected = self._numeric_result_descriptor(
            'prof_wr_expected',
            'Expected weighted profile R factor for powder fits.',
            'Expected weighted profile R-factor',
            cif_name='prof_wR_expected',
        )
        self._number_restraints = self._integer_result_descriptor(
            'number_restraints',
            'Number of restraints used in the deterministic fit.',
            'Number of restraints',
        )
        self._number_constraints = self._integer_result_descriptor(
            'number_constraints',
            'Number of constraints used in the deterministic fit.',
            'Number of constraints',
        )
        self._shift_over_su_max = self._numeric_result_descriptor(
            'shift_over_su_max',
            'Maximum absolute parameter shift divided by s.u.',
            'Max shift/s.u.',
        )
        self._shift_over_su_mean = self._numeric_result_descriptor(
            'shift_over_su_mean',
            'Mean absolute parameter shift divided by s.u.',
            'Mean shift/s.u.',
        )
        self._profile_function = self._string_result_descriptor(
            'profile_function',
            'Active profile function names for the deterministic fit.',
            'Profile function',
        )
        self._background_function = self._string_result_descriptor(
            'background_function',
            'Active background function names for the deterministic fit.',
            'Background function',
        )
        self._threshold_expression = self._string_result_descriptor(
            'threshold_expression',
            'Expression defining the observed-reflection threshold.',
            'Threshold expression',
        )
        self._number_reflns_total = self._integer_result_descriptor(
            'number_reflns_total',
            'Total number of reflections represented in the fit.',
            'Number of reflections (total)',
        )
        self._number_reflns_gt = self._integer_result_descriptor(
            'number_reflns_gt',
            'Number of reflections above the observed threshold.',
            'Number of reflections (observed)',
        )

    @staticmethod
    def _string_result_descriptor(
        name: str,
        description: str,
        display_name: str,
        *,
        cif_name: str | None = None,
    ) -> StringDescriptor:
        """
        Create a string-valued result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than an empty string, matching the shared "no fit"
        semantics of numeric, integer-like, and bool result fields.
        """
        return StringDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=_fit_result_cif_handler(name, cif_name),
            display_handler=_result_display_handler(display_name),
        )

    @staticmethod
    def _numeric_result_descriptor(
        name: str,
        description: str,
        display_name: str,
        *,
        default: float | None = None,
        allow_none: bool = True,
        cif_name: str | None = None,
    ) -> NumericDescriptor:
        """Create a numeric result descriptor."""
        return NumericDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=default, allow_none=allow_none),
            cif_handler=_fit_result_cif_handler(name, cif_name),
            display_handler=_result_display_handler(display_name),
        )

    @staticmethod
    def _integer_result_descriptor(
        name: str,
        description: str,
        display_name: str,
    ) -> NumericDescriptor:
        """
        Create an integer-like numeric result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than ``0``; the scientist audience reads ``0`` as a
        degenerate result, not as "no fit yet".
        """
        return NumericDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_fit_result.{name}']),
            display_handler=_result_display_handler(display_name),
        )

    @staticmethod
    def _bool_result_descriptor(
        name: str,
        description: str,
        display_name: str,
    ) -> BoolDescriptor:
        """
        Create a boolean result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than ``false``; ``false`` would otherwise read as an
        active result instead of "no fit happened yet".
        """
        return BoolDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_fit_result.{name}']),
            display_handler=_result_display_handler(display_name),
        )

    def _include_exit_reason_cif_descriptor(self) -> bool:
        """Return whether exit_reason adds distinct information."""
        exit_reason = self.exit_reason.value
        if exit_reason is None:
            return False
        return exit_reason != self.message.value

    def _cif_parameters(self) -> list[object]:
        """Return LSQ fit-result descriptors active for CIF output."""
        return [
            descriptor
            for descriptor in self.parameters
            if self._include_cif_descriptor(descriptor)
        ]

    def _include_cif_descriptor(self, descriptor: object) -> bool:
        """Return whether *descriptor* belongs in analysis CIF."""
        name = descriptor.name
        if name in self._cif_required_descriptor_names:
            return True
        if name == 'exit_reason':
            return self._include_exit_reason_cif_descriptor()
        if name in self._cif_reflection_descriptor_names:
            return self._has_reflection_result()
        if name in self._cif_powder_descriptor_names:
            return self._has_powder_result()
        if name in self._cif_positive_count_descriptor_names:
            return self._has_positive_value(descriptor)
        return False

    def _has_reflection_result(self) -> bool:
        """
        Return whether reflection-result descriptors are populated.
        """
        return any(
            self._has_value(getattr(self, name))
            for name in (
                'r_factor_all',
                'wr_factor_all',
                'r_factor_gt',
                'wr_factor_gt',
                'number_reflns_total',
                'number_reflns_gt',
            )
        )

    def _has_powder_result(self) -> bool:
        """Return whether powder-profile descriptors are populated."""
        return any(
            self._has_value(getattr(self, name)) for name in self._cif_powder_descriptor_names
        )

    @staticmethod
    def _has_value(descriptor: object) -> bool:
        """Return whether a descriptor carries a persisted value."""
        return descriptor.value is not None

    @staticmethod
    def _has_positive_value(descriptor: object) -> bool:
        """Return whether a count descriptor is positive."""
        value = descriptor.value
        return isinstance(value, (int, float)) and value > 0
