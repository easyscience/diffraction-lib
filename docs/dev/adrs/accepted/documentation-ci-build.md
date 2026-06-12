# ADR: Documentation CI and Build Verification

**Status:** Accepted  
**Date:** 2026-05-31

## Group

Documentation.

## Context

User-facing documentation can drift from the Python API, persisted CIF
tags, tutorial outputs, and MkDocs navigation. Recent examples included
stale selector methods, an outdated minimizer list, missing Quick
Reference navigation, and code snippets that no longer matched current
category-owned selectors.

The documentation build should catch more of this drift before review.
The checks should remain understandable to scientific contributors and
should distinguish source documentation from generated notebooks.

## Decision

Add documentation verification in layers, starting with checks that are
cheap, deterministic, and useful in local development.

### 1. Build the MkDocs site in strict mode

Run the docs build in CI with:

```shell
mkdocs build --strict
```

or the equivalent `pixi` task once one is added. This should catch
missing navigation entries, broken internal references reported by
MkDocs, and warnings that should fail documentation CI.

### 2. Keep API reference generation source-driven

Continue using source-driven API documentation. If the current API
reference generation is not already based on `mkdocstrings`, adopt or
standardize on `mkdocstrings[python]` so public signatures and docstring
content are pulled from the installed package rather than copied into
manual Markdown.

### 3. Add snippet smoke tests for user-facing examples

Add a small documentation smoke-test script that extracts or imports
selected Python snippets from:

- `docs/docs/quick-reference/index.md`
- `docs/docs/user-guide/first-steps.md`
- `docs/docs/user-guide/analysis-workflow/*.md`

The smoke tests should focus on API shape, not full calculations. They
should instantiate small projects, check public method names, and avoid
network, notebooks, and real calculator backends unless explicitly
covered by slower script or integration tests.

### 4. Check generated tutorial freshness separately

Tutorial notebooks remain generated artifacts. CI should verify that
`pixi run notebook-prepare` leaves generated `.ipynb` files unchanged,
or expose an explicit `notebook-prepare-check` task if the project wants
a faster no-write mode.

### 5. Check links with a dedicated link checker

Use `lychee` or an equivalent link checker for Markdown and generated
HTML links. Configure it with an allowlist for intentionally unstable or
rate-limited external domains, and cache results where practical.

### 6. Add prose and spelling checks incrementally

Use `codespell` first for low-noise spelling checks. Consider `Vale`
after the project has a small EasyDiffraction style vocabulary and an
allowlist for crystallographic terms, package names, and CIF tags.

## Implementation Status

Most of this ADR is already in place; it is accepted to record the
chosen direction and to track the remaining gaps.

| # | Decision | Status |
| - | -------- | ------ |
| 1 | MkDocs `--strict` build | **Done** — `docs-build` pixi task runs `mkdocs build --strict`; wired into the `lint-format.yml` "docs strict build" gate and the `docs.yml` deploy workflow. |
| 2 | `mkdocstrings` for API pages | **Done** — `mkdocstrings` + `mkdocstrings-python` configured in `docs/mkdocs.yml` (handler `paths: ['src']`); the `api-reference/*.md` pages use `:::` directives. |
| 3 | Snippet smoke tests | **Not done** — no task imports or executes the user-facing snippets in `quick-reference/`, `user-guide/first-steps.md`, or `user-guide/analysis-workflow/*.md`. Highest-value remaining gap. |
| 4 | Tutorial freshness check | **Partial** — `notebook-prepare` plus `notebook-tests`/`notebook-exec-ci` exist, but no no-write task asserts that `notebook-prepare` leaves the committed `.ipynb` unchanged. |
| 5 | `lychee` link checking | **Done for local/relative links** — `link-check` pixi task (config in `lychee.toml`) is wired into `lint-format.yml`. External-URL checking is deferred (see issue 114). |
| 6 | `codespell`, then `Vale` | **codespell done** — `spell-check` pixi task wired into `lint-format.yml`. `Vale` deferred. |

## Options Considered

### MkDocs strict build

Pros:

- aligns with the existing MkDocs build path
- catches navigation and internal-reference problems early
- low conceptual overhead for contributors

Cons:

- does not execute Python snippets
- external URLs require a separate checker

### mkdocstrings for API pages

Pros:

- keeps API reference tied to source signatures and docstrings
- supports Python docstring styles already used by the project
- reduces manual API copy/paste drift

Cons:

- requires a docs dependency if not already present
- only helps reference pages, not narrative examples

### Documentation snippet smoke tests

Pros:

- directly catches renamed methods and stale public API examples
- can stay fast if limited to no-backend API construction
- complements unit tests because it validates documented workflows

Cons:

- snippet extraction needs conventions or explicit markers
- examples involving downloaded data or calculators need fixtures or
  slower test tiers

### lychee link checking

Pros:

- checks Markdown, HTML, and external URLs
- has a GitHub Action and CLI workflow
- can run on a schedule for external-link rot

Cons:

- external sites can be flaky or rate-limited
- needs ignore rules for intentionally unreachable example URLs

### Vale prose linting

Pros:

- catches grammar/style issues beyond spelling
- supports project-specific style rules
- can make docs more consistent for non-programmer users

Cons:

- needs careful configuration to avoid noisy scientific false positives
- style-rule debates can slow feature reviews if introduced too broadly

### codespell spelling checks

Pros:

- fast, simple, and available through pre-commit and CI
- catches common typos in docs and code comments
- lower adoption cost than full prose linting

Cons:

- needs ignore words for crystallography, CIF tags, names, and package
  identifiers
- does not catch grammar or stale API examples

## Consequences

### Positive

- Documentation drift becomes visible before merge.
- User-facing examples are more likely to match the current API.
- Generated notebooks remain controlled by their existing
  source-of-truth workflow.
- Link and prose quality can improve without blocking on a full
  documentation-system redesign.

### Trade-offs

- CI gains more jobs or longer docs jobs.
- New tools require dependency and configuration maintenance.
- External link checking can produce intermittent failures unless
  scheduled, cached, or configured with retries and an allowlist.

## Deferred Work

- Add snippet smoke tests for user-facing examples (decision 3). Tracked
  by the `documentation-snippet-tests` implementation plan. Open
  question carried into that plan: extract fenced code blocks
  automatically or rely on explicitly named snippets.
- Add a no-write `notebook-prepare-check` task that fails CI when the
  committed notebooks are out of date with their `.py` sources
  (decision 4).
- Enable external-URL link checking in the docs gate (decision 5),
  scheduled or cached to avoid flakiness. Tracked by issue 114.
- Adopt `Vale` prose linting once an EasyDiffraction style vocabulary
  and crystallographic-term allowlist exist (decision 6).
