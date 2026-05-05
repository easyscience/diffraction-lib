# Node24 Actions Migration Plan

## Goal

Eliminate GitHub Actions Node.js 20 deprecation warnings originating from
this repository's `.github/` configuration while preserving current workflow
behavior. Remove `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` only after the relevant
actions are upgraded or replaced.

## Current Findings

### Confirmed warning sources

| Surface | Current reference | Verified runtime status | Planned direction |
| --- | --- | --- | --- |
| `.github/actions/setup-easyscience-bot/action.yml` | `actions/create-github-app-token@v2` | Node 20 warning source | Upgrade to `@v3` |
| `.github/actions/upload-codecov/action.yml` | `codecov/codecov-action@v5` | Composite action; `v5` internally pins `actions/github-script@v7.0.1` (Node 20) | Upgrade to `@v6` |
| `.github/workflows/dashboard.yml` | `Wandalen/wretry.action@v3.8.0` | Composite action resolves to `v3.8.0_js_action`, which declares `node20` | Replace action chain |

### Confirmed future warning sources in current workflow graph

| Surface | Current reference | Verified runtime status | Planned direction |
| --- | --- | --- | --- |
| `.github/workflows/dashboard.yml` | `peaceiris/actions-gh-pages@v4` (wrapped by `wretry`) | Declares `node20` | Replace with local shell/git publish logic |
| `.github/workflows/release-notes.yml` | `enhantica/drafterino@v2` | Declares `node20` | Upgrade upstream or replace locally |
| `.github/workflows/release-notes.yml` | `softprops/action-gh-release@v2` | Declares `node20`; upstream `v3` is Node 24 | Upgrade to `@v3` |

### Actions already aligned or not a Node warning risk

| Reference | Status |
| --- | --- |
| `actions/checkout@v5` | Declares `node24` |
| `prefix-dev/setup-pixi@v0.9.4` | Declares `node24` |
| `.github/actions/github-script` -> `actions/github-script@v8` | Declares `node24` |
| `Mattraks/delete-workflow-runs@v2` | Major tag currently resolves to `node24` |
| `trstringer/require-label-prefix@v1` | Docker action, not a Node runtime warning source |
| `github/codeql-action@v4` | Composite stub at root; not part of the reported warning set |

### Watchlist

These are not part of the quoted warnings, but their current upstream action
manifests still declare `node20` and may need follow-up if GitHub starts
flagging them in this repository's runs:

- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `actions/download-artifact@v4`

Do not churn on these in this repo until they either start warning in actual
runs or an obvious safe upgrade path exists.

## Decisions Already Made

- `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` is a temporary compatibility
  switch, not a fix. It keeps workflows running but does not remove warnings.
- Upgrading only `Wandalen/wretry.action` is not sufficient, because the wrapped
  `peaceiris/actions-gh-pages@v4` action also still targets Node 20.
- `actions/create-github-app-token@v3` can be adopted without an immediate
  secret/variable migration because it still accepts the deprecated `app-id`
  input. A later cleanup can move to `client-id` if desired.

## Files Likely To Change

- `.github/actions/setup-easyscience-bot/action.yml`
- `.github/actions/upload-codecov/action.yml`
- `.github/workflows/dashboard.yml`
- `.github/workflows/release-notes.yml`
- `.github/workflows/backmerge.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/issues-labels.yml`
- `.github/workflows/pypi-test.yml`
- `.github/workflows/release-pr.yml`
- `.github/workflows/test-trigger.yml`
- `.github/workflows/tutorial-tests-trigger.yml`
- `.github/workflows/coverage.yml`
- `.github/workflows/test.yml`
- `.github/workflows/tutorial-tests.yml`
- Possibly a new helper under `.github/scripts/` for dashboard publishing
  retries and push logic
- Possibly a local replacement script/action for Drafterino if upstream is not
  updated in time

## Open Questions

- Should `enhantica/drafterino` be updated upstream as part of this effort, or
  should this repository replace it locally to remove the dependency?
- Is it acceptable to replace the dashboard publish step with plain shell/git
  logic instead of third-party publish actions?
- Should the watchlist actions be proactively replaced if warnings appear, or
  should we wait for upstream major releases from the action maintainers?

## Phase 1 — Implementation

- [ ] Upgrade `.github/actions/setup-easyscience-bot/action.yml` from
      `actions/create-github-app-token@v2` to `@v3`.
- [ ] Upgrade `.github/actions/upload-codecov/action.yml` from
      `codecov/codecov-action@v5` to `@v6`.
- [ ] Replace the dashboard publish chain in `.github/workflows/dashboard.yml`
      so it no longer depends on either `Wandalen/wretry.action` or
      `peaceiris/actions-gh-pages`.
- [ ] Keep the replacement behaviorally equivalent: publish to the external
      `dashboard` repository, preserve existing files, and retry transient push
      failures.
- [ ] Upgrade `.github/workflows/release-notes.yml` from
      `softprops/action-gh-release@v2` to `@v3`.
- [ ] Decide and implement one of the two Drafterino paths:
      update `enhantica/drafterino` upstream to a Node 24-compatible release and
      bump the dependency here, or replace it locally in this repository.
- [ ] Re-run the `.github/` action inventory after the above changes and remove
      `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` only from workflows that no longer
      depend on Node 20 actions.
- [ ] Leave `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` only where there is a known,
      documented upstream blocker.

Stop after Phase 1 and ask for review before starting verification.

## Phase 2 — Verification

- [ ] Validate workflow YAML after edits.
- [ ] Re-scan `.github/workflows/` and `.github/actions/` for external action
      references and confirm the warning-causing refs are gone.
- [ ] Trigger or re-run the affected workflows and inspect logs for Node 20
      deprecation messages:
      `coverage.yml`, reusable `dashboard.yml`, `release-notes.yml`, and any
      workflow that uses `.github/actions/setup-easyscience-bot`.
- [ ] If warnings remain, record the exact action refs and classify them as
      either upgradeable in-repo or blocked on upstream releases.
- [ ] Remove the remaining `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` entries only
      after the corresponding workflows complete without Node 20 warnings.

## Suggested Verification Commands

These are the cheapest local checks before running workflows remotely:

```bash
grep -R "uses:" .github/workflows .github/actions
grep -R "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" .github/workflows
```

Remote verification is required for the actual warning condition because the
warnings are emitted by GitHub-hosted runners, not by local tooling.

## Suggested Branch

`feature/node24-actions-migration`

## Suggested Commit Messages

```text
Upgrade GitHub App token and Codecov actions
Replace dashboard publish actions with shell flow
Migrate release notes workflow off Node 20 actions
Remove temporary Node24 force overrides
```
