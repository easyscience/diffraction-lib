# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

# TODO: Change to use enum for these constants
DEFAULT_AXES_LABELS = {
    'bragg': {
        'constant wavelength': ['2θ (degree)', 'Intensity (arb. units)'],
        'time-of-flight': ['TOF (µs)', 'Intensity (arb. units)'],
        'd-spacing': ['d (Å)', 'Intensity (arb. units)'],
    },
    'total': {
        'constant wavelength': ['r (Å)', 'G(r) (Å)'],
        'time-of-flight': ['r (Å)', 'G(r) (Å)'],
    },
}
