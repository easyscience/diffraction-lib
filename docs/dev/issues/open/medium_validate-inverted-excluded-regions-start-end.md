# 149. Validate Inverted Excluded Regions (start > end)

**Priority:** `[priority] medium`

**Type:** API safety

`start`/`end` on an excluded region are independent `NumericDescriptor`s
with no cross-field validation; `_update` builds
`region_mask = (x >= start) & (x <= end)`, so a region with
`start > end` produces an all-False mask and is silently ignored. A
scientist who enters the bounds in the wrong order gets no exclusion and
no feedback.

**Fix:** validate `start <= end` (warn or raise) when both are set.

**TODOs / locations:**

- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L52)
- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L163)

**Depends on:** nothing.
