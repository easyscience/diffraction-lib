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
  BETA  0.00303  0.00272  0.00295  0.0  0.0  -0.00025
  Atom  Y2  Y   0.25     0.25 0.25  0.0  0.16667
  BETA  0.00304  0.00304  0.00304  -0.00013  -0.00013  -0.00013
  Atom  O1  O   0.39072  0.15204  0.38030  0.0  1.0
  BETA  0.00299  0.00310  0.00273  -0.00007  -0.00020  -0.00001
  Contributes_to_patterns  1
  Scale_Factors  1.0
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
    1.5014706, 0.3536294, 0.0730261477, 0.0091738523,
    0.0085706, 0.0479706, 0.2606289, 1.33952615,
    6.00567385, 23.6750706, 81.7644706, 247.567029,
    657.106426, 1529.08257, 3119.02147, 5577.35087,
    8742.97353, 12014.6629, 14474.0091, 15285.478,
    14151.1174, 11484.81, 8171.04943, 5096.06557,
    2786.29497, 1335.49387, 561.146529, 206.695926,
    66.7420739, 18.8914706, 4.6903711, 1.0230294,
    0.202426148, 0.0485738523, 0.1379706, 0.7773706,
    4.0395294, 18.3789261, 73.3750739, 256.694471,
    786.843771, 2113.09643, 4971.87543, 10249.6315,
    18511.3209, 29290.9103, 40606.4329, 49320.0118,
    52482.898, 48929.9174, 39966.6368, 28601.3994,
    17932.5988, 9850.16497, 4740.54387, 1998.84327,
    738.415929, 238.995326, 67.7614739, 16.8408706,
    3.6697711, 0.7024294, 0.141826148, 0.147973852,
    0.7173706, 3.5662711, 15.5189294, 59.1283261,
    197.244474, 576.133771, 1473.57317, 3300.18543,
    6471.80473, 11113.4309, 16709.8303, 21999.7097,
    25361.9218, 25601.6612, 22629.1674, 17514.2468,
    11869.5762,
])


def main() -> None:
    control = compare_to_fullprof(
        'without beta ADPs',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with beta ADPs in FullProf',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 7: beta ADPs', comparisons)
    print(
        'Note: CFL can carry BETA records; the requested gap is the '
        'non-CFL Python input path.'
    )
    if should_plot(sys.argv):
        plot_comparisons('Request 7: beta ADPs', comparisons)


if __name__ == '__main__':
    main()
