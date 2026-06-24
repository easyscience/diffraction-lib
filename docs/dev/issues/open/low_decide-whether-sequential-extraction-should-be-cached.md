# 125. Decide Whether Sequential Extraction Should Be Cached

**Priority:** `[priority] low`

**Type:** Performance

Sequential metadata extraction currently re-reads input files when the
run is repeated or resumed.

**Fix:** decide whether extracted `diffrn.*` values should be cached in
`analysis/results.csv` only, or also in a dedicated reusable cache.

**Depends on:** nothing.
