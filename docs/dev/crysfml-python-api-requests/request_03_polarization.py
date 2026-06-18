from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot
from y2o3_common import FULLPROF_Y2O3_POLARIZATION
from y2o3_common import FULLPROF_Y2O3_XRAY_SINGLE
from y2o3_common import Y2O3_CFL_XRAY_POLARIZATION
from y2o3_common import Y2O3_CFL_XRAY_SINGLE
from y2o3_common import Y2O3_X_SHIFT


def main() -> None:
    control = compare_to_fullprof(
        'without X-ray polarization',
        Y2O3_CFL_XRAY_SINGLE,
        FULLPROF_Y2O3_XRAY_SINGLE,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with X-ray polarization in FullProf',
        Y2O3_CFL_XRAY_POLARIZATION,
        FULLPROF_Y2O3_POLARIZATION,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 3: X-ray polarization', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 3: X-ray polarization', comparisons)


if __name__ == '__main__':
    main()
