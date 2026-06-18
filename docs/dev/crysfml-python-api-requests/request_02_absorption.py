from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot
from y2o3_common import FULLPROF_Y2O3_ABSORPTION
from y2o3_common import FULLPROF_Y2O3_BETA_CONTROL
from y2o3_common import Y2O3_CFL_NEUTRON_ABSORPTION
from y2o3_common import Y2O3_CFL_NEUTRON_BETA
from y2o3_common import Y2O3_X_SHIFT


def main() -> None:
    control = compare_to_fullprof(
        'without cylindrical absorption',
        Y2O3_CFL_NEUTRON_BETA,
        FULLPROF_Y2O3_BETA_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with cylindrical absorption in FullProf',
        Y2O3_CFL_NEUTRON_ABSORPTION,
        FULLPROF_Y2O3_ABSORPTION,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 2: cylindrical absorption', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 2: cylindrical absorption', comparisons)


if __name__ == '__main__':
    main()
