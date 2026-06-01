# Plan: Python and CIF Category Correspondence

Follows [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions.

> **Status:** Phase 1 implementation complete; awaiting implementation
> review. The ADR review cycle closed at
> `python-cif-category-correspondence_review-2.md` with the final-review
> sentinel. The review/reply artifacts have already been removed from
> the active tree.

## ADR

- Primary ADR:
  [`python-cif-category-correspondence.md`](../adrs/accepted/python-cif-category-correspondence.md)
  (Accepted).
- Referenced accepted ADRs:
  - [`project-facade-and-persistence.md`](../adrs/accepted/project-facade-and-persistence.md)
  - [`project-summary-rendering.md`](../adrs/accepted/project-summary-rendering.md)
  - [`iucr-cif-tag-alignment.md`](../adrs/accepted/iucr-cif-tag-alignment.md)
  - [`loop-category-key-identity.md`](../adrs/accepted/loop-category-key-identity.md)
  - [`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md)

## Branch and PR

- Branch: current branch, `crysview-structure-visualization`.
- PR target: `develop`.
- Do not push the branch unless asked.

## Decisions

- Promote the reviewed ADR from `suggestions/` to `accepted/`.
- Keep the ADR as a documentation-only decision record. It records the
  current correspondence policy and does not require source-code
  behavior changes.
- Update ADR index and cross-references so accepted ADRs no longer point
  to the old suggestion path.
- Preserve the clean-report policy: no v1 `project.publication` owner
  and no empty journal/publication placeholders.

## Open Questions

None.

## Concrete Files Likely To Change

- `docs/dev/adrs/accepted/python-cif-category-correspondence.md`
  (status and accepted-location link fixes after the move).
- `docs/dev/adrs/index.md`.
- Accepted ADRs that link to the suggestion path:
  - `docs/dev/adrs/accepted/iucr-cif-tag-alignment.md`
  - `docs/dev/adrs/accepted/project-summary-rendering.md`
  - `docs/dev/adrs/accepted/switchable-category-owned-selectors.md`

## Commit Discipline

When an AI agent follows this plan, every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or the Phase 1
review gate. Follow the rules in [`AGENTS.md`](../../../AGENTS.md) →
**Commits**.

## Implementation Steps (Phase 1)

- [x] **P1.1 - Promote the ADR to accepted**
  - Move the ADR from `docs/dev/adrs/suggestions/` to
    `docs/dev/adrs/accepted/`.
  - Change ADR status from `Proposed` to `Accepted`.
  - Remove the suggestion-only status note.
  - Update `docs/dev/adrs/index.md` to mark the ADR as accepted and
    point to the accepted path.
  - Update accepted ADR cross-references that still point to
    `../suggestions/python-cif-category-correspondence.md`.
  - Commit: `Promote Python-CIF correspondence ADR`

- [x] **P1.2 - Phase 1 review gate**
  - Mark this checklist item complete after P1.1 is committed.
  - Commit: `Reach Python-CIF correspondence Phase 1 review gate`

## Verification Commands (Phase 2)

Run the standard Phase 2 sequence:

```shell
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

Use the zsh-safe log-capture pattern from `AGENTS.md` if a command's
output needs to be preserved for analysis, for example:

```shell
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
```

## Suggested Pull Request

Title: Accept Python and CIF category correspondence

Description: Records the current Python-to-CIF naming policy so project
configuration remains predictable while scientific CIF categories keep
their domain-specific names.
