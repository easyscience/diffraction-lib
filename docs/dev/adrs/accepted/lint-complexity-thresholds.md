# ADR: Lint Complexity Thresholds

## Status

Accepted.

## Date

2026-05-17

## Group

Quality.

## Context

The repository enforces ruff PLR complexity rules. Raising thresholds or
adding local suppressions would make complex functions easier to merge
without addressing maintainability.

## Decision

Keep ruff's default PLR thresholds, except set `max-args` and
`max-positional-args` to 6 because ruff counts `self` and `cls`.

Do not raise complexity thresholds or add `# noqa` comments to silence
complexity rules. Refactor code instead.

## Consequences

Complexity failures are treated as design feedback. Large refactors that
change public API should be planned explicitly instead of bypassing the
guardrail.
