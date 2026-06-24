# 128. Align `dir()` With Help Filtering

**Priority:** `[priority] low`

**Type:** Discoverability

`help()` now hides inactive analysis categories by fitting mode, while
`dir()` and tab completion still expose the full class surface.

**Fix:** decide whether `dir()` should mirror the help filter or remain
an always-complete developer surface.

**Depends on:** nothing.
