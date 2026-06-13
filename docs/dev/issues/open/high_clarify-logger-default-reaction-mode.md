# 61. Clarify Logger Default Reaction Mode

**Priority:** `[priority] high`

**Type:** Design

`Logger._reaction` defaults to `Reaction.RAISE` with a
`TODO: not default?` marker.

**TODOs:**

- [logging.py](src/easydiffraction/utils/logging.py#L430)

**Depends on:** nothing.

**Recommended-priority note:** Logger default reaction mode — pairs with #66's error-handling strategy decision. **Tier 2.**
