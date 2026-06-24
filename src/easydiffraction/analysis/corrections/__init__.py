# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Calculator-independent corrections applied on top of a backend pattern.

Each module here adjusts an already-calculated diffraction pattern
rather than computing one. The shared informal contract is a module
level ``apply(y, experiment) -> y`` function that returns the corrected
intensities, leaving ``y`` unchanged when the correction does not apply.
Engines live in the sibling ``analysis.calculators`` package; these
corrections are consumed by those engines after they return a convolved
profile.
"""
