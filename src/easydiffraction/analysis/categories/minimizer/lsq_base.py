# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Behavior helpers for deterministic minimizer categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.lsq import LeastSquaresFitResult
from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.io.cif.handler import TagSpec


class LeastSquaresMinimizerBase(MinimizerCategoryBase):
    """Shared behavior for least-squares minimizer categories."""

    _default_max_iterations: ClassVar[int] = 1000
    _fit_result_class: ClassVar[type] = LeastSquaresFitResult
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = ('max_iterations',)
    _native_key_map: ClassVar[dict[str, str]] = {
        'max_iterations': 'max_iterations',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = ('max_iterations',)
    _result_descriptor_names: ClassVar[tuple[str, ...]] = ()

    def __init__(self) -> None:
        """Initialize the max-iterations setting descriptor."""
        super().__init__()
        self._max_iterations = self._max_iterations_descriptor(self._default_max_iterations)

    @staticmethod
    def _max_iterations_descriptor(default: int) -> IntegerDescriptor:
        """Create a max-iterations descriptor."""
        return IntegerDescriptor(
            name='max_iterations',
            description='Maximum solver iterations.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            tags=TagSpec(
                edi_names=['_minimizer.max_iterations'],
                cif_names=['_easydiffraction_minimizer.max_iterations'],
            ),
            display_handler=DisplayHandler(
                display_name='Maximum iterations',
                latex_name='Maximum iterations',
            ),
        )

    @property
    def max_iterations(self) -> IntegerDescriptor:
        """Maximum solver iterations."""
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        """Set the maximum solver iterations."""
        self._max_iterations.value = value


class ObjectiveParameterToleranceMinimizerBase(LeastSquaresMinimizerBase):
    """Settings with objective and parameter stopping criteria."""

    _default_chi_square_change_tolerance: ClassVar[float] = 1e-8
    _default_parameter_change_tolerance: ClassVar[float] = 1e-8
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._expected_descriptor_names,
        'chi_square_change_tolerance',
        'parameter_change_tolerance',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        **LeastSquaresMinimizerBase._native_key_map,
        'chi_square_change_tolerance': 'chi_square_change_tolerance',
        'parameter_change_tolerance': 'parameter_change_tolerance',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._setting_descriptor_names,
        'chi_square_change_tolerance',
        'parameter_change_tolerance',
    )

    def __init__(self) -> None:
        """Initialize objective and parameter change tolerances."""
        super().__init__()
        self._chi_square_change_tolerance = self._tolerance_descriptor(
            name='chi_square_change_tolerance',
            description='Relative change in the objective (chi-square) used to stop fitting.',
            display_name='χ² change tolerance',
            default=self._default_chi_square_change_tolerance,
        )
        self._parameter_change_tolerance = self._tolerance_descriptor(
            name='parameter_change_tolerance',
            description='Relative change in fitted parameters used to stop fitting.',
            display_name='Parameter change tolerance',
            default=self._default_parameter_change_tolerance,
        )

    @staticmethod
    def _tolerance_descriptor(
        *,
        name: str,
        description: str,
        display_name: str,
        default: float,
        allow_zero: bool = False,
    ) -> NumericDescriptor:
        """Create a dimensionless solver-tolerance descriptor."""
        validator = RangeValidator(ge=0.0) if allow_zero else RangeValidator(gt=0.0)
        return NumericDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=default, validator=validator),
            tags=TagSpec(
                edi_names=[f'_minimizer.{name}'],
                cif_names=[f'_easydiffraction_minimizer.{name}'],
            ),
            display_handler=DisplayHandler(
                display_name=display_name,
                latex_name=display_name,
            ),
        )

    @property
    def chi_square_change_tolerance(self) -> NumericDescriptor:
        """Relative chi-square change used for convergence."""
        return self._chi_square_change_tolerance

    @chi_square_change_tolerance.setter
    def chi_square_change_tolerance(self, value: float) -> None:
        """Set the relative objective-change tolerance."""
        self._chi_square_change_tolerance.value = value

    @property
    def parameter_change_tolerance(self) -> NumericDescriptor:
        """Relative parameter change used for convergence."""
        return self._parameter_change_tolerance

    @parameter_change_tolerance.setter
    def parameter_change_tolerance(self, value: float) -> None:
        """Set the relative parameter-change tolerance."""
        self._parameter_change_tolerance.value = value


