# 101. Remove Dead Branch in `_fit_state_categories`

Closed by the emcee minimizer implementation. The deterministic branch
that returned the same category list as the fallthrough path was removed
while preserving unsupported `result_kind` warning behavior.
