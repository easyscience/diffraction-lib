# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from easydiffraction.core.categories import CategoryCollection


class BackgroundBase(CategoryCollection):
    @abstractmethod
    def calculate(self, x_data: Any) -> Any:
        pass

    @abstractmethod
    def show(self) -> None:
        pass
