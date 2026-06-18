from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import compare_unavailable
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_reference_window
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_POWDER_CFL_CONTROL = fullprof_array([
    [38.5, 26.5957],
    [39.538, 3032.2799],
    [40.575, 20.8942],
    [41.612, 6.76595],
    [42.65, 4.7827],
    [43.688, 6.464375],
    [44.725, 20.2661],
    [45.762, 2948.9928],
    [46.8, 21.2596],
])

FULLPROF_WITHOUT_EXTINCTION = fullprof_array([
    [1, 176.27],
    [2, 10.29],
    [3, 78.38],
    [4, 175.52],
    [5, 1877.14],
    [6, 1811.06],
    [7, 229.17],
    [8, 1055.16],
    [9, 453.39],
    [10, 3243.18],
    [11, 323.26],
    [12, 0.05],
    [13, 289.28],
    [14, 14.8],
    [15, 173.89],
    [16, 344.39],
    [17, 800.91],
    [18, 39.26],
    [19, 20.28],
    [20, 717.31],
    [21, 58.12],
    [22, 2211.62],
    [23, 3118.11],
    [24, 0.58],
])

FULLPROF_WITH_ISOTROPIC_EXTINCTION = fullprof_array([
    [1, 193.18],
    [2, 13.32],
    [3, 96.24],
    [4, 206.77],
    [5, 1424.56],
    [6, 1424.86],
    [7, 270.11],
    [8, 1004.65],
    [9, 499.04],
    [10, 2271.13],
    [11, 371.57],
    [12, 0.06],
    [13, 339.33],
    [14, 17.72],
    [15, 206.95],
    [16, 404.55],
    [17, 841.03],
    [18, 49.67],
    [19, 26.13],
    [20, 769.03],
    [21, 73.84],
    [22, 1892.35],
    [23, 2451.86],
    [24, 0.61],
])

NO_CFL_SINGLE_CRYSTAL_EXTINCTION = (
    'patterns_simulation is a powder-pattern CFL API. It cannot request '
    'single-crystal extinction factors or return corrected integrated '
    'intensities.'
)

LBCO_CFL_CONTROL = """
PATTERN_LBCO  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  30.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.494  1.494  0.0
  UVWXY  0.081547  -0.115345  0.121125  0.0  0.083038
  GEN_PATT  38.5  0.05  46.8
END_PATTERN_LBCO

PHASE_LBCO  1
  Cell  3.89079  3.89079  3.89079  90.0  90.0  90.0
  SPGR  P m -3 m
  Atom  La  La  0.0  0.0  0.0  0.57511  0.01042
  Atom  Ba  Ba  0.0  0.0  0.0  0.57511  0.01042
  Atom  Co  Co  0.5  0.5  0.5  0.26023  0.02083
  Atom  O   O   0.0  0.5  0.5  1.36662  0.06116
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LBCO
"""


def main() -> None:
    powder_control = compare_to_fullprof(
        'control powder pattern through CFL',
        LBCO_CFL_CONTROL,
        FULLPROF_POWDER_CFL_CONTROL,
        x_shift=0.6204,
    )
    print_summary('Request 4 powder-CFL control', [powder_control])
    print_reference_window(
        'FullProf single-crystal integrated intensities without extinction',
        FULLPROF_WITHOUT_EXTINCTION,
    )
    print_reference_window(
        'FullProf single-crystal integrated intensities with extinction',
        FULLPROF_WITH_ISOTROPIC_EXTINCTION,
    )
    control = compare_unavailable(
        'control without extinction',
        FULLPROF_WITHOUT_EXTINCTION,
        NO_CFL_SINGLE_CRYSTAL_EXTINCTION,
    )
    requested = compare_unavailable(
        'requested isotropic extinction enabled in FullProf',
        FULLPROF_WITH_ISOTROPIC_EXTINCTION,
        NO_CFL_SINGLE_CRYSTAL_EXTINCTION,
    )
    print_summary('Request 4: single-crystal extinction', [control, requested])
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 4: single-crystal extinction',
            FULLPROF_WITHOUT_EXTINCTION[:, 0],
            [control, requested],
        )


if __name__ == '__main__':
    main()
