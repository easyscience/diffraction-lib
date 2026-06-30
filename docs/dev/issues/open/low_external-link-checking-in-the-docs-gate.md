# 114. External Link Checking in the Docs Gate

**Priority:** `[priority] low`

**Type:** CI / Documentation

The fast docs gate (`docs-build` + `link-check` + `spell-check`) catches
broken nav/internal links and typos on every push, but does not yet
check external URLs. Add a `lychee` link checker (with an allowlist for
rate-limited/unstable domains), coordinated with the
[Documentation CI and Build Verification](../../adrs/accepted/documentation-ci-build.md)
ADR. Run it nightly or on pull requests to avoid flakiness from external
sites. Also covers link-checking of URLs that appear only inside
executed notebook output cells (a feature that does not exist yet).

**Depends on:** nothing.
