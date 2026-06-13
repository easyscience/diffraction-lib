# 91. Disable TODO Comment Checks in CodeFactor PRs

**Priority:** `[priority] lowest`

**Type:** CI / Tooling

CodeFactor flags TODO comments as unresolved issues (rule C100) in PRs.
Since TODOs are tracked in `issues/open.md`, the CodeFactor check adds
noise. Disable the C100 rule or configure CodeFactor to ignore TODO
comments.

**Depends on:** nothing.

**Recommended-priority note:** Marked **lowest**: CI-tooling noise reduction (CodeFactor TODO rule), not a product defect.
