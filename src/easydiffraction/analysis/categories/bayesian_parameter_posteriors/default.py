# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian parameter posterior summary rows."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_parameter_posteriors.factory import (
    BayesianParameterPosteriorsFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class BayesianParameterPosteriorItem(CategoryItem):
    """Single persisted Bayesian parameter posterior summary row."""

    _category_code = 'bayesian_parameter_posterior'
    _category_entry_name = 'unique_name'

    def __init__(self) -> None:
        super().__init__()
        self._unique_name = StringDescriptor(
            name='unique_name',
            description='Unique EasyDiffraction parameter name.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.unique_name']),
        )
        self._display_name = StringDescriptor(
            name='display_name',
            description='Human-readable parameter label.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.display_name']),
        )
        self._best_sample_value = NumericDescriptor(
            name='best_sample_value',
            description='Committed sampled parameter value.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.best_sample_value']),
        )
        self._median = NumericDescriptor(
            name='median',
            description='Posterior median value.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.median']),
        )
        self._uncertainty = NumericDescriptor(
            name='uncertainty',
            description='Posterior standard deviation.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.uncertainty']),
        )
        self._interval_68_lower = NumericDescriptor(
            name='interval_68_lower',
            description='Lower bound of the 68% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.interval_68_lower']),
        )
        self._interval_68_upper = NumericDescriptor(
            name='interval_68_upper',
            description='Upper bound of the 68% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.interval_68_upper']),
        )
        self._interval_95_lower = NumericDescriptor(
            name='interval_95_lower',
            description='Lower bound of the 95% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.interval_95_lower']),
        )
        self._interval_95_upper = NumericDescriptor(
            name='interval_95_upper',
            description='Upper bound of the 95% credible interval.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.interval_95_upper']),
        )
        self._ess_bulk = NumericDescriptor(
            name='ess_bulk',
            description='Bulk effective sample size when available.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.ess_bulk']),
        )
        self._r_hat = NumericDescriptor(
            name='r_hat',
            description='Rank-normalized split-R-hat when available.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_parameter_posterior.r_hat']),
        )

    @property
    def unique_name(self) -> StringDescriptor:
        """Unique EasyDiffraction parameter name."""
        return self._unique_name

    def _set_unique_name(self, value: str) -> None:
        """Set the unique parameter name for internal callers."""
        self._unique_name.value = value

    @property
    def display_name(self) -> StringDescriptor:
        """Human-readable parameter label."""
        return self._display_name

    def _set_display_name(self, value: str) -> None:
        """Set the display name for internal callers."""
        self._display_name.value = value

    @property
    def best_sample_value(self) -> NumericDescriptor:
        """Committed sampled parameter value."""
        return self._best_sample_value

    def _set_best_sample_value(self, value: float | None) -> None:
        """Set the best sampled parameter value for internal callers."""
        self._best_sample_value.value = value

    @property
    def median(self) -> NumericDescriptor:
        """Posterior median value."""
        return self._median

    def _set_median(self, value: float | None) -> None:
        """Set the posterior median for internal callers."""
        self._median.value = value

    @property
    def uncertainty(self) -> NumericDescriptor:
        """Posterior standard deviation."""
        return self._uncertainty

    def _set_uncertainty(self, value: float | None) -> None:
        """Set the posterior uncertainty for internal callers."""
        self._uncertainty.value = value

    @property
    def interval_68_lower(self) -> NumericDescriptor:
        """Lower bound of the 68% credible interval."""
        return self._interval_68_lower

    def _set_interval_68_lower(self, value: float | None) -> None:
        """Set the 68% interval lower bound for internal callers."""
        self._interval_68_lower.value = value

    @property
    def interval_68_upper(self) -> NumericDescriptor:
        """Upper bound of the 68% credible interval."""
        return self._interval_68_upper

    def _set_interval_68_upper(self, value: float | None) -> None:
        """Set the 68% interval upper bound for internal callers."""
        self._interval_68_upper.value = value

    @property
    def interval_95_lower(self) -> NumericDescriptor:
        """Lower bound of the 95% credible interval."""
        return self._interval_95_lower

    def _set_interval_95_lower(self, value: float | None) -> None:
        """Set the 95% interval lower bound for internal callers."""
        self._interval_95_lower.value = value

    @property
    def interval_95_upper(self) -> NumericDescriptor:
        """Upper bound of the 95% credible interval."""
        return self._interval_95_upper

    def _set_interval_95_upper(self, value: float | None) -> None:
        """Set the 95% interval upper bound for internal callers."""
        self._interval_95_upper.value = value

    @property
    def ess_bulk(self) -> NumericDescriptor:
        """Bulk effective sample size when available."""
        return self._ess_bulk

    def _set_ess_bulk(self, value: float | None) -> None:
        """Set the ESS bulk value for internal callers."""
        self._ess_bulk.value = value

    @property
    def r_hat(self) -> NumericDescriptor:
        """Rank-normalized split-R-hat when available."""
        return self._r_hat

    def _set_r_hat(self, value: float | None) -> None:
        """Set the R-hat value for internal callers."""
        self._r_hat.value = value


@BayesianParameterPosteriorsFactory.register
class BayesianParameterPosteriors(CategoryCollection):
    """
    Collection of persisted Bayesian parameter posterior summaries.
    """

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian parameter posterior summaries',
    )

    def __init__(self) -> None:
        super().__init__(item_type=BayesianParameterPosteriorItem)

    def create(
        self,
        *,
        unique_name: str,
        display_name: str,
        best_sample_value: float | None = None,
        median: float | None = None,
        uncertainty: float | None = None,
        interval_68_lower: float | None = None,
        interval_68_upper: float | None = None,
        interval_95_lower: float | None = None,
        interval_95_upper: float | None = None,
        ess_bulk: float | None = None,
        r_hat: float | None = None,
    ) -> None:
        """
        Create a persisted Bayesian parameter posterior summary row.

        Parameters
        ----------
        unique_name : str
            Unique EasyDiffraction parameter name.
        display_name : str
            Human-readable parameter label.
        best_sample_value : int | float | None, default=None
            Committed sampled parameter value.
        median : int | float | None, default=None
            Posterior median value.
        uncertainty : int | float | None, default=None
            Posterior standard deviation.
        interval_68_lower : int | float | None, default=None
            Lower bound of the 68% credible interval.
        interval_68_upper : int | float | None, default=None
            Upper bound of the 68% credible interval.
        interval_95_lower : int | float | None, default=None
            Lower bound of the 95% credible interval.
        interval_95_upper : int | float | None, default=None
            Upper bound of the 95% credible interval.
        ess_bulk : int | float | None, default=None
            Bulk effective sample size when available.
        r_hat : int | float | None, default=None
            Rank-normalized split-R-hat when available.
        """
        item = BayesianParameterPosteriorItem()
        item._set_unique_name(unique_name)
        item._set_display_name(display_name)
        item._set_best_sample_value(best_sample_value)
        item._set_median(median)
        item._set_uncertainty(uncertainty)
        item._set_interval_68_lower(interval_68_lower)
        item._set_interval_68_upper(interval_68_upper)
        item._set_interval_95_lower(interval_95_lower)
        item._set_interval_95_upper(interval_95_upper)
        item._set_ess_bulk(ess_bulk)
        item._set_r_hat(r_hat)
        self.add(item)
