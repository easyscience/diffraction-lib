# 123. Define `sequential_fit_extract` Target Scope

**Priority:** `[priority] medium`

**Type:** Data model

Sequential extract rules currently target one numeric descriptor under
`experiment.diffrn`. Open questions remain around nested targets,
duplicate rules writing the same target, and how additional supported
prefixes should be introduced when new environment categories appear.

**Fix:** pin the allowed target grammar and duplicate-target behaviour
in an ADR and validation rules.

**Depends on:** nothing.
