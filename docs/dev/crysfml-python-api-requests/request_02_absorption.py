from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot


WINDOW_START = 55.5
WINDOW_STEP = 0.05
Y2O3_X_SHIFT = -0.01625


def _window_array(intensities: list[float]) -> np.ndarray:
    return fullprof_array([
        [WINDOW_START + WINDOW_STEP * index, intensity]
        for index, intensity in enumerate(intensities)
    ])


# Edit these CFL blocks to experiment with CrysFML output.
CONTROL_CFL = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  55.51625  0.05  59.51625
END_PATTERN_Y2O3

PHASE_Y2O3  1
  Cell  10.605744  10.605744  10.605744  90.0  90.0  90.0
  SPGR  I a -3
  Atom  Y1  Y  -0.03236  0.0  0.25  0.0  0.5
  Atom  Y2  Y   0.25     0.25 0.25  0.0  0.16667
  Atom  O1  O   0.39072  0.15204  0.38030  0.0  1.0
  Contributes_to_patterns  1
  Scale_Factors  1.0
  PH_Pattern  1
    Calc_Type  Nuclear
  END_PH_Pattern
END_PHASE_Y2O3
"""

REQUESTED_CFL = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  55.51625  0.05  59.51625
END_PATTERN_Y2O3

PHASE_Y2O3  1
  Cell  10.605744  10.605744  10.605744  90.0  90.0  90.0
  SPGR  I a -3
  Atom  Y1  Y  -0.03236  0.0  0.25  0.0  0.5
  Atom  Y2  Y   0.25     0.25 0.25  0.0  0.16667
  Atom  O1  O   0.39072  0.15204  0.38030  0.0  1.0
  Contributes_to_patterns  1
  Scale_Factors  1.0
  PH_Pattern  1
    Calc_Type  Nuclear
    Absorption  0.9
  END_PH_Pattern
END_PHASE_Y2O3
"""

# Generated with FullProf 8.40 from the PCR files in fullprof/.
FULLPROF_CONTROL = _window_array([
    1.8614706, 0.4336294, 0.0930261477, 0.0191738523,
    0.0085706, 0.0579706, 0.3406289, 1.70952615,
    7.68567385, 30.2850706, 104.584471, 316.667029,
    840.526426, 1955.90257, 3989.66147, 7134.21087,
    11183.4735, 15368.4129, 18514.2491, 19552.238,
    18101.2274, 14690.65, 10451.8994, 6518.57557,
    3564.05497, 1708.27387, 717.786529, 264.395926,
    85.3720739, 24.1614706, 6.0003711, 1.3130294,
    0.252426148, 0.0685738523, 0.1779706, 0.9973706,
    5.1995294, 23.6689261, 94.5050739, 330.644471,
    1013.50377, 2721.82643, 6404.13543, 13202.2715,
    23843.9409, 37728.8403, 52304.0629, 63527.7818,
    67601.818, 63025.3174, 51479.9568, 36840.6894,
    23098.4988, 12687.725, 6106.16387, 2574.66327,
    951.125929, 307.845326, 87.2814739, 21.6908706,
    4.7197711, 0.9124294, 0.181826148, 0.187973852,
    0.9573706, 4.7162711, 20.5289294, 78.1983261,
    260.854474, 761.923771, 1948.76317, 4364.40543,
    8558.77473, 14697.2009, 22098.2803, 29093.9897,
    33540.4218, 33857.4812, 29926.4274, 23162.0968,
    15697.1762,
])

FULLPROF_REQUESTED = _window_array([
    0.4614706, 0.1136294, 0.0230261477, -0.000826147705,
    -0.0014294, 0.0179706, 0.0806289, 0.429526148,
    1.90567385, 7.5250706, 26.0044706, 78.7570294,
    209.036426, 486.432574, 992.231471, 1774.28087,
    2781.33353, 3822.13293, 4604.49907, 4862.64797,
    4501.77737, 3653.57003, 2599.38943, 1621.17557,
    886.384971, 424.843871, 178.516529, 65.7559261,
    21.2320739, 6.0114706, 1.4903711, 0.3230294,
    0.0624261477, 0.0185738523, 0.0379706, 0.2473706,
    1.2995294, 5.90892615, 23.5850739, 82.5244706,
    252.963771, 679.356429, 1598.43543, 3295.21147,
    5951.31087, 9416.91027, 13054.8129, 15856.1918,
    16873.048, 15730.7774, 12849.1168, 9195.23943,
    5765.25883, 3166.78497, 1524.06387, 642.623271,
    237.395929, 76.8353261, 21.7814739, 5.4108706,
    1.1797711, 0.2324294, 0.0418261477, 0.0479738523,
    0.2373706, 1.1762711, 5.1389294, 19.5883261,
    65.3444739, 190.853771, 488.143171, 1093.24543,
    2143.90473, 3681.53087, 5535.44027, 7287.80967,
    8401.61183, 8481.03123, 7496.33737, 5801.91677,
    3932.01617,
])


def main() -> None:
    control = compare_to_fullprof(
        'without cylindrical absorption',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with cylindrical absorption requested in CFL',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 2: cylindrical absorption', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 2: cylindrical absorption', comparisons)


if __name__ == '__main__':
    main()
