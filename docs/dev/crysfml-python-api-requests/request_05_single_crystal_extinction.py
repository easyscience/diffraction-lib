from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import compare_unavailable
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot
from y2o3_common import FULLPROF_Y2O3_BETA_CONTROL
from y2o3_common import Y2O3_CFL_NEUTRON_BETA
from y2o3_common import Y2O3_X_SHIFT

NO_SINGLE_CRYSTAL_EXTINCTION_API = (
    'patterns_simulation is a powder-pattern API. The inspected '
    'pycrysfml package has no callable single-crystal extinction API '
    'for corrected integrated intensities or correction factors.'
)


def main() -> None:
    control = compare_to_fullprof(
        'without single-crystal extinction API request',
        Y2O3_CFL_NEUTRON_BETA,
        FULLPROF_Y2O3_BETA_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_unavailable(
        'with single-crystal extinction API requested',
        FULLPROF_Y2O3_BETA_CONTROL,
        NO_SINGLE_CRYSTAL_EXTINCTION_API,
    )
    comparisons = [control, requested]
    print_summary('Request 5: single-crystal extinction', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 5: single-crystal extinction', comparisons)


if __name__ == '__main__':
    main()
