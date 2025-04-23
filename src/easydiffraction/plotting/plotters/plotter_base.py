import numpy as np
from abc import ABC, abstractmethod

DEFAULT_HEIGHT = 9
DEFAULT_ENGINE = 'asciichartpy'
DEFAULT_MIN = -np.Inf
DEFAULT_MAX = np.Inf

SERIES_CONFIG = dict(
    calc=dict(
        mode='lines',
        name='Total calculated (Icalc)'
    ),
    meas=dict(
        mode='markers',
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
             title,
             height):
        pass
