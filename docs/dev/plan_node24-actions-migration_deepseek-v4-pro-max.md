# Plan: Migrate GitHub Actions to Node.js 24

**Branch:** `feature/node24-actions` **Date:** 2026-05-05

## Context

GitHub is deprecating Node.js 20 on actions runners:

- **June 2, 2026:** Node.js 24 becomes default
- **September 16, 2026:** Node.js 20 removed from runners

We added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` to 16 workflows as a
temporary measure, but warnings persist because the flag forces Node 24
at runtime while the actions still _target_ Node 20 internally. The
long-term fix is to upgrade every action to a version that natively
targets Node 24, then remove the flag.

## Answers to extra questions

### 1. Why do we see those warnings?

GitHub Actions runners now detect JS actions whose `action.yml` declares
`runs.using: node20`. Even with
`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` (which coerces the runtime to
Node 24), the deprecation warning still fires because the action's
_declared_ target is Node 20.

The first warning ("Node.js 20 actions are deprecated") appears for
actions declaring `node20` when the flag is NOT set. The second warning
("target Node.js 20 but are being forced to run on Node.js 24") appears
when the flag IS set — it's telling you coercion is happening.

### 2. What is needed to fix this?

Upgrade every referenced action to a version whose `action.yml` declares
`runs.using: node24`. Three actions in this repo need attention:

| Action                            | Current | Target | Status                |
| --------------------------------- | ------- | ------ | --------------------- |
| `actions/create-github-app-token` | v2      | v3.1.1 | ✅ Available          |
| `codecov/codecov-action`          | v5      | v6.0.0 | ✅ Available          |
| `Wandalen/wretry.action`          | v3.8.0  | —      | ❌ No Node 24 version |

### 3. Is `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` a good long-term strategy?

No. It's a **temporary bridge** to test Node 24 compatibility before
actions are updated. Long-term, every action should declare `node24`
natively. The flag will eventually be removed by GitHub after the
transition period. Keeping it masks the real problem and may hide
breakage when Node 20 is removed entirely (Sept 2026).

## Changes

### Step 1: Upgrade `actions/create-github-app-token` v2 → v3

**File:** `.github/actions/setup-easyscience-bot/action.yml`

- Change `uses: actions/create-github-app-token@v2` → `@v3`
- v3.1.1 targets Node 24 (added in v3.0.0, Mar 2026)
- Breaking change: v3 requires runner ≥ v2.327.1 (already satisfied on
  `ubuntu-latest`)
- No other input changes needed (`app-id`, `private-key`, `repositories`
  are unchanged)

### Step 2: Upgrade `codecov/codecov-action` v5 → v6

**File:** `.github/actions/upload-codecov/action.yml`

- Change `uses: codecov/codecov-action@v5` → `@v6`
- v6.0.0 targets Node 24 (released Mar 2026)
- This also resolves the `actions/github-script@v7.0.1` (SHA `60a0d83…`)
  sub-dependency warning, since v6 internally uses
  `actions/github-script@v8`
- No input changes needed for our usage

### Step 3: Replace `Wandalen/wretry.action@v3.8.0` with bash retry

**File:** `.github/workflows/dashboard.yml`

`wretry.action` has no Node 24-compatible release (latest v3.8.0 is from
Jan 2025). Replace the retry logic with a bash `while` loop that re-runs
the `peaceiris/actions-gh-pages@v4` deploy step on failure.

The replacement step will:

- Use a bash loop with 3 attempts and 15-second delay between retries
- Call `peaceiris/actions-gh-pages@v4` (a Docker action, no Node.js
  concern)
- Preserve identical behavior

### Step 4: Remove `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`

Once all three actions are updated, no JS action in the repo targets
Node 20. Remove the env var from all 16 workflows that set it.

## Verification (Phase 2)

- [ ] Run `pixi run check` to ensure no lint/format regressions
- [ ] Manually inspect each workflow YAML for syntax validity
- [ ] Trigger a test run via `workflow_dispatch` on `dashboard.yml`,
      `coverage.yml`, and `backmerge.yml` (the workflows most affected
      by the changes)
- [ ] Confirm all deprecation warnings are gone from workflow run logs

## Open Questions

- [ ] Is there a `Wandalen/wretry.action` issue/PR tracking Node 24
      support? If yes, we could defer Step 3 and keep
      `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` in `dashboard.yml` only until
      upstream ships.
