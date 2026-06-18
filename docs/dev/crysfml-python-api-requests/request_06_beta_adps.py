from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_ISOTROPIC_CONTROL = fullprof_array([
    [28.0, 9.5300002e-05],
    [28.15, 0.0041953],
    [28.3, 0.0028010978],
    [28.45, 0.0142943],
    [28.6, 1.9182989],
    [28.75, 141.5334],
    [28.85, 1372.0027],
    [29.0, 16906.888],
    [29.15, 71109.952],
    [29.3, 102082.95],
    [29.45, 50017.792],
    [29.6, 8364.756],
    [29.75, 477.461],
    [29.9, 9.3050953],
    [30.05, 0.063701098],
    [30.2, 0.0051953],
    [30.35, -0.00080109781],
    [30.5, 0.0042953],
    [30.65, -0.0007057],
    [30.75, -0.0013047],
    [30.9, 0.0036943],
    [31.05, 1.3214011],
    [31.2, 73.752795],
    [31.35, 1397.8269],
    [31.5, 8951.0519],
])

FULLPROF_BETA_ADP = fullprof_array([
    [28.0, 9.5300002e-05],
    [28.15, 0.0041953],
    [28.3, 0.0028010978],
    [28.45, 0.0042943],
    [28.6, 1.7882989],
    [28.75, 131.7234],
    [28.85, 1276.8327],
    [29.0, 15734.738],
    [29.15, 66180.672],
    [29.3, 95005.531],
    [29.45, 46550.062],
    [29.6, 7785.056],
    [29.75, 444.361],
    [29.9, 8.6550953],
    [30.05, 0.063701098],
    [30.2, 0.0051953],
    [30.35, -0.00080109781],
    [30.5, 0.0042953],
    [30.65, -0.0007057],
    [30.75, -0.0013047],
    [30.9, 0.0036943],
    [31.05, 1.2114011],
    [31.2, 67.612795],
    [31.35, 1281.5569],
    [31.5, 8206.3919],
])

Y2O3_CFL_ISOTROPIC = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  28.0  0.05  31.5
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

Y2O3_CFL_BETA = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  28.0  0.05  31.5
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


def main() -> None:
    control = compare_to_fullprof(
        'control with isotropic Biso records',
        Y2O3_CFL_ISOTROPIC,
        FULLPROF_ISOTROPIC_CONTROL,
        x_shift=-0.01625,
    )
    requested = compare_to_fullprof(
        'beta ADPs enabled through CFL',
        Y2O3_CFL_BETA,
        FULLPROF_BETA_ADP,
        x_shift=-0.01625,
        scale_override=control.scale,
    )
    print_summary('Request 6: beta ADPs', [control, requested])
    print(
        'Note: CFL can carry BETA records; the requested gap is the '
        'non-CFL Python input path.'
    )
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 6: beta ADPs',
            FULLPROF_ISOTROPIC_CONTROL[:, 0],
            [control, requested],
        )


if __name__ == '__main__':
    main()
