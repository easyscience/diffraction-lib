# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Compatibility exports for single-crystal reflection data."""

from __future__ import annotations

from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.categories.refln import bragg_sc as refln_bragg_sc

Refln = refln_bragg_sc.Refln
ReflnData = refln_bragg_sc.ReflnData

DataFactory.register(ReflnData)
