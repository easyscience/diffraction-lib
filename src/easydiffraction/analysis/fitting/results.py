from typing import Any
from typing import List
from typing import Optional

from easydiffraction import paragraph
from easydiffraction.analysis.fitting.metrics import calculate_r_factor
from easydiffraction.analysis.fitting.metrics import calculate_r_factor_squared
from easydiffraction.analysis.fitting.metrics import calculate_rb_factor
from easydiffraction.analysis.fitting.metrics import calculate_weighted_r_factor
from easydiffraction.utils.utils import render_table


class FitResults:
    def __init__(
        self,
        success: bool = False,
        parameters: Optional[List[Any]] = None,
        chi_square: Optional[float] = None,
        reduced_chi_square: Optional[float] = None,
        message: str = '',
        iterations: int = 0,
        engine_result: Optional[Any] = None,
        starting_parameters: Optional[List[Any]] = None,
        fitting_time: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.success: bool = success
        self.parameters: List[Any] = parameters if parameters is not None else []
        self.chi_square: Optional[float] = chi_square
        self.reduced_chi_square: Optional[float] = reduced_chi_square
        self.message: str = message
        self.iterations: int = iterations
        self.engine_result: Optional[Any] = engine_result
        self.result: Optional[Any] = None
        self.starting_parameters: List[Any] = starting_parameters if starting_parameters is not None else []
        self.fitting_time: Optional[float] = fitting_time

        if 'redchi' in kwargs and self.reduced_chi_square is None:
            self.reduced_chi_square = kwargs.get('redchi')

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
        status_icon = '✅' if self.success else '❌'
        rf = rf2 = wr = br = None
        if y_obs is not None and y_calc is not None:
            rf = calculate_r_factor(y_obs, y_calc) * 100
            rf2 = calculate_r_factor_squared(y_obs, y_calc) * 100
        if y_obs is not None and y_calc is not None and y_err is not None:
            wr = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
        if f_obs is not None and f_calc is not None:
            br = calculate_rb_factor(f_obs, f_calc) * 100

        print(paragraph('Fit results'))
        print(f'{status_icon} Success: {self.success}')
        print(f'⏱️ Fitting time: {self.fitting_time:.2f} seconds')
        print(f'📏 Goodness-of-fit (reduced χ²): {self.reduced_chi_square:.2f}')
        if rf is not None:
            print(f'📏 R-factor (Rf): {rf:.2f}%')
        if rf2 is not None:
            print(f'📏 R-factor squared (Rf²): {rf2:.2f}%')
        if wr is not None:
            print(f'📏 Weighted R-factor (wR): {wr:.2f}%')
        if br is not None:
            print(f'📏 Bragg R-factor (BR): {br:.2f}%')
        print('📈 Fitted parameters:')

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
            datablock_id = getattr(param, 'datablock_id', 'N/A')
            category_key = getattr(param, 'category_key', 'N/A')
            collection_entry_id = getattr(param, 'collection_entry_id', 'N/A')
            name = getattr(param, 'name', 'N/A')
            start = f'{getattr(param, "start_value", "N/A"):.4f}' if param.start_value is not None else 'N/A'
            fitted = f'{param.value:.4f}' if param.value is not None else 'N/A'
            uncertainty = f'{param.uncertainty:.4f}' if param.uncertainty is not None else 'N/A'
            units = getattr(param, 'units', 'N/A')

            if param.start_value and param.value:
                change = ((param.value - param.start_value) / param.start_value) * 100
                arrow = '↑' if change > 0 else '↓'
                relative_change = f'{abs(change):.2f} % {arrow}'
            else:
                relative_change = 'N/A'

            rows.append(
                [datablock_id, category_key, collection_entry_id, name, start, fitted, uncertainty, units, relative_change]
            )

        render_table(
            columns_headers=headers,
            columns_alignment=alignments,
            columns_data=rows,
            show_index=True,
        )
