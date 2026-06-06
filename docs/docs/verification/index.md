# Verification

This section compares EasyDiffraction's calculation engines against each
other (and, in future, against external software such as FullProf) on
the **same** input parameters, **without any fitting** — just calculated
diffraction patterns and clear closeness metrics.

Each page also runs as a fast regression check
(`pixi run script-tests`), so cross-engine agreement is monitored over
time. Coverage grows to span every supported experiment and instrument
combination.
