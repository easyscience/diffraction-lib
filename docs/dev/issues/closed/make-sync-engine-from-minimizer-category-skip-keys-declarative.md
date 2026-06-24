# 103. Make `_sync_engine_from_minimizer_category` Skip-Keys Declarative

Closed by the emcee minimizer implementation. Minimizer categories now
declare `_engine_sync_skip_keys`, and analysis sync filters against that
set instead of hardcoding skipped keys.
