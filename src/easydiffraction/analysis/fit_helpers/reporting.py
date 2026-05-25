# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor_squared
from easydiffraction.analysis.fit_helpers.metrics import calculate_rb_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_weighted_r_factor
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import print_metrics_table
from easydiffraction.utils.utils import print_table_footnote
from easydiffraction.utils.utils import render_table


def _overall_status_row_label(status: str) -> str:
    """Return the metric label for an overall status row."""
    icon = '✅' if status == 'success' else '❌'
    return f'{icon} Overall status'


class FitResults:
    """
    Container for results of a single optimization run.

    Holds success flag, chi-square metrics, iteration counts, timing,
    and parameter objects. Provides a printer to summarize key
    indicators and a table of fitted parameters.
    """

    def __init__(
        self,
        *,
        success: bool = False,
        parameters: list[object] | None = None,
        reduced_chi_square: float | None = None,
        engine_result: object | None = None,
        starting_parameters: list[object] | None = None,
        fitting_time: float | None = None,
        **kwargs: object,
    ) -> None:
        """
        Initialize FitResults with the given parameters.

        Parameters
        ----------
        success : bool, default=False
            Indicates if the fit was successful.
        parameters : list[object] | None, default=None
            List of parameters used in the fit.
        reduced_chi_square : float | None, default=None
            Reduced chi-square value of the fit.
        engine_result : object | None, default=None
            Result from the fitting engine.
        starting_parameters : list[object] | None, default=None
            Initial parameters for the fit.
        fitting_time : float | None, default=None
            Time taken for the fitting process.
        **kwargs : object
            Additional engine-specific fields. If ``redchi`` is provided
            and ``reduced_chi_square`` is not set, it is used as the
            reduced chi-square value.
        """
        self.success: bool = success
        self.parameters: list[object] = parameters if parameters is not None else []
        self.chi_square: float | None = None
        self.reduced_chi_square: float | None = reduced_chi_square
        self.message: str = ''
        self.iterations: int = 0
        self.engine_result: object | None = engine_result
        self.result: object | None = None
        self.starting_parameters: list[object] = (
            starting_parameters if starting_parameters is not None else []
        )
        self.fitting_time: float | None = fitting_time
        self.minimizer_type: str | None = None

        if 'redchi' in kwargs and self.reduced_chi_square is None:
            self.reduced_chi_square = kwargs.get('redchi')

        for key, value in kwargs.items():
            setattr(self, key, value)

    def display_results(
        self,
        y_obs: list[float] | None = None,
        y_calc: list[float] | None = None,
        y_err: list[float] | None = None,
        f_obs: list[float] | None = None,
        f_calc: list[float] | None = None,
    ) -> None:
        """
        Render a human-readable summary of the fit.

        Parameters
        ----------
        y_obs : list[float] | None, default=None
            Observed intensities for pattern R-factor metrics.
        y_calc : list[float] | None, default=None
            Calculated intensities for pattern R-factor metrics.
        y_err : list[float] | None, default=None
            Standard deviations of observed intensities for wR.
        f_obs : list[float] | None, default=None
            Observed structure-factor magnitudes for Bragg R.
        f_calc : list[float] | None, default=None
            Calculated structure-factor magnitudes for Bragg R.
        """
        rf = rf2 = wr = br = None
        if y_obs is not None and y_calc is not None:
            rf = calculate_r_factor(y_obs, y_calc) * 100
            rf2 = calculate_r_factor_squared(y_obs, y_calc) * 100
        if y_obs is not None and y_calc is not None and y_err is not None:
            wr = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
        if f_obs is not None and f_calc is not None:
            br = calculate_rb_factor(f_obs, f_calc) * 100

        console.print('📋 Least-squares fit results:')
        print_metrics_table(self._build_fit_results_rows(rf=rf, rf2=rf2, wr=wr, br=br))

        console.print('📈 Refined parameters:')

        headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'units',
            'start',
            'value',
            's.u.',
            'change',
        ]
        alignments = [
            'left',
            'left',
            'left',
            'left',
            'left',
            'right',
            'right',
            'right',
            'right',
        ]

        rows = [_build_parameter_row(p) for p in self.parameters]

        render_table(
            columns_headers=headers,
            columns_alignment=alignments,
            columns_data=rows,
        )

        print_table_footnote(_REFINED_PARAMETERS_FOOTNOTE)
        self._print_table_notes()

    def _build_fit_results_rows(
        self,
        *,
        rf: float | None,
        rf2: float | None,
        wr: float | None,
        br: float | None,
    ) -> list[list[str]]:
        """Return the rows for the 'Least-squares fit results' table."""
        rows: list[list[str]] = []
        if self.minimizer_type is not None:
            rows.append(['🧪 Minimizer', str(self.minimizer_type)])
        overall_status = 'success' if self.success else 'failed'
        rows.append([_overall_status_row_label(overall_status), overall_status])
        if self.fitting_time is not None:
            rows.append(['⏱️ Fitting time (seconds)', f'{self.fitting_time:.2f}'])
        if self.iterations:
            rows.append(['🔁 Iterations', str(self.iterations)])
        if self.reduced_chi_square is not None:
            rows.append(['📏 Goodness-of-fit (reduced χ²)', f'{self.reduced_chi_square:.2f}'])
        if rf is not None:
            rows.append(['📏 R-factor (Rf, %)', f'{rf:.2f}'])
        if rf2 is not None:
            rows.append(['📏 R-factor squared (Rf², %)', f'{rf2:.2f}'])
        if wr is not None:
            rows.append(['📏 Weighted R-factor (wR, %)', f'{wr:.2f}'])
        if br is not None:
            rows.append(['📏 Bragg R-factor (BR, %)', f'{br:.2f}'])
        return rows

    def _print_table_notes(self) -> None:
        """
        Print color-coded warnings below the refined parameters table.
        """
        notes: list[str] = []
        if any(getattr(p, '_outside_physical_limits', False) for p in self.parameters):
            notes.append(
                '⚠️ [red]Red value:[/red] outside expected physical limits '
                '(consider adding constraints)'
            )
        if any(_is_uncertainty_large(p) for p in self.parameters):
            notes.append(
                '⚠️ [red]Red s.u.:[/red] exceeds the refined value (consider adding constraints)'
            )
        if notes:
            console.small(*notes)


