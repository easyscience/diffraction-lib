# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-parameter control snapshots."""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from easydiffraction.analysis.categories.fit_parameters.factory import FitParametersFactory
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.posterior import PosteriorParameterSummary
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class FitParameterItem(CategoryItem):
    """Single persisted fit-parameter control row."""

    _category_code = 'fit_parameter'
    _category_entry_name = 'param_unique_name'
    _control_descriptor_names: ClassVar[tuple[str, ...]] = (
        'param_unique_name',
        'fit_min',
        'fit_max',
        'start_value',
        'start_uncertainty',
    )
    _optional_control_descriptor_names: ClassVar[tuple[str, ...]] = (
        'fit_bounds_uncertainty_multiplier',
    )
    _posterior_descriptor_names: ClassVar[tuple[str, ...]] = (
        'posterior_best_sample_value',
        'posterior_median',
        'posterior_uncertainty',
        'posterior_interval_68_low',
        'posterior_interval_68_high',
        'posterior_interval_95_low',
        'posterior_interval_95_high',
        'posterior_gelman_rubin',
        'posterior_effective_sample_size_bulk',
    )

    def __init__(self) -> None:
        super().__init__()
        self._param_unique_name = StringDescriptor(
            name='param_unique_name',
            description='Unique name of the referenced live parameter.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_fit_parameter.param_unique_name']),
        )
        self._fit_min = NumericDescriptor(
            name='fit_min',
            description='Persisted lower fit bound.',
            value_spec=AttributeSpec(default=-np.inf),
            cif_handler=CifHandler(names=['_fit_parameter.fit_min']),
        )
        self._fit_max = NumericDescriptor(
            name='fit_max',
            description='Persisted upper fit bound.',
            value_spec=AttributeSpec(default=np.inf),
            cif_handler=CifHandler(names=['_fit_parameter.fit_max']),
        )
        self._fit_bounds_uncertainty_multiplier = NumericDescriptor(
            name='fit_bounds_uncertainty_multiplier',
            description='Multiplier used to derive fit bounds from uncertainty.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.fit_bounds_uncertainty_multiplier']),
        )
        self._start_value = NumericDescriptor(
            name='start_value',
            description='Persisted pre-fit value snapshot.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.start_value']),
        )
        self._start_uncertainty = NumericDescriptor(
            name='start_uncertainty',
            description='Persisted pre-fit uncertainty snapshot.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.start_uncertainty']),
        )
        self._posterior_best_sample_value = NumericDescriptor(
            name='posterior_best_sample_value',
            description='Highest-posterior sampled parameter value.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_best_sample_value']),
        )
        self._posterior_median = NumericDescriptor(
            name='posterior_median',
            description='Posterior median value.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_median']),
        )
        self._posterior_uncertainty = NumericDescriptor(
            name='posterior_uncertainty',
            description='Posterior standard deviation.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_uncertainty']),
        )
        self._posterior_interval_68_low = NumericDescriptor(
            name='posterior_interval_68_low',
            description='Lower bound of the 68% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_interval_68_low']),
        )
        self._posterior_interval_68_high = NumericDescriptor(
            name='posterior_interval_68_high',
            description='Upper bound of the 68% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_interval_68_high']),
        )
        self._posterior_interval_95_low = NumericDescriptor(
            name='posterior_interval_95_low',
            description='Lower bound of the 95% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_interval_95_low']),
        )
        self._posterior_interval_95_high = NumericDescriptor(
            name='posterior_interval_95_high',
            description='Upper bound of the 95% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_interval_95_high']),
        )
        self._posterior_gelman_rubin = NumericDescriptor(
            name='posterior_gelman_rubin',
            description='Rank-normalized split-R-hat when available.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_gelman_rubin']),
        )
        self._posterior_effective_sample_size_bulk = NumericDescriptor(
            name='posterior_effective_sample_size_bulk',
            description='Bulk effective sample size when available.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.posterior_effective_sample_size_bulk']),
        )

    @property
    def param_unique_name(self) -> StringDescriptor:
        """Unique name of the referenced live parameter."""
        return self._param_unique_name

    def _set_param_unique_name(self, value: str) -> None:
        """
        Set the referenced parameter unique name for internal callers.
        """
        self._param_unique_name.value = value

    @property
    def fit_min(self) -> NumericDescriptor:
        """Persisted lower fit bound."""
        return self._fit_min

    def _set_fit_min(self, value: float) -> None:
        """Set the persisted lower fit bound for internal callers."""
        self._fit_min.value = value

    @property
    def fit_max(self) -> NumericDescriptor:
        """Persisted upper fit bound."""
        return self._fit_max

    def _set_fit_max(self, value: float) -> None:
        """Set the persisted upper fit bound for internal callers."""
        self._fit_max.value = value

    @property
    def fit_bounds_uncertainty_multiplier(self) -> NumericDescriptor:
        """Multiplier used to derive fit bounds from uncertainty."""
        return self._fit_bounds_uncertainty_multiplier

    def _set_fit_bounds_uncertainty_multiplier(
        self,
        value: float | None,
    ) -> None:
        """
        Set the fit-bounds uncertainty multiplier for internal callers.
        """
        self._fit_bounds_uncertainty_multiplier.value = value

    @property
    def start_value(self) -> NumericDescriptor:
        """Persisted pre-fit value snapshot."""
        return self._start_value

    def _set_start_value(self, value: float | None) -> None:
        """Set the pre-fit value snapshot for internal callers."""
        self._start_value.value = value

    @property
    def start_uncertainty(self) -> NumericDescriptor:
        """Persisted pre-fit uncertainty snapshot."""
        return self._start_uncertainty

    def _set_start_uncertainty(self, value: float | None) -> None:
        """Set the pre-fit uncertainty snapshot for internal callers."""
        self._start_uncertainty.value = value

    @property
    def posterior_best_sample_value(self) -> NumericDescriptor:
        """Highest-posterior sampled parameter value."""
        return self._posterior_best_sample_value

    def _set_posterior_best_sample_value(self, value: float | None) -> None:
        """Set the posterior best sample for internal callers."""
        self._posterior_best_sample_value.value = value

    @property
    def posterior_median(self) -> NumericDescriptor:
        """Posterior median value."""
        return self._posterior_median

    def _set_posterior_median(self, value: float | None) -> None:
        """Set the posterior median for internal callers."""
        self._posterior_median.value = value

    @property
    def posterior_uncertainty(self) -> NumericDescriptor:
        """Posterior standard deviation."""
        return self._posterior_uncertainty

    def _set_posterior_uncertainty(self, value: float | None) -> None:
        """Set the posterior uncertainty for internal callers."""
        self._posterior_uncertainty.value = value

    @property
    def posterior_interval_68_low(self) -> NumericDescriptor:
        """Lower bound of the 68% credible interval."""
        return self._posterior_interval_68_low

    def _set_posterior_interval_68_low(self, value: float | None) -> None:
        """Set the lower 68% interval bound for internal callers."""
        self._posterior_interval_68_low.value = value

    @property
    def posterior_interval_68_high(self) -> NumericDescriptor:
        """Upper bound of the 68% credible interval."""
        return self._posterior_interval_68_high

    def _set_posterior_interval_68_high(self, value: float | None) -> None:
        """Set the upper 68% interval bound for internal callers."""
        self._posterior_interval_68_high.value = value

    @property
    def posterior_interval_95_low(self) -> NumericDescriptor:
        """Lower bound of the 95% credible interval."""
        return self._posterior_interval_95_low

    def _set_posterior_interval_95_low(self, value: float | None) -> None:
        """Set the lower 95% interval bound for internal callers."""
        self._posterior_interval_95_low.value = value

    @property
    def posterior_interval_95_high(self) -> NumericDescriptor:
        """Upper bound of the 95% credible interval."""
        return self._posterior_interval_95_high

    def _set_posterior_interval_95_high(self, value: float | None) -> None:
        """Set the upper 95% interval bound for internal callers."""
        self._posterior_interval_95_high.value = value

    @property
    def posterior_gelman_rubin(self) -> NumericDescriptor:
        """Rank-normalized split-R-hat when available."""
        return self._posterior_gelman_rubin

    def _set_posterior_gelman_rubin(self, value: float | None) -> None:
        """Set the posterior R-hat for internal callers."""
        self._posterior_gelman_rubin.value = value

    @property
    def posterior_effective_sample_size_bulk(self) -> NumericDescriptor:
        """Bulk effective sample size when available."""
        return self._posterior_effective_sample_size_bulk

    def _set_posterior_effective_sample_size_bulk(self, value: float | None) -> None:
        """Set the posterior bulk ESS for internal callers."""
        self._posterior_effective_sample_size_bulk.value = value

    def _set_posterior_summary(self, summary: PosteriorParameterSummary) -> None:
        """Set posterior summary fields for internal callers."""
        self._set_posterior_best_sample_value(summary.best_sample_value)
        self._set_posterior_median(summary.median)
        self._set_posterior_uncertainty(summary.standard_deviation)
        self._set_posterior_interval_68_low(summary.interval_68[0])
        self._set_posterior_interval_68_high(summary.interval_68[1])
        self._set_posterior_interval_95_low(summary.interval_95[0])
        self._set_posterior_interval_95_high(summary.interval_95[1])
        self._set_posterior_gelman_rubin(summary.r_hat)
        self._set_posterior_effective_sample_size_bulk(summary.ess_bulk)

    def has_posterior_summary(self) -> bool:
        """Return whether any posterior summary field is populated."""
        return any(
            value is not None
            for value in (
                self.posterior_best_sample_value.value,
                self.posterior_median.value,
                self.posterior_uncertainty.value,
                self.posterior_interval_68_low.value,
                self.posterior_interval_68_high.value,
                self.posterior_interval_95_low.value,
                self.posterior_interval_95_high.value,
                self.posterior_gelman_rubin.value,
                self.posterior_effective_sample_size_bulk.value,
            )
        )

    @staticmethod
    def _posterior_float(value: float | None) -> float:
        """Return a posterior value or NaN for incomplete rows."""
        return np.nan if value is None else float(value)

    def posterior_summary(self, *, display_name: str) -> PosteriorParameterSummary | None:
        """Return this row as a posterior summary, if populated."""
        if not self.has_posterior_summary():
            return None

        return PosteriorParameterSummary(
            unique_name=self.param_unique_name.value,
            display_name=display_name,
            best_sample_value=self._posterior_float(self.posterior_best_sample_value.value),
            median=self._posterior_float(self.posterior_median.value),
            standard_deviation=self._posterior_float(self.posterior_uncertainty.value),
            interval_68=(
                self._posterior_float(self.posterior_interval_68_low.value),
                self._posterior_float(self.posterior_interval_68_high.value),
            ),
            interval_95=(
                self._posterior_float(self.posterior_interval_95_low.value),
                self._posterior_float(self.posterior_interval_95_high.value),
            ),
            ess_bulk=self.posterior_effective_sample_size_bulk.value,
            r_hat=self.posterior_gelman_rubin.value,
        )


