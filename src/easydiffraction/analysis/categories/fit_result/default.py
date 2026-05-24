# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Default fit-result category import."""

from __future__ import annotations

from easydiffraction.analysis.categories.fit_result.base import FitResultBase

DEFAULT_FIT_RESULT_CLASS: type[FitResultBase] = FitResultBase
