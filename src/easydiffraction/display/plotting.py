# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotting facade for measured and calculated patterns.

Uses the common :class:`RendererBase` so plotters and tablers share a
consistent configuration surface and engine handling.
"""

import pathlib
from enum import StrEnum

import numpy as np
import pandas as pd

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.plotters.ascii import AsciiPlotter
from easydiffraction.display.plotters.base import DEFAULT_AXES_LABELS
from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import DEFAULT_MAX
from easydiffraction.display.plotters.base import DEFAULT_MIN
from easydiffraction.display.plotters.base import DEFAULT_X_AXIS
from easydiffraction.display.plotters.base import XAxisType
from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class PlotterEngineEnum(StrEnum):
    """Available plotting engine backends."""

    ASCII = 'asciichartpy'
    PLOTLY = 'plotly'

    @classmethod
    def default(cls) -> 'PlotterEngineEnum':
        """Select default engine based on environment."""
        if in_jupyter():
            log.debug('Setting default plotting engine to Plotly for Jupyter')
            return cls.PLOTLY
        log.debug('Setting default plotting engine to Asciichartpy for console')
        return cls.ASCII

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is PlotterEngineEnum.ASCII:
            return 'Console ASCII line charts'
        if self is PlotterEngineEnum.PLOTLY:
            return 'Interactive browser-based graphing library'
        return ''


DEFAULT_CORRELATION_THRESHOLD = 0.7
EXPECTED_COVAR_NDIM = 2


class Plotter(RendererBase):
    """User-facing plotting facade backed by concrete plotters."""

    # ------------------------------------------------------------------
    #  Private special methods
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        super().__init__()
        # X-axis limits
        self._x_min = DEFAULT_MIN
        self._x_max = DEFAULT_MAX
        # Chart height
        self.height = DEFAULT_HEIGHT
        # Back-reference to the owning Project (set via _set_project)
        self._project = None

    # ------------------------------------------------------------------
    #  Private class methods
    # ------------------------------------------------------------------

    def _set_project(self, project: object) -> None:
        """Wire the owning project for high-level plot methods."""
        self._project = project

    def _update_project_categories(self, expt_name: str) -> None:
        """Update all project categories before plotting."""
        for structure in self._project.structures:
            structure._update_categories()
        self._project.analysis._update_categories()
        experiment = self._project.experiments[expt_name]
        experiment._update_categories()

    @classmethod
    def _factory(cls) -> type[RendererFactoryBase]:  # type: ignore[override]
        return PlotterFactory

    @classmethod
    def _default_engine(cls) -> str:
        return PlotterEngineEnum.default().value

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _auto_x_range_for_ascii(
        self,
        pattern: object,
        x_array: object,
        x_min: object,
        x_max: object,
    ) -> tuple:
        """
        For the ASCII engine, narrow the range around the tallest peak.

        Parameters
        ----------
        pattern : object
            Data pattern object (needs ``intensity_meas``).
        x_array : object
            Full x-axis array.
        x_min : object
            Current minimum (may be ``None``).
        x_max : object
            Current maximum (may be ``None``).

        Returns
        -------
        tuple
            Tuple of ``(x_min, x_max)``, possibly narrowed.
        """
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.intensity_meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]
        return x_min, x_max

    def _filtered_y_array(
        self,
        y_array: object,
        x_array: object,
        x_min: object,
        x_max: object,
    ) -> object:
        """
        Filter an array by the inclusive x-range limits.

        Parameters
        ----------
        y_array : object
            1D array-like of y values.
        x_array : object
            1D array-like of x values (same length as ``y_array``).
        x_min : object
            Minimum x limit (or ``None`` to use default).
        x_max : object
            Maximum x limit (or ``None`` to use default).

        Returns
        -------
        object
            Filtered ``y_array`` values where ``x_array`` lies within
            ``[x_min, x_max]``.
        """
        if x_min is None:
            x_min = self.x_min
        if x_max is None:
            x_max = self.x_max

        mask = (x_array >= x_min) & (x_array <= x_max)
        filtered_y_array = y_array[mask]

        return filtered_y_array

    @staticmethod
    def _get_axes_labels(
        sample_form: object,
        scattering_type: object,
        x_axis: object,
    ) -> list:
        """Look up axis labels for the experiment / x-axis."""
        return DEFAULT_AXES_LABELS[sample_form, scattering_type, x_axis]

    def _prepare_powder_context(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object,
        x_max: object,
        x: object,
    ) -> dict | None:
        """
        Resolve axes, auto-range, and filter x-array.

        Parameters
        ----------
        pattern : object
            Data pattern object with intensity arrays.
        expt_name : str
            Experiment name for error messages.
        expt_type : object
            Experiment type with sample_form, scattering, and beam
            enums.
        x_min : object
            Optional minimum x-axis limit.
        x_max : object
            Optional maximum x-axis limit.
        x : object
            Explicit x-axis type or ``None``.

        Returns
        -------
        dict | None
            A dict with keys ``x_filtered``, ``x_array``, ``x_min``,
            ``x_max``, and ``axes_labels``; or ``None`` when the x-array
            is missing.
        """
        x_axis, x_name, sample_form, scattering_type, _ = self._resolve_x_axis(expt_type, x)

        # Get x-array from pattern
        x_raw = getattr(pattern, x_axis, None)
        if x_raw is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return None

        x_array = np.asarray(x_raw)

        # Auto-range for ASCII engine
        x_min, x_max = self._auto_x_range_for_ascii(pattern, x_array, x_min, x_max)

        # Filter x
        x_filtered = self._filtered_y_array(x_array, x_array, x_min, x_max)

        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)

        return {
            'x_filtered': x_filtered,
            'x_array': x_array,
            'x_min': x_min,
            'x_max': x_max,
            'axes_labels': axes_labels,
        }

    @staticmethod
    def _resolve_x_axis(expt_type: object, x: object) -> tuple:
        """
        Determine the x-axis type from experiment metadata.

        Parameters
        ----------
        expt_type : object
            Experiment type with sample_form, scattering_type, and
            beam_mode enums.
        x : object
            Explicit x-axis type or ``None`` to auto-detect.

        Returns
        -------
        tuple
            Tuple of ``(x_axis, x_name, sample_form, scattering_type,
            beam_mode)``.
        """
        sample_form = expt_type.sample_form.value
        scattering_type = expt_type.scattering_type.value
        beam_mode = expt_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[sample_form, scattering_type, beam_mode] if x is None else x
        x_name = getattr(x_axis, 'value', x_axis)
        return x_axis, x_name, sample_form, scattering_type, beam_mode

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def x_min(self) -> float:
        """Minimum x-axis limit."""
        return self._x_min

    @x_min.setter
    def x_min(self, value: object) -> None:
        """
        Set the minimum x-axis limit.

        Parameters
        ----------
        value : object
            Minimum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_min = value
        else:
            self._x_min = DEFAULT_MIN

    @property
    def x_max(self) -> float:
        """Maximum x-axis limit."""
        return self._x_max

    @x_max.setter
    def x_max(self, value: object) -> None:
        """
        Set the maximum x-axis limit.

        Parameters
        ----------
        value : object
            Maximum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_max = value
        else:
            self._x_max = DEFAULT_MAX

    @property
    def height(self) -> int:
        """Plot height (rows for ASCII, pixels for Plotly)."""
        return self._height

    @height.setter
    def height(self, value: object) -> None:
        """
        Set plot height.

        Parameters
        ----------
        value : object
            Height value or ``None`` to reset to default.
        """
        if value is not None:
            self._height = value
        else:
            self._height = DEFAULT_HEIGHT

    # ------------------------------------------------------------------
    #  Public methods
    # ------------------------------------------------------------------

    def show_config(self) -> None:
        """Display the current plotting configuration."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [
            ['Plotting engine', self.engine],
            ['x-axis limits', f'[{self.x_min}, {self.x_max}]'],
            ['Chart height', self.height],
        ]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        console.paragraph('Current plotter configuration')
        TableRenderer.get().render(df)

    def plot_meas(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
    ) -> None:
        """
        Plot measured diffraction data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        self._plot_meas_data(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            x=x,
        )

    def plot_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
    ) -> None:
        """
        Plot calculated diffraction pattern for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        self._plot_calc_data(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            x=x,
        )

    def plot_meas_vs_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        show_residual: bool = False,
        x: object | None = None,
    ) -> None:
        """
        Plot measured vs calculated data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        show_residual : bool, default=False
            When ``True``, include the residual (difference) curve.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        self._plot_meas_vs_calc_data(
            experiment,
            expt_name,
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            x=x,
        )

    def plot_param_series(
        self,
        param: object,
        versus: object | None = None,
    ) -> None:
        """
        Plot a parameter's value across sequential fit results.

        When a ``results.csv`` file exists in the project's
        ``analysis/`` directory, data is read from CSV.  Otherwise,
        falls back to in-memory parameter snapshots (produced by
        ``fit()`` in single mode).

        Parameters
        ----------
        param : object
            Parameter descriptor whose ``unique_name`` identifies the
            values to plot.
        versus : object | None, default=None
            A diffrn descriptor (e.g.
            ``expt.diffrn.ambient_temperature``) whose value is used as
            the x-axis for each experiment.  When ``None``, the
            experiment sequence number is used instead.
        """
        unique_name = param.unique_name

        # Try CSV first (produced by fit_sequential or future fit)
        csv_path = None
        if self._project.info.path is not None:
            candidate = pathlib.Path(self._project.info.path) / 'analysis' / 'results.csv'
            if candidate.is_file():
                csv_path = str(candidate)

        if csv_path is not None:
            self._plot_param_series_from_csv(
                csv_path=csv_path,
                unique_name=unique_name,
                param_descriptor=param,
                versus_descriptor=versus,
            )
        else:
            # Fallback: in-memory snapshots from fit() single mode
            versus_name = versus.name if versus is not None else None
            self._plot_param_series_from_snapshots(
                unique_name,
                versus_name,
                self._project.experiments,
                self._project.analysis._parameter_snapshots,
            )

    def plot_param_correlations(
        self,
        threshold: float | None = DEFAULT_CORRELATION_THRESHOLD,
        show_diagonal: bool = False,
        triangle: str = 'lower',
        precision: int = 2,
    ) -> None:
        """
        Plot the parameter correlation matrix from the latest fit.

        The matrix is taken from ``project.analysis.fit_results``. When
        the active engine is Plotly, an interactive heatmap is shown.
        Otherwise, a rounded correlation table is rendered.

        Parameters
        ----------
        threshold : float | None, default=DEFAULT_CORRELATION_THRESHOLD
            Minimum absolute off-diagonal correlation required for a
            parameter to be shown. Parameters are kept only if they
            participate in at least one pair with ``abs(correlation) >=
            threshold``. Set to ``None`` or ``0`` to show the full
            matrix.
        show_diagonal : bool, default=False
            Whether to show self-correlations on the diagonal. The
            default hides them because they are always ``1`` and do not
            add information.
        triangle : str, default='lower'
            Which half of the symmetric matrix to show. Supported values
            are ``'lower'``, ``'upper'``, and ``'full'``.
        precision : int, default=2
            Number of decimal places to show in the table fallback.
        """
        corr_df = self._get_param_correlation_dataframe()
        if corr_df is None:
            return

        corr_df = self._filter_correlation_dataframe(corr_df, threshold=threshold)
        if corr_df is None:
            return

        corr_df = self._mask_correlation_triangle(
            corr_df,
            triangle=triangle,
            show_diagonal=show_diagonal,
        )
        title = 'Refined parameter correlation matrix'
        if threshold is not None and threshold > 0:
            title += f' with |correlation| >= {threshold:.2f}'

        is_plotly = self._engine == PlotterEngineEnum.PLOTLY.value and isinstance(
            self._backend, PlotlyPlotter
        )
        display_corr_df, row_numbers, col_numbers = self._trim_correlation_display_dataframe(
            corr_df,
            triangle=triangle,
            show_diagonal=show_diagonal,
            preserve_all_rows=not is_plotly,
        )

        if is_plotly:
            self._plot_correlation_heatmap(
                display_corr_df,
                title,
                threshold=threshold,
                precision=precision,
            )
            return

        console.paragraph(title)
        TableRenderer.get().render(
            self._format_correlation_table_dataframe(
                display_corr_df,
                row_numbers=row_numbers,
                col_numbers=col_numbers,
                threshold=threshold,
                precision=precision,
            )
        )

    @staticmethod
    def _filter_correlation_dataframe(
        corr_df: pd.DataFrame,
        threshold: float | None,
    ) -> pd.DataFrame | None:
        """
        Filter a correlation matrix to only strongly correlated params.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.
        threshold : float | None
            Absolute-correlation cutoff. ``None`` or ``0`` keeps all
            parameters.

        Returns
        -------
        pd.DataFrame | None
            Filtered square matrix, or ``None`` if no off-diagonal
            correlations meet the cutoff.

        Raises
        ------
        ValueError
            If *threshold* is outside ``[0, 1]``.
        """
        if threshold is None or threshold <= 0:
            return corr_df
        if threshold > 1:
            msg = 'Correlation threshold must be between 0 and 1.'
            raise ValueError(msg)

        abs_corr = np.abs(corr_df.to_numpy(copy=True))
        np.fill_diagonal(abs_corr, 0.0)
        keep_mask = (abs_corr >= threshold).any(axis=0)

        if not keep_mask.any():
            log.warning(f'No parameter pairs with |correlation| >= {threshold:.2f} were found.')
            return None

        labels = corr_df.index[keep_mask]
        return corr_df.loc[labels, labels]

    @staticmethod
    def _mask_correlation_triangle(
        corr_df: pd.DataFrame,
        triangle: str,
        show_diagonal: bool,
    ) -> pd.DataFrame:
        """
        Mask the unused half of the symmetric correlation matrix.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.
        triangle : str
            Which part of the matrix to keep: ``'lower'``, ``'upper'``,
            or ``'full'``.
        show_diagonal : bool
            Whether to keep the diagonal values visible.

        Returns
        -------
        pd.DataFrame
            Correlation matrix with unused cells masked.

        Raises
        ------
        ValueError
            If *triangle* is unsupported.
        """
        if triangle not in {'lower', 'upper', 'full'}:
            msg = "Correlation triangle must be 'lower', 'upper', or 'full'."
            raise ValueError(msg)

        masked_values = corr_df.to_numpy(copy=True)
        k = 1 if show_diagonal else 0

        if triangle == 'lower':
            mask = np.triu(np.ones_like(masked_values, dtype=bool), k=k)
            masked_values[mask] = np.nan
        elif triangle == 'upper':
            mask = np.tril(np.ones_like(masked_values, dtype=bool), k=-k)
            masked_values[mask] = np.nan
        elif not show_diagonal:
            diag_idx = np.diag_indices_from(masked_values)
            masked_values[diag_idx] = np.nan

        return pd.DataFrame(masked_values, index=corr_df.index, columns=corr_df.columns)

    @staticmethod
    def _trim_correlation_display_dataframe(
        corr_df: pd.DataFrame,
        triangle: str,
        show_diagonal: bool,
        preserve_all_rows: bool,
    ) -> tuple[pd.DataFrame, list[int], list[int]]:
        """
        Trim empty outer rows/columns from triangle views.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Masked correlation matrix.
        triangle : str
            Which triangle is shown.
        show_diagonal : bool
            Whether diagonal values are visible.
        preserve_all_rows : bool
            Whether to keep the full row list so row labels continue to
            identify all numeric column headers in tabular output.

        Returns
        -------
        tuple[pd.DataFrame, list[int], list[int]]
            Display matrix plus 1-based parameter numbers for the kept
            rows and columns.
        """
        num_rows, num_cols = corr_df.shape
        row_numbers = list(range(1, num_rows + 1))
        col_numbers = list(range(1, num_cols + 1))

        if show_diagonal or triangle == 'full' or min(num_rows, num_cols) <= 1:
            return corr_df, row_numbers, col_numbers

        if triangle == 'lower':
            if preserve_all_rows:
                return corr_df.iloc[:, :-1], row_numbers, col_numbers[:-1]
            return corr_df.iloc[1:, :-1], row_numbers[1:], col_numbers[:-1]
        if triangle == 'upper':
            if preserve_all_rows:
                return corr_df.iloc[:, 1:], row_numbers, col_numbers[1:]
            return corr_df.iloc[:-1, 1:], row_numbers[:-1], col_numbers[1:]

        return corr_df, row_numbers, col_numbers

    def _get_param_correlation_dataframe(self) -> pd.DataFrame | None:
        """
        Return the correlation matrix for the latest fit.

        Returns
        -------
        pd.DataFrame | None
            Square correlation matrix labeled by parameter unique names,
            or ``None`` if unavailable.
        """
        result = self._get_fit_result_for_correlation()
        if result is None:
            return None
        raw_result, var_names, fit_results = result

        covar = getattr(raw_result, 'covar', None)
        if covar is not None:
            return self._correlation_from_covariance(covar, var_names, fit_results.parameters)

        corr_df = self._get_param_correlation_dataframe_from_engine_params(
            raw_result=raw_result,
            parameters=fit_results.parameters,
        )
        if corr_df is not None:
            return corr_df

        log.warning(
            'Correlation matrix is unavailable for this fit. '
            'Use the lmfit minimizer and ensure covariance estimation succeeds.'
        )
        return None

    def _get_fit_result_for_correlation(
        self,
    ) -> tuple[object, list[str], object] | None:
        """
        Validate and return the raw fit result for correlation.

        Returns
        -------
        tuple[object, list[str], object] | None
            A tuple of ``(raw_result, var_names, fit_results)`` when all
            required data is present, or ``None`` otherwise.
        """
        if self._project is None:
            log.warning('Plotter is not attached to a project.')
            return None

        fit_results = getattr(self._project.analysis, 'fit_results', None)
        if fit_results is None:
            log.warning('No fit results available. Run fit() first.')
            return None

        raw_result = getattr(fit_results, 'engine_result', None)
        if raw_result is None:
            log.warning('No raw fit result available. Correlation matrix cannot be plotted.')
            return None

        var_names = getattr(raw_result, 'var_names', None)
        if not var_names:
            log.warning('Fit result does not expose variable names for a correlation matrix.')
            return None

        return raw_result, var_names, fit_results

    @staticmethod
    def _correlation_from_covariance(
        covar: object,
        var_names: list[str],
        parameters: list[object],
    ) -> pd.DataFrame | None:
        """
        Convert a covariance matrix to a correlation DataFrame.

        Parameters
        ----------
        covar : object
            Raw covariance matrix from the fit result.
        var_names : list[str]
            Minimizer variable names.
        parameters : list[object]
            Fitted parameter descriptors.

        Returns
        -------
        pd.DataFrame | None
            Correlation matrix, or ``None`` if the covariance is
            invalid.
        """
        covar_array = np.asarray(covar, dtype=float)
        if covar_array.ndim != EXPECTED_COVAR_NDIM or covar_array.shape[0] != covar_array.shape[1]:
            log.warning('Fit result returned an invalid covariance matrix.')
            return None
        if covar_array.shape[0] != len(var_names):
            log.warning('Covariance matrix size does not match the fitted parameter list.')
            return None

        sigma = np.sqrt(np.diag(covar_array))
        with np.errstate(divide='ignore', invalid='ignore'):
            corr = covar_array / np.outer(sigma, sigma)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(corr, 1.0)

        labels = Plotter._get_correlation_labels(parameters, var_names)
        return pd.DataFrame(corr, index=labels, columns=labels)

    @staticmethod
    def _get_correlation_labels(
        parameters: list[object],
        var_names: list[str],
    ) -> list[str]:
        """
        Map minimizer variable names to readable parameter labels.

        Parameters
        ----------
        parameters : list[object]
            Fitted parameter descriptors.
        var_names : list[str]
            Minimizer variable names from the engine result.

        Returns
        -------
        list[str]
            Labels for the correlation matrix axes.
        """
        labels_by_uid = {
            getattr(param, '_minimizer_uid', ''): getattr(
                param, 'unique_name', getattr(param, 'name', '')
            )
            for param in parameters
        }
        return [labels_by_uid.get(name, name) for name in var_names]

    def _get_param_correlation_dataframe_from_engine_params(
        self,
        raw_result: object,
        parameters: list[object],
    ) -> pd.DataFrame | None:
        """
        Reconstruct a correlation matrix from engine parameter metadata.

        This is a fallback for backends that populate per-parameter
        correlation coefficients but do not expose a covariance matrix.

        Parameters
        ----------
        raw_result : object
            Backend-specific fit result.
        parameters : list[object]
            Fitted parameter descriptors.

        Returns
        -------
        pd.DataFrame | None
            Correlation matrix labeled by readable parameter names, or
            ``None`` if no correlation coefficients are available.
        """
        engine_params = getattr(raw_result, 'params', None)
        var_names = getattr(raw_result, 'var_names', None)
        if engine_params is None or not var_names:
            return None

        corr = np.eye(len(var_names), dtype=float)
        indices = {name: idx for idx, name in enumerate(var_names)}
        found_corr = False

        for name, idx in indices.items():
            engine_param = engine_params.get(name)
            param_corr = getattr(engine_param, 'correl', None)
            if not param_corr:
                continue

            for other_name, value in param_corr.items():
                other_idx = indices.get(other_name)
                if other_idx is None:
                    continue
                corr_value = float(value)
                corr[idx, other_idx] = corr_value
                corr[other_idx, idx] = corr_value
                found_corr = True

        if not found_corr:
            return None

        labels = self._get_correlation_labels(parameters, var_names)
        return pd.DataFrame(corr, index=labels, columns=labels)

    def _plot_correlation_heatmap(
        self,
        corr_df: pd.DataFrame,
        title: str,
        threshold: float | None,
        precision: int,
    ) -> None:
        """
        Delegate correlation heatmap rendering to the Plotly backend.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.
        title : str
            Figure title.
        threshold : float | None
            Absolute-correlation cutoff used for value labels.
        precision : int
            Number of decimals to show in plot labels and hover text.
        """
        self._backend.plot_correlation_heatmap(
            corr_df,
            title,
            threshold=threshold,
            precision=precision,
        )

    @staticmethod
    def _format_correlation_table_dataframe(
        corr_df: pd.DataFrame,
        row_numbers: list[int],
        col_numbers: list[int],
        threshold: float | None,
        precision: int,
    ) -> pd.DataFrame:
        """
        Format a correlation matrix for TableRenderer.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Correlation matrix labeled by parameter name.
        row_numbers : list[int]
            1-based parameter numbers for displayed rows.
        col_numbers : list[int]
            1-based parameter numbers for displayed columns.
        threshold : float | None
            Absolute-correlation cutoff used to blank low-magnitude
            cells in the rendered table. ``None`` or ``0`` keeps all
            non-masked values.
        precision : int
            Number of decimals to show in the rendered values.

        Returns
        -------
        pd.DataFrame
            DataFrame with MultiIndex columns and default numeric index,
            suitable for :class:`TableRenderer`. Correlation columns use
            1-based numeric headers so they line up with the numbered
            parameter rows in terminal output.
        """
        rounded = corr_df.round(precision)
        cell_width = max(
            len(str(max(col_numbers, default=0))),
            len(f'{-1.0:.{precision}f}'),
        )
        headers = [('parameter', 'left')]
        headers.extend((str(index).rjust(cell_width), 'right') for index in col_numbers)

        rows = []
        for label, values in rounded.iterrows():
            row_values = []
            for value in values.tolist():
                should_blank = pd.isna(value) or (
                    threshold is not None and threshold > 0 and abs(float(value)) < threshold
                )
                if should_blank:
                    row_values.append('')
                else:
                    row_values.append(f'{float(value):>{cell_width}.{precision}f}')
            rows.append([label, *row_values])

        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        df.index = pd.Index([row_number - 1 for row_number in row_numbers])
        return df

    def _plot_meas_data(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object = None,
        x_max: object = None,
        x: object = None,
    ) -> None:
        """
        Plot measured pattern using the current engine.

        Parameters
        ----------
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``meas`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        x : object, default=None
            X-axis type. If ``None``, auto-detected from beam mode.
        """
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
        )
        if ctx is None:
            return

        if pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        y_meas = self._filtered_y_array(
            pattern.intensity_meas, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=[y_meas],
            labels=['meas'],
            axes_labels=ctx['axes_labels'],
            title=f"Measured data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def _plot_calc_data(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object = None,
        x_max: object = None,
        x: object = None,
    ) -> None:
        """
        Plot calculated pattern using the current engine.

        Parameters
        ----------
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``calc`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        x : object, default=None
            X-axis type. If ``None``, auto-detected from beam mode.
        """
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
        )
        if ctx is None:
            return

        if pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return
        y_calc = self._filtered_y_array(
            pattern.intensity_calc, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=[y_calc],
            labels=['calc'],
            axes_labels=ctx['axes_labels'],
            title=f"Calculated data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def _plot_meas_vs_calc_data(
        self,
        experiment: object,
        expt_name: str,
        x_min: object = None,
        x_max: object = None,
        show_residual: bool = False,
        x: object = None,
    ) -> None:
        """
        Plot measured and calculated series and optional residual.

        Supports both powder and single crystal data with a unified API.

        For powder diffraction: - x='two_theta', 'time_of_flight', or
        'd_spacing' - Auto-detected from beam mode if not specified

        For single crystal diffraction: - x='intensity_calc' (default):
        scatter plot - x='d_spacing' or 'sin_theta_over_lambda': line
        plot

        Parameters
        ----------
        experiment : object
            Experiment instance with ``.data`` and ``.type`` attributes.
        expt_name : str
            Experiment name for the title.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        show_residual : bool, default=False
            If ``True``, add residual series (powder only).
        x : object, default=None
            X-axis type. If ``None``, auto-detected from sample form and
            beam mode.
        """
        pattern = experiment.data
        expt_type = experiment.type

        x_axis, _, sample_form, scattering_type, _ = self._resolve_x_axis(expt_type, x)

        # Validate required data (before x-array check, matching
        # original behavior for plot_meas_vs_calc)
        if pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        if pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        title = f"Measured vs Calculated data for experiment 🔬 '{expt_name}'"

        # Single crystal scatter plot (I²calc vs I²meas)
        if x_axis in {XAxisType.INTENSITY_CALC, 'intensity_calc'}:
            axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)

            if pattern.intensity_meas_su is None:
                log.warning(f'No measurement uncertainties for experiment {expt_name}')
                meas_su = np.zeros_like(pattern.intensity_meas)
            else:
                meas_su = pattern.intensity_meas_su

            self._backend.plot_single_crystal(
                x_calc=pattern.intensity_calc,
                y_meas=pattern.intensity_meas,
                y_meas_su=meas_su,
                axes_labels=axes_labels,
                title=f"Measured vs Calculated data for experiment 🔬 '{expt_name}'",
                height=self.height,
            )
            return

        # Line plot (PD or SC with d_spacing/sin_theta_over_lambda)
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
        )
        if ctx is None:
            return

        y_series = []
        y_labels = []
        y_meas = self._filtered_y_array(
            pattern.intensity_meas, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        y_series.append(y_meas)
        y_labels.append('meas')
        y_calc = self._filtered_y_array(
            pattern.intensity_calc, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        y_series.append(y_calc)
        y_labels.append('calc')
        if show_residual:
            y_series.append(y_meas - y_calc)
            y_labels.append('resid')

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=y_series,
            labels=y_labels,
            axes_labels=ctx['axes_labels'],
            title=title,
            height=self.height,
        )

    def _plot_param_series_from_csv(
        self,
        csv_path: str,
        unique_name: str,
        param_descriptor: object,
        versus_descriptor: object | None = None,
    ) -> None:
        """
        Plot a parameter's value across sequential fit results.

        Reads data from the CSV file at *csv_path*.  The y-axis values
        come from the column named *unique_name*, uncertainties from
        ``{unique_name}.uncertainty``.  When *versus_descriptor* is
        provided, the x-axis uses the corresponding ``diffrn.{name}``
        column; otherwise the row index is used.

        Axis labels are derived from the live descriptor objects
        (*param_descriptor* and *versus_descriptor*), which carry
        ``.description`` and ``.units`` attributes.

        Parameters
        ----------
        csv_path : str
            Path to the ``results.csv`` file.
        unique_name : str
            Unique name of the parameter to plot (CSV column key).
        param_descriptor : object
            The live parameter descriptor (for axis label / units).
        versus_descriptor : object | None, default=None
            A diffrn descriptor whose ``.name`` maps to a
            ``diffrn.{name}`` CSV column.  ``None`` → use row index.
        """
        df = pd.read_csv(csv_path)

        if unique_name not in df.columns:
            log.warning(
                f"Parameter '{unique_name}' not found in CSV columns. "
                f'Available: {list(df.columns)}'
            )
            return

        y = df[unique_name].astype(float).tolist()
        uncert_col = f'{unique_name}.uncertainty'
        sy = df[uncert_col].astype(float).tolist() if uncert_col in df.columns else [0.0] * len(y)

        # X-axis: diffrn column or row index
        versus_name = versus_descriptor.name if versus_descriptor is not None else None
        diffrn_col = f'diffrn.{versus_name}' if versus_name else None

        if diffrn_col and diffrn_col in df.columns:
            x = pd.to_numeric(df[diffrn_col], errors='coerce').tolist()
            x_label = getattr(versus_descriptor, 'description', None) or versus_name
            if hasattr(versus_descriptor, 'units') and versus_descriptor.units:
                x_label = f'{x_label} ({versus_descriptor.units})'
        else:
            x = list(range(1, len(y) + 1))
            x_label = 'Experiment No.'

        # Y-axis label from descriptor
        param_units = getattr(param_descriptor, 'units', '')
        y_label = f'Parameter value ({param_units})' if param_units else 'Parameter value'

        title = f"Parameter '{unique_name}' across fit results"

        self._backend.plot_scatter(
            x=x,
            y=y,
            sy=sy,
            axes_labels=[x_label, y_label],
            title=title,
            height=self.height,
        )

    def _plot_param_series_from_snapshots(
        self,
        csv_path: str,
        unique_name: str,
        param_descriptor: object,
        versus_descriptor: object | None = None,
    ) -> None:
        """
        Plot a parameter's value across sequential fit results.

        Reads data from the CSV file at *csv_path*.  The y-axis values
        come from the column named *unique_name*, uncertainties from
        ``{unique_name}.uncertainty``.  When *versus_descriptor* is
        provided, the x-axis uses the corresponding ``diffrn.{name}``
        column; otherwise the row index is used.

        Axis labels are derived from the live descriptor objects
        (*param_descriptor* and *versus_descriptor*), which carry
        ``.description`` and ``.units`` attributes.

        Parameters
        ----------
        csv_path : str
            Path to the ``results.csv`` file.
        unique_name : str
            Unique name of the parameter to plot (CSV column key).
        param_descriptor : object
            The live parameter descriptor (for axis label / units).
        versus_descriptor : object | None, default=None
            A diffrn descriptor whose ``.name`` maps to a
            ``diffrn.{name}`` CSV column.  ``None`` → use row index.
        """
        df = pd.read_csv(csv_path)

        if unique_name not in df.columns:
            log.warning(
                f"Parameter '{unique_name}' not found in CSV columns. "
                f'Available: {list(df.columns)}'
            )
            return

        y = df[unique_name].astype(float).tolist()
        uncert_col = f'{unique_name}.uncertainty'
        sy = df[uncert_col].astype(float).tolist() if uncert_col in df.columns else [0.0] * len(y)

        # X-axis: diffrn column or row index
        versus_name = versus_descriptor.name if versus_descriptor is not None else None
        diffrn_col = f'diffrn.{versus_name}' if versus_name else None

        if diffrn_col and diffrn_col in df.columns:
            x = pd.to_numeric(df[diffrn_col], errors='coerce').tolist()
            x_label = getattr(versus_descriptor, 'description', None) or versus_name
            if hasattr(versus_descriptor, 'units') and versus_descriptor.units:
                x_label = f'{x_label} ({versus_descriptor.units})'
        else:
            x = list(range(1, len(y) + 1))
            x_label = 'Experiment No.'

        # Y-axis label from descriptor
        param_units = getattr(param_descriptor, 'units', '')
        y_label = f'Parameter value ({param_units})' if param_units else 'Parameter value'

        title = f"Parameter '{unique_name}' across fit results"

        self._backend.plot_scatter(
            x=x,
            y=y,
            sy=sy,
            axes_labels=[x_label, y_label],
            title=title,
            height=self.height,
        )

    def plot_param_series_from_snapshots(
        self,
        unique_name: str,
        versus_name: str | None,
        experiments: object,
        parameter_snapshots: dict[str, dict[str, dict]],
    ) -> None:
        """
        Plot a parameter's value from in-memory snapshots.

        This is a backward-compatibility method used when no CSV file is
        available (e.g. after ``fit()`` in single mode, before PR 13
        adds CSV output to the existing fit loop).

        Parameters
        ----------
        unique_name : str
            Unique name of the parameter to plot.
        versus_name : str | None
            Name of the diffrn descriptor for the x-axis.
        experiments : object
            Experiments collection for accessing diffrn conditions.
        parameter_snapshots : dict[str, dict[str, dict]]
            Per-experiment parameter value snapshots.
        """
        x = []
        y = []
        sy = []
        axes_labels = []
        title = ''

        for idx, expt_name in enumerate(parameter_snapshots, start=1):
            experiment = experiments[expt_name]
            diffrn = experiment.diffrn

            x_axis_param = self._resolve_diffrn_descriptor(diffrn, versus_name)

            if x_axis_param is not None and x_axis_param.value is not None:
                value = x_axis_param.value
            else:
                value = idx
            x.append(value)

            param_data = parameter_snapshots[expt_name][unique_name]
            y.append(param_data['value'])
            sy.append(param_data['uncertainty'])

            if x_axis_param is not None:
                axes_labels = [
                    x_axis_param.description or x_axis_param.name,
                    f'Parameter value ({param_data["units"]})',
                ]
            else:
                axes_labels = [
                    'Experiment No.',
                    f'Parameter value ({param_data["units"]})',
                ]

            title = f"Parameter '{unique_name}' across fit results"

        self._backend.plot_scatter(
            x=x,
            y=y,
            sy=sy,
            axes_labels=axes_labels,
            title=title,
            height=self.height,
        )

    @staticmethod
    def _resolve_diffrn_descriptor(
        diffrn: object,
        name: str | None,
    ) -> object | None:
        """
        Return the diffrn descriptor matching *name*, or ``None``.

        Parameters
        ----------
        diffrn : object
            The diffrn category of an experiment.
        name : str | None
            Descriptor name (e.g. ``'ambient_temperature'``).

        Returns
        -------
        object | None
            The matching ``NumericDescriptor``, or ``None`` when *name*
            is ``None`` or unrecognised.
        """
        if name is None:
            return None
        if name == 'ambient_temperature':
            return diffrn.ambient_temperature
        if name == 'ambient_pressure':
            return diffrn.ambient_pressure
        if name == 'ambient_magnetic_field':
            return diffrn.ambient_magnetic_field
        if name == 'ambient_electric_field':
            return diffrn.ambient_electric_field
        return None


class PlotterFactory(RendererFactoryBase):
    """Factory for plotter implementations."""

    @classmethod
    def _registry(cls) -> dict:
        return {
            PlotterEngineEnum.ASCII.value: {
                'description': PlotterEngineEnum.ASCII.description(),
                'class': AsciiPlotter,
            },
            PlotterEngineEnum.PLOTLY.value: {
                'description': PlotterEngineEnum.PLOTLY.description(),
                'class': PlotlyPlotter,
            },
        }