@FitParametersFactory.register
class FitParameters(CategoryCollection):
    """Collection of persisted fit-parameter control snapshots."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted fit-parameter control snapshots',
    )

    def __init__(self) -> None:
        super().__init__(item_type=FitParameterItem)

    def _include_posterior_cif_descriptors(self) -> bool:
        """Return whether CIF output includes posterior columns."""
        parent = getattr(self, '_parent', None)
        fit_result = getattr(parent, 'fit_result', None)
        result_kind = getattr(getattr(fit_result, 'result_kind', None), 'value', None)
        if result_kind is not None:
            return result_kind == FitResultKindEnum.BAYESIAN.value
        return any(item.has_posterior_summary() for item in self)

    def _include_uncertainty_multiplier_cif_descriptor(self) -> bool:
        """Return whether CIF output includes the bounds multiplier."""
        return any(
            item.fit_bounds_uncertainty_multiplier.value is not None
            for item in self
        )

    def _cif_loop_parameters(self, item: FitParameterItem) -> list[object]:
        """Return CIF loop descriptors for the current fit kind."""
        descriptor_names = FitParameterItem._control_descriptor_names
        if self._include_uncertainty_multiplier_cif_descriptor():
            descriptor_names = (
                *descriptor_names[:3],
                *FitParameterItem._optional_control_descriptor_names,
                *descriptor_names[3:],
            )
        if self._include_posterior_cif_descriptors():
            descriptor_names = (
                *descriptor_names,
                *FitParameterItem._posterior_descriptor_names,
            )
        return [getattr(item, name) for name in descriptor_names]

    def create(
        self,
        *,
        param_unique_name: str,
        fit_min: float,
        fit_max: float,
        fit_bounds_uncertainty_multiplier: float | None = None,
        start_value: float | None = None,
        start_uncertainty: float | None = None,
    ) -> None:
        """
        Create a persisted fit-parameter control snapshot row.

        Parameters
        ----------
        param_unique_name : str
            Unique name of the referenced live parameter.
        fit_min : float
            Persisted lower fit bound.
        fit_max : float
            Persisted upper fit bound.
        fit_bounds_uncertainty_multiplier : float | None, default=None
            Multiplier used to derive fit bounds from uncertainty.
        start_value : float | None, default=None
            Persisted pre-fit value snapshot.
        start_uncertainty : float | None, default=None
            Persisted pre-fit uncertainty snapshot.
        """
        item = FitParameterItem()
        item._set_param_unique_name(param_unique_name)
        item._set_fit_min(fit_min)
        item._set_fit_max(fit_max)
        item._set_fit_bounds_uncertainty_multiplier(fit_bounds_uncertainty_multiplier)
        item._set_start_value(start_value)
        item._set_start_uncertainty(start_uncertainty)
        self.add(item)

    def set_posterior_summary(self, summary: PosteriorParameterSummary) -> None:
        """Attach a posterior summary to an existing row."""
        item = self[summary.unique_name]
        item._set_posterior_summary(summary)
