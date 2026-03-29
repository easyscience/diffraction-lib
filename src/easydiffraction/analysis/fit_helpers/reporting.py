# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List
from typing import Optional

from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor_squared
from easydiffraction.analysis.fit_helpers.metrics import calculate_rb_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_weighted_r_factor
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class FitResults:
    """
    Container for results of a single optimization run.

    Holds success flag, chi-square metrics, iteration counts, timing,
    and parameter objects. Provides a printer to summarize key
    indicators and a table of fitted parameters.
    """

    def __init__(
        self,
        success: bool = False,
        parameters: Optional[List[object]] = None,
        chi_square: Optional[float] = None,
        reduced_chi_square: Optional[float] = None,
        message: str = '',
        iterations: int = 0,
        engine_result: Optional[object] = None,
        starting_parameters: Optional[List[object]] = None,
        fitting_time: Optional[float] = None,
        **kwargs: object,
    ) -> None:
        """
        Initialize FitResults with the given parameters.

        Parameters
        ----------
        success : bool, default=False
            Indicates if the fit was successful.
        parameters : Optional[List[object]], default=None
            List of parameters used in the fit.
        chi_square : Optional[float], default=None
            Chi-square value of the fit.
        reduced_chi_square : Optional[float], default=None
            Reduced chi-square value of the fit.
        message : str, default=''
            Message related to the fit.
        iterations : int, default=0
            Number of iterations performed.
        engine_result : Optional[object], default=None
            Result from the fitting engine.
        starting_parameters : Optional[List[object]], default=None
            Initial parameters for the fit.
        fitting_time : Optional[float], default=None
            Time taken for the fitting process.
        **kwargs : object
            Additional engine-specific fields. If ``redchi`` is provided
            and ``reduced_chi_square`` is not set, it is used as the
            reduced chi-square value.
        """
        self.success: bool = success
        self.parameters: List[object] = parameters if parameters is not None else []
        self.chi_square: Optional[float] = chi_square
        self.reduced_chi_square: Optional[float] = reduced_chi_square
        self.message: str = message
        self.iterations: int = iterations
        self.engine_result: Optional[object] = engine_result
        self.result: Optional[object] = None
        self.starting_parameters: List[object] = (
            starting_parameters if starting_parameters is not None else []
        )
        self.fitting_time: Optional[float] = fitting_time
        self.final_parameters_dict: dict[str, object] = {}

        if 'redchi' in kwargs and self.reduced_chi_square is None:
            self.reduced_chi_square = kwargs.get('redchi')

        for parameter in self.parameters:
            self.final_parameters_dict[parameter.unique_name] = {
                'value': parameter.value,
                'uncertainty': parameter.uncertainty,
                'units': parameter.units,
            }

        for key, value in kwargs.items():
            setattr(self, key, value)

    def display_results(
        self,
        y_obs: Optional[List[float]] = None,
        y_calc: Optional[List[float]] = None,
        y_err: Optional[List[float]] = None,
        f_obs: Optional[List[float]] = None,
        f_calc: Optional[List[float]] = None,
    ) -> None:
        """
        Render a human-readable summary of the fit.

        Parameters
        ----------
        y_obs : Optional[List[float]], default=None
            Observed intensities for pattern R-factor metrics.
        y_calc : Optional[List[float]], default=None
            Calculated intensities for pattern R-factor metrics.
        y_err : Optional[List[float]], default=None
            Standard deviations of observed intensities for wR.
        f_obs : Optional[List[float]], default=None
            Observed structure-factor magnitudes for Bragg R.
        f_calc : Optional[List[float]], default=None
            Calculated structure-factor magnitudes for Bragg R.
        """
        status_icon = '✅' if self.success else '❌'
        rf = rf2 = wr = br = None
        if y_obs is not None and y_calc is not None:
            rf = calculate_r_factor(y_obs, y_calc) * 100
            rf2 = calculate_r_factor_squared(y_obs, y_calc) * 100
        if y_obs is not None and y_calc is not None and y_err is not None:
            wr = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
        if f_obs is not None and f_calc is not None:
            br = calculate_rb_factor(f_obs, f_calc) * 100

        console.paragraph('Fit results')
        console.print(f'{status_icon} Success: {self.success}')
        console.print(f'⏱️ Fitting time: {self.fitting_time:.2f} seconds')
        console.print(f'📏 Goodness-of-fit (reduced χ²): {self.reduced_chi_square:.2f}')
        if rf is not None:
            console.print(f'📏 R-factor (Rf): {rf:.2f}%')
        if rf2 is not None:
            console.print(f'📏 R-factor squared (Rf²): {rf2:.2f}%')
        if wr is not None:
            console.print(f'📏 Weighted R-factor (wR): {wr:.2f}%')
        if br is not None:
            console.print(f'📏 Bragg R-factor (BR): {br:.2f}%')
        console.print('📈 Fitted parameters:')

        headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'start',
            'fitted',
            'uncertainty',
            'units',
            'change',
        ]
        alignments = [
            'left',
            'left',
            'left',
            'left',
            'right',
            'right',
            'right',
            'left',
            'right',
        ]

        rows = []
        for param in self.parameters:
            datablock_entry_name = (
                param._identity.datablock_entry_name
            )  # getattr(param, 'datablock_name', 'N/A')
            category_code = param._identity.category_code  # getattr(param, 'category_key', 'N/A')
            category_entry_name = (
                param._identity.category_entry_name or ''
            )  # getattr(param, 'category_entry_name', 'N/A')
            name = getattr(param, 'name', 'N/A')
            start = (
                f'{getattr(param, "_fit_start_value", "N/A"):.4f}'
                if param._fit_start_value is not None
                else 'N/A'
            )
            fitted = f'{param.value:.4f}' if param.value is not None else 'N/A'
            uncertainty = f'{param.uncertainty:.4f}' if param.uncertainty is not None else 'N/A'
            units = getattr(param, 'units', 'N/A')

            if param._fit_start_value and param.value:
                change = ((param.value - param._fit_start_value) / param._fit_start_value) * 100
                arrow = '↑' if change > 0 else '↓'
                relative_change = f'{abs(change):.2f} % {arrow}'
            else:
                relative_change = 'N/A'

            rows.append([
                datablock_entry_name,
                category_code,
                category_entry_name,
                name,
                start,
                fitted,
                uncertainty,
                units,
                relative_change,
            ])

        render_table(
            columns_headers=headers,
            columns_alignment=alignments,
            columns_data=rows,
        )
