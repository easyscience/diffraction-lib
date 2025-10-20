from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List
from typing import Tuple

import pandas as pd

from easydiffraction import log
from easydiffraction.core.singletons import SingletonBase


class RendererBase(SingletonBase, ABC):
    """Base class for display/render components with pluggable
    engines.
    """

    def __init__(self):
        self._engine = self._default_engine()
        self._backend = self._factory().create(self._engine)

    @classmethod
    @abstractmethod
    def _factory(cls) -> type[RendererFactoryBase]:
        """Return the factory class (e.g., PlotterFactory,
        TableFactory).
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _default_engine(cls) -> str:
        """Return the default engine name for this renderer."""
        raise NotImplementedError

    @property
    def engine(self) -> str:
        return self._engine

    @engine.setter
    def engine(self, new_engine: str) -> None:
        if new_engine == self._engine:
            log.info(f"Engine is already set to '{new_engine}'. No change made.")
            return
        engines_list = self._factory().supported_engines()
        if new_engine not in engines_list:
            engines = str(engines_list)[1:-1]  # remove brackets
            log.warning(f"Engine '{new_engine}' is not supported. Available engines: {engines}")
            return
        self._backend = self._factory().create(new_engine)
        self._engine = new_engine
        log.paragraph('Current engine changed to')
        log.print(f"'{self._engine}'")

    def show_config(self) -> None:
        """Display minimal configuration for this renderer."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [['engine', self._engine]]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        log.paragraph('Current renderer configuration')
        self.render(df)

    def show_supported_engines(self) -> None:
        """List supported engines with descriptions."""
        headers = [
            ('Engine', 'left'),
            ('Description', 'left'),
        ]
        rows = self._factory().descriptions()
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        log.paragraph('Supported engines')
        self.render(df)

    def show_current_engine(self) -> None:
        """Display the currently selected engine."""
        log.paragraph('Current engine')
        log.print(f"'{self._engine}'")


class RendererFactoryBase(ABC):
    _SUPPORTED_ENGINES: dict[str, type]

    @classmethod
    def create(cls, engine_name: str) -> Any:
        config = cls._SUPPORTED_ENGINES[engine_name]
        engine_class = config['class']
        instance = engine_class()
        return instance

    @classmethod
    def supported_engines(cls) -> List[str]:
        keys = cls._SUPPORTED_ENGINES.keys()
        engines = list(keys)
        return engines

    @classmethod
    def descriptions(cls) -> List[Tuple[str, str]]:
        items = cls._SUPPORTED_ENGINES.items()
        descriptions = [(name, config.get('description')) for name, config in items]
        return descriptions
