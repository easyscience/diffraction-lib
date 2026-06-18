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

FULLPROF_STRUCTURE_FACTOR_REFERENCE = fullprof_array([
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
])

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

NO_IN_MEMORY_CFL_API = (
    'The CFL API requires text blocks and returns powder profiles. It has no '
    'call that accepts in-memory cell, space group, atoms, and an hkl list and '
    'returns structure factors.'
)


def main() -> None:
    control = compare_to_fullprof(
        'control through CFL powder-pattern simulation',
        LBCO_CFL_CONTROL,
        FULLPROF_POWDER_CFL_CONTROL,
        x_shift=0.6204,
    )
    requested = compare_unavailable(
        'requested in-memory structure-factor calculation',
        FULLPROF_STRUCTURE_FACTOR_REFERENCE,
        NO_IN_MEMORY_CFL_API,
    )
    print_reference_window(
        'FullProf integrated intensities used as structure-factor evidence',
        FULLPROF_STRUCTURE_FACTOR_REFERENCE,
    )
    print_summary('Request 5: in-memory structure factors', [control, requested])
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 5: in-memory structure factors',
            FULLPROF_POWDER_CFL_CONTROL[:, 0],
            [control],
        )


if __name__ == '__main__':
    main()
