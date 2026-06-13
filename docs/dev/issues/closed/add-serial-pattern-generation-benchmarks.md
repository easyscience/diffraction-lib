# 16. Add Serial Pattern-Generation Benchmarks

Closed by the cross-engine verification work (#195): `tests/benchmarks/test_calculate_pattern_benchmark.py` benchmarks single-pattern calculation on fixed datasets across cryspy and crysfml, and a dedicated serial `pixi run benchmarks` task runs it outside the parallel xdist suite (no `-n auto`). Regression thresholds remain deferred until timings stabilise, exactly as the issue specified.
