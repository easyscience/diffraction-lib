from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_CW_CONTROL = fullprof_array([
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

FULLPROF_TOF_JORGENSEN_VON_DREELE = fullprof_array([
    [12000, 4.63],
    [12100, 12.73],
    [12200, 190.66],
    [12300, 730.86],
    [12400, 22.36],
    [12500, 0.11],
    [12600, 0.08],
    [12700, 0.04],
    [12800, 0.0],
    [12900, -0.04],
    [13000, -0.08],
    [13100, -0.11],
    [13200, -0.14],
    [13300, -0.17],
    [13400, -0.19],
    [13500, -0.21],
    [13600, -0.22],
    [13700, -0.22],
    [13800, -0.21],
    [13900, -0.19],
    [14000, -0.16],
    [14100, 9.03],
    [14200, 24.33],
    [14300, 212.71],
    [14400, 2375.95],
    [14500, 67.44],
    [14600, 12.26],
])

LBCO_CW_CONTROL_CFL = """
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

SI_TOF_CFL = """
PATTERN_Si_TOF  1
  Patt_Type  Neutrons Powder TOF
  Profile_function  tof_Jorgensen_VonDreele
  WDT  8.2
  D2TOF  -9.18766  7476.91016  -1.54  0.0
  ALPHA  0.0  0.5971  0.0
  BETA  0.04221  0.00946  0.0
  SIGMA  0.0  33.0419  3.5544  0.0
  GAMMA  0.0  2.543  0.0
  TOF_RANGE  12000.0  14600.0  5.0
  GEN_PATT  12000.0  5.0  14600.0
END_PATTERN_Si_TOF

PHASE_Si  1
  Cell  5.431342  5.431342  5.431342  90.0  90.0  90.0
  SPGR  F d -3 m
  Atom  Si  Si  0.125  0.125  0.125  0.52448  1.0
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_Si
"""


def main() -> None:
    control = compare_to_fullprof(
        'control CW powder pattern through patterns_simulation',
        LBCO_CW_CONTROL_CFL,
        FULLPROF_CW_CONTROL,
        x_shift=0.6204,
    )
    requested = compare_to_fullprof(
        'requested TOF pattern through patterns_simulation',
        SI_TOF_CFL,
        FULLPROF_TOF_JORGENSEN_VON_DREELE,
    )
    print_summary('Request 7: TOF patterns_simulation', [control, requested])
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 7: TOF patterns_simulation',
            FULLPROF_TOF_JORGENSEN_VON_DREELE[:, 0],
            [requested],
        )


if __name__ == '__main__':
    main()
