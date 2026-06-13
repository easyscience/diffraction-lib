# 68. Decide Whether to Apply `@typechecked` to All Public Methods

**Priority:** `[priority] low`

**Type:** Design

`@typechecked` is currently applied only in ~24 places (factories,
collections). Decide whether it should be applied systematically to all
public method signatures, or whether custom validation (issue 67) is
preferred.

**Depends on:** issue 67.