class GradientToleranceMinimizerBase(ObjectiveParameterToleranceMinimizerBase):
    """Settings that also expose a gradient stopping criterion."""

    _default_gradient_tolerance: ClassVar[float] = 1e-8
    _gradient_tolerance_allows_zero: ClassVar[bool] = False
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        *ObjectiveParameterToleranceMinimizerBase._expected_descriptor_names,
        'gradient_tolerance',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        **ObjectiveParameterToleranceMinimizerBase._native_key_map,
        'gradient_tolerance': 'gradient_tolerance',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        *ObjectiveParameterToleranceMinimizerBase._setting_descriptor_names,
        'gradient_tolerance',
    )

    def __init__(self) -> None:
        """Initialize the gradient tolerance."""
        super().__init__()
        self._gradient_tolerance = self._tolerance_descriptor(
            name='gradient_tolerance',
            description='Gradient orthogonality used to stop fitting; zero disables it.',
            display_name='Gradient tolerance',
            default=self._default_gradient_tolerance,
            allow_zero=self._gradient_tolerance_allows_zero,
        )

    @property
    def gradient_tolerance(self) -> NumericDescriptor:
        """Gradient orthogonality used for convergence."""
        return self._gradient_tolerance

    @gradient_tolerance.setter
    def gradient_tolerance(self, value: float) -> None:
        """Set the gradient tolerance."""
        self._gradient_tolerance.value = value


class PopulationToleranceMinimizerBase(LeastSquaresMinimizerBase):
    """Settings for population-based minimizers."""

    _default_population_convergence_tolerance: ClassVar[float] = 1e-6
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._expected_descriptor_names,
        'population_convergence_tolerance',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        **LeastSquaresMinimizerBase._native_key_map,
        'population_convergence_tolerance': 'population_convergence_tolerance',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._setting_descriptor_names,
        'population_convergence_tolerance',
    )

    def __init__(self) -> None:
        """Initialize the population-convergence tolerance."""
        super().__init__()
        self._population_convergence_tolerance = (
            ObjectiveParameterToleranceMinimizerBase._tolerance_descriptor(
                name='population_convergence_tolerance',
                description='Population spread used to stop differential evolution.',
                display_name='Population convergence tolerance',
                default=self._default_population_convergence_tolerance,
            )
        )

    @property
    def population_convergence_tolerance(self) -> NumericDescriptor:
        """Population spread used for convergence."""
        return self._population_convergence_tolerance

    @population_convergence_tolerance.setter
    def population_convergence_tolerance(self, value: float) -> None:
        """Set the population-convergence tolerance."""
        self._population_convergence_tolerance.value = value


class TrustRegionToleranceMinimizerBase(LeastSquaresMinimizerBase):
    """Settings for derivative-free trust-region minimizers."""

    _default_final_trust_region_radius: ClassVar[float] = 1e-8
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._expected_descriptor_names,
        'final_trust_region_radius',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        **LeastSquaresMinimizerBase._native_key_map,
        'final_trust_region_radius': 'final_trust_region_radius',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        *LeastSquaresMinimizerBase._setting_descriptor_names,
        'final_trust_region_radius',
    )

    def __init__(self) -> None:
        """Initialize the final trust-region radius."""
        super().__init__()
        self._final_trust_region_radius = (
            ObjectiveParameterToleranceMinimizerBase._tolerance_descriptor(
                name='final_trust_region_radius',
                description='Final trust-region radius used to stop DFO-LS.',
                display_name='Final trust-region radius',
                default=self._default_final_trust_region_radius,
            )
        )

    @property
    def final_trust_region_radius(self) -> NumericDescriptor:
        """Final trust-region radius used for convergence."""
        return self._final_trust_region_radius

    @final_trust_region_radius.setter
    def final_trust_region_radius(self, value: float) -> None:
        """Set the final trust-region radius."""
        self._final_trust_region_radius.value = value
