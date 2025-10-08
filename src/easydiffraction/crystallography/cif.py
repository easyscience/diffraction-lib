from __future__ import annotations


class CifHandler:
    def __init__(self, *, names: list[str]) -> None:
        self._names = names

    @property
    def names(self):
        return self._names