_REFINED_PARAMETERS_FOOTNOTE: list[tuple[str, str]] = [
    ('start', 'parameter value before refinement'),
    ('value', 'refined value from least-squares minimization'),
    ('s.u.', 'standard uncertainty (1σ), from the covariance matrix'),
    ('change', 'relative change from start, in %; ↑ = increase, ↓ = decrease'),
]


def _is_uncertainty_large(param: object) -> bool:
    """
    Return True when the uncertainty exceeds the absolute fitted value.

    Parameters
    ----------
    param : object
        Fitted parameter descriptor.

    Returns
    -------
    bool
        Whether the parameter is poorly constrained.
    """
    if param.uncertainty is None or param.value is None:
        return False
    abs_value = abs(param.value)
    if abs_value == 0:
        return param.uncertainty > 0
    return param.uncertainty > abs_value


def _build_parameter_row(param: object) -> list[str]:
    """
    Build a single table row for a fitted parameter.

    Parameters
    ----------
    param : object
        Fitted parameter descriptor.

    Returns
    -------
    list[str]
        Column values for the parameter row.
    """
    name = getattr(param, 'name', 'N/A')
    start = f'{param._fit_start_value:.4f}' if param._fit_start_value is not None else 'N/A'
    fitted = f'{param.value:.4f}' if param.value is not None else 'N/A'
    if getattr(param, '_outside_physical_limits', False):
        fitted = f'[red]{fitted}[/red]'
    uncertainty = f'{param.uncertainty:.4f}' if param.uncertainty is not None else 'N/A'
    if _is_uncertainty_large(param):
        uncertainty = f'[red]{uncertainty}[/red]'
    units = getattr(param, 'units', 'N/A')
    relative_change = _compute_relative_change(param)
    return [
        param._identity.datablock_entry_name,
        param._identity.category_code,
        param._identity.category_entry_name or '',
        name,
        units,
        start,
        fitted,
        uncertainty,
        relative_change,
    ]


def _compute_relative_change(param: object) -> str:
    """
    Compute percentage change between start and fitted values.

    Parameters
    ----------
    param : object
        Fitted parameter descriptor.

    Returns
    -------
    str
        Formatted change string or ``'N/A'``.
    """
    if not param._fit_start_value or not param.value:
        return 'N/A'
    change = ((param.value - param._fit_start_value) / param._fit_start_value) * 100
    arrow = '↑' if change > 0 else '↓'
    return f'{abs(change):.2f} % {arrow}'
