from abc import ABC
from abc import abstractmethod

import numpy as np

from easydiffraction.utils.utils import is_notebook
from easydiffraction.utils.utils import is_pycharm

DEFAULT_ENGINE = 'plotly' if is_notebook() or is_pycharm() else 'asciichartpy'
DEFAULT_HEIGHT = 9
DEFAULT_MIN = -np.inf
DEFAULT_MAX = np.inf

SERIES_CONFIG = dict(
    calc=dict(
        mode='lines',
        name='Total calculated (Icalc)'
    ),
    meas=dict(
        mode='lines+markers',
        name='Measured (Imeas)'
    ),
    resid=dict(
        mode='lines',
        name='Residual (Imeas - Icalc)'
    )
)


class PlotterBase(ABC):

    @abstractmethod
    def plot(self,
             x,
             y_series,
             labels,
             axes_labels,
             title,
             height):
        pass
