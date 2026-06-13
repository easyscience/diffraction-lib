# 155. Fix Reversed Abstract `_sync_result_to_parameters` Signature

**Priority:** `[priority] low`

**Type:** Maintainability

The abstract declaration is
`_sync_result_to_parameters(self, raw_result, parameters)`, but the base
caller (`_finalize_fit`) and every concrete override use
`(parameters, raw_result)`. Calls are positional so runtime is correct,
but the abstract signature and docstring are misleading and would trip up
a new minimizer author.

**Fix:** correct the abstract signature/docstring to
`(parameters, raw_result)`.

**TODOs / locations:**

- [base.py](src/easydiffraction/analysis/minimizers/base.py#L169)

**Depends on:** nothing.
