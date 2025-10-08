# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


class CifHandler:
    def __init__(self, *, names: list[str]) -> None:
        self._names = names

    @property
    def names(self):
        return self._names
