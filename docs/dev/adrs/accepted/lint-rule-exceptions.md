# ADR: Lint Rule Scope and Test-File Exceptions

## Status

Accepted.

## Date

2026-06-08

## Group

Quality.

## Context

A full audit of ruff's disabled rules (merged in #194) adopted a
low-risk subset and recorded which remaining suppressions are
deliberate. Three of those suppressions are standing policy rather than
temporary noise, and the audit flagged each as needing a recorded
decision because it either scopes or extends the
[`lint-complexity-thresholds.md`](lint-complexity-thresholds.md) ADR
(which treats PLR complexity limits as guardrails that must not be
silenced):

- The PLR complexity rules `PLR0913`, `PLR0914`, `PLR0915`, and
  `PLR0917` are ignored for `tests/**`.
- `N812` (lowercase import alias) is ignored for `tests/**`.
- The flake8-builtins `A` family is not enabled at all, so CIF-aligned
  field names such as `id` and `type` do not trip builtin-shadowing
  rules.

The audit document itself was a one-time roadmap and is not retained;
this ADR records the durable decisions it surfaced.

## Decision

1. **Test-file complexity exception.** `PLR0913`, `PLR0914`, `PLR0915`,
   and `PLR0917` stay ignored under `tests/**` via
   `[tool.ruff.lint.per-file-ignores]`. This is a deliberate, scoped
   exception to `lint-complexity-thresholds.md`: test bodies legitimately
   accumulate many arguments, locals, and statements (fixtures,
   parametrisation, arrange-act-assert) where the complexity is not a
   maintainability signal. Production code under `src/**` remains fully
   governed by `lint-complexity-thresholds.md` — the guardrail is not
   relaxed there, and `# noqa` / threshold raises remain disallowed in
   `src/**`.

2. **Test-file import-alias exception.** `N812` stays ignored under
   `tests/**` so tests may import a module-under-test with a lowercase
   alias (the `MUT` / `mut` idiom) without renaming convention churn.

3. **CIF-aligned builtin names.** The flake8-builtins `A` family stays
   disabled project-wide so categories can use the CIF-aligned field
   names `id` and `type` (mandated by IUCr CIF tag alignment) without
   builtin-shadowing warnings. Renaming these would break CIF
   correspondence; the lint cost is not worth the divergence.

These exceptions are the complete set of standing PLR/naming/builtin
suppressions. Any further permanent suppression that conflicts with or
extends `lint-complexity-thresholds.md` needs its own recorded decision
before adoption.

## Consequences

### Positive

- The standing test-file and CIF-naming suppressions are documented
  decisions rather than unexplained `pyproject.toml` entries.
- `lint-complexity-thresholds.md` keeps its full force over `src/**`; the
  scope of the relaxation is explicit and bounded to `tests/**`.

### Trade-offs

- Test code can grow more complex without lint feedback; reviewers carry
  that judgement instead of the linter.
- The `id` / `type` field names continue to shadow builtins by design, so
  contributors must keep CIF-alignment context in mind when reading those
  categories.
