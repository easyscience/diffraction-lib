# ADR: Switchable Category Owned Selectors

## Status

Proposed.

## Date

2026-05-23

## Group

User-facing API and CIF mapping.

## Context

Today every switchable category — `analysis.minimizer`,
`experiment.background`, `experiment.peak`, `experiment.extinction`,
`experiment.calculation`, … — exposes its selector at owner level per
[`switchable-category-api.md`](switchable-category-api.md):

```python
analysis.minimizer_type = 'bumps (lm)'
analysis.minimizer                          # read-only
analysis.show_supported_minimizer_types()   # method on owner
analysis.show_current_minimizer_type()      # method on owner
```

Three problems have accumulated since that ADR landed:

1. **Two-scope UX.** The category instance lives at `analysis.minimizer`
   (read-only). The thing you assign lives at `analysis.minimizer_type`
   (writable). Every supported show-method is on the owner. A scientist
   looking at `analysis.minimizer.help()` sees the configuration
   descriptors but cannot change the active backend from that surface;
   they have to go back up one level. The same split applies to
   background, peak, etc.

2. **CIF duplication.** The owner-level convention persists a tag like
   `_fitting.minimizer_type = 'bumps (lm)'` _and_ the swapped category
   records its identity again — e.g.
   `_minimizer.optimizer_name = 'bumps (lm)'`. The two values are by
   construction equal; one of them is dead weight in every saved
   project. The codebase is also inconsistent: `_background.type` and
   `_peak.profile_type` already collapse the duplication;
   `_fitting.minimizer_type` does not.
   [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
   notes the inconsistency under §"Owner-level switchable selectors" and
   tags it for a future ADR.

3. **Cross-cutting inconsistency.** Issue [#76](../../issues/open.md)
   ("Consistent `_type` suffix in switchable-category API names")
   tracked the inconsistency in the _method names_ on the owner, but
   assumed the owner-level model stayed.
   [`fit-mode-categories.md`](fit-mode-categories.md) §"Deferred Work"
   explicitly records:

   > "A separate ADR for changing switchable category selectors globally
   > from owner-level names such as `peak_profile_type` toward
   > category-owned selectors such as `peak.profile_type`."

   This ADR is that follow-up.

The
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
work just landed; it intentionally preserved `_fitting.minimizer_type`
because the broader convention had not yet been amended. With that PR
merged, the path is clear to amend the convention now.

## Decision

### 1. The category owns its selector

Every instance-swap switchable category exposes:

```python
category.type             # writable property (str)
category.show_supported() # one method, current marked with '*'
```

That is the entire public selector surface. Nothing else. Setting
`category.type = 'X'` triggers the parent to swap the underlying
instance.

Owner-level shims are removed (no `<owner>.<cat>_type`, no
`show_supported_<cat>_types()`, no `show_current_<cat>_type()`). The
owner exposes only the category itself, e.g. `analysis.minimizer`.

The owner still owns the swap mechanism (it holds the slot) but the swap
is _initiated_ from the category through a back-reference.

### 2. `show_current()` is intentionally omitted

`category.show_supported()` marks the active type with `'*'` in its
table, so a dedicated "show current" method would print a strict subset
of the same information. The machine-readable accessor is
`category.type`. Three paths cover every reasonable user need:

| User wants                         | API                         |
| ---------------------------------- | --------------------------- |
| The active type as a string        | `category.type`             |
| The active type printed            | `print(category.type)`      |
| The full table, active row starred | `category.show_supported()` |

A separate `show_current()` method is therefore not added, and the
existing owner-level `show_current_<cat>_type()` methods are removed in
step with the rest of this ADR.

### 3. CIF mapping is collapsed to one tag per category

Each switchable category persists exactly one identity tag —
`_<cat>.type` — and its own descriptors. The owner-level selector tags
are dropped:

| Today (will be removed)                                | Replacement                              |
| ------------------------------------------------------ | ---------------------------------------- |
| `_fitting.minimizer_type`                              | `_minimizer.type`                        |
| `_fitting.mode_type` ¹                                 | `_fitting.mode_type` (kept — not a swap) |
| owner-level peak/background/extinction selector tags ² | `_<cat>.type`                            |

¹ `_fitting.mode_type` is _not_ an instance-swap selector; it is a plain
`FitModeEnum` on `Analysis` (per
[`fit-mode-categories.md`](fit-mode-categories.md)). It keeps its
current home.

² Already collapsed for `_background.type` and `_peak.profile_type` per
[`python-cif-category-correspondence.md`](python-cif-category-correspondence.md);
this ADR documents the convention and makes it uniform.

Identity-echo fields that the backend libraries re-report (e.g.
`_minimizer.optimizer_name`, `_minimizer.method_name`) are **removed**.
They duplicate `_<cat>.type` by construction. Backends that actually
carry independent sub-method information (none today, but emcee's
`proposal_moves` is the model) keep their distinct descriptor.

### 4. Mechanism: back-reference + parent-side swap hook

A behavior-only base records the contract:

```python
class SwitchableCategoryBase(CategoryItem):
    """Behavior-only base for instance-swap switchable categories.

    The concrete subclasses still declare their own descriptors in
    their class body (no mixins, per the parent ADR). This base
    contributes only the back-reference, the ``type`` selector
    property, and ``show_supported()`` plus the contract for the
    owner-side swap hook.
    """

    _parent: object | None = None
    _swap_method_name: ClassVar[str]          # e.g. '_swap_minimizer'
    _factory: ClassVar[type[FactoryBase]]

    @property
    def type(self) -> str:
        """Active factory tag for this category."""
        return str(self.type_info.tag)

    @type.setter
    def type(self, value: str) -> None:
        if self._parent is None:
            raise RuntimeError(
                f'{type(self).__name__} is not attached to an owner; '
                'cannot change type before the category is owned.'
            )
        getattr(self._parent, self._swap_method_name)(value)

    @classmethod
    def show_supported(cls) -> None:
        """Show supported types; the active type is marked '*'."""
        cls._factory.show_supported(cls.__mro__[1])
```

The owner provides one private `_swap_<name>` method per switchable
category:

```python
class Analysis:
    def _swap_minimizer(self, new_type: str) -> None:
        new_minimizer = MinimizerCategoryFactory.create(new_type)
        self._warn_about_minimizer_swap_defaults(
            self._minimizer, new_minimizer,
        )
        new_minimizer._parent = self
        self._minimizer = new_minimizer
        self._fitter = Fitter(new_type)
```

The owner sets `_parent` after construction and after every swap. The
existing swap-warning helpers (introduced in P2.7) move into the owner's
`_swap_<name>` body so the warning still fires on type changes.

### 5. Reference-staleness is documented behaviour

A user that holds a reference to the _old_ instance and then swaps
through it will keep editing the orphaned object:

```python
m = project.analysis.minimizer       # binds to instance A
m.type = 'bumps (dream)'              # owner replaces A with B
m.sampling_steps = 3000               # writes to A — surprising
```

The intended pattern goes through the live property each time:

```python
project.analysis.minimizer.type = 'bumps (dream)'
project.analysis.minimizer.sampling_steps = 3000
```

For the scientist audience this is the natural workflow (one chained
attribute path per statement). The library does not guard against the
staleness; it is documented in the category's `help()` and in the
user-facing docs. A future refactor could emit a `log.warn(...)` from
the `type` setter when `self is not self._parent.<cat>` afterwards, but
that is out of scope for this ADR.

### 6. Scope: instance-swap selectors only

This ADR applies only to selectors that swap a category _instance_ at
runtime via a factory. Per
[`selector-families.md`](selector-families.md):

- **Switchable-category selectors** (in scope): `minimizer`,
  `background`, `peak` / `peak_profile`, `extinction`, `calculation`
  (`calculator`), and any future category fitting the same shape.
- **Plain enum descriptors** (out of scope): `fitting_mode_type`,
  `radiation_probe`, `beam_mode`, `sample_form`, `scattering_type`,
  `adp_type`. These do not swap an instance; they keep whatever form the
  existing ADR specifies.
- **Backend selectors at module scope** (out of scope): factory tag
  lookups that never appear as a user-facing property.

The plan that implements this ADR will enumerate the exact set of
affected categories at the start of Phase 1.

### 7. Beta posture: hard cutover, no shims

[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
→ **Change Discipline**: "Project is in beta: no legacy shims, no
deprecation warnings — update tests and tutorials to the current API."
This ADR keeps that posture:

- `<owner>.<cat>_type` is **deleted**, not deprecated.
- `show_supported_<cat>_types()` / `show_current_<cat>_type()` are
  deleted.
- Owner-level CIF selector tags are deleted.
- Identity-echo CIF fields are deleted.
- Every tutorial, test, and example CIF is migrated.

Existing saved projects under `tmp/tutorials/projects/*` regenerate from
script tests, matching the precedent set by
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

## Consequences

### Architecture wins

- One uniform API surface per category: `type`, `show_supported()`, and
  the category's own descriptors. No two-scope split.
- `category.help()` becomes self-contained: it lists every property the
  user can read or write _for that category_, including the type
  selector. Discoverability is single-step.
- CIF projects shrink by one tag per switchable category plus any
  redundant identity-echo fields. The remaining `_<cat>.*` block is a
  self-describing record of the active backend's state.
- The convention extends naturally to future switchable categories.
  Adding emcee, a new background flavor, a new peak profile, etc. costs
  one class plus factory registration; no owner-side selector plumbing.

### Trade-offs

- Reference-staleness is a real but documented quirk (see §5). The
  scientist workflow does not hit it; expert users who store a reference
  and then swap have a documented gotcha.
- The migration is cross-cutting. Every test, tutorial, and saved
  fixture that touches a switchable selector needs an edit. Order of
  magnitude: dozens of test files, every tutorial, every saved
  `analysis.cif` / `experiment.cif`.
- Two beta-period CIF formats coexist briefly (consolidation just
  shipped). Anyone with projects saved in the post-consolidation format
  needs to regenerate; the project's beta posture covers this.

### ADRs that need to be updated when this ADR is accepted

- [`switchable-category-api.md`](switchable-category-api.md) — rewrite
  the §"Decision" to point at this ADR. The new contract is "the
  category exposes `type` (getter+setter) and `show_supported()`; the
  owner exposes only the category itself".
- [`selector-families.md`](selector-families.md) — update the
  switchable-category-selector row to show the new location
  (`<owner>.<cat>.type`, not `<owner>.<cat>_type`).
- [`fit-mode-categories.md`](fit-mode-categories.md) — strike the
  matching "Deferred Work" entry; this ADR closes that follow-up.
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — the §"Owner-level switchable selectors" table becomes obsolete;
  remove the "deliberate abstraction" exception.
- [`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
  — append a "Superseded selector layout" note pointing here for the
  `_fitting.minimizer_type` change.

### Issues that this ADR closes

- [#72 "Warn on All Switchable-Category Type Changes"](../../issues/open.md)
  — the warning logic moves into each owner's `_swap_<name>` method;
  uniform by construction.
- [#76 "Consistent `_type` suffix in switchable-category API names"](../../issues/open.md)
  — superseded; the new convention drops the suffix entirely.

## Alternatives Considered

### A. `__class__` mutation on the existing instance

Replace `self.__class__` with the new concrete class so the user's
reference keeps pointing at "the same object". Rejected:
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
→ **Architecture** forbids it ("no monkey-patching or runtime class
mutation"). It would also confuse `isinstance` checks and break
descriptor introspection.

### B. Single category class with internal mode switching

One `MinimizerCategory` class with a `type` attribute that reconfigures
internal state. Rejected: conflicts with
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
§8 ("concrete classes carry their own defaults; no mixins"). Loses
per-backend type signatures and `help()` output.

### C. Proxy / handle layer

`analysis.minimizer` returns a `SwitchableHandle[MinimizerCategoryBase]`
that wraps the concrete instance and delegates via `__getattr__`.
Rejected: the user wants the _category_ to be the interface, not a
wrapper that looks like one. `isinstance` checks, descriptor
introspection, factory metadata, and `help()` all need bespoke
delegation. The cost is much higher than the back-reference approach for
no extra capability.

### D. Keep owner-level setters; just deduplicate CIF

Strip `_fitting.minimizer_type` from CIF while leaving the Python API at
owner level. Rejected: fixes the CIF duplication but leaves the UX split
(the original complaint). Half a solution at the cost of a separate
amendment ADR.

### E. Hybrid: writable `type` on category + alias on owner

Keep `<owner>.<cat>_type` as a thin alias that forwards to
`<owner>.<cat>.type` setter, "for backwards compatibility". Rejected:
beta posture explicitly says "no legacy shims, no deprecation warnings".
Dual surfaces double the API and the documentation burden.

## Example: minimizer in the new shape

`analysis.cif` after this ADR:

```
data_analysis

_fitting.mode_type        joint

_minimizer.type                       'bumps (dream)'
_minimizer.sampling_steps             3000
_minimizer.burn_in_steps              600
_minimizer.thinning_interval          1
_minimizer.population_size            4
_minimizer.parallel_workers           0
_minimizer.initialization_method      latin_hypercube
_minimizer.random_seed                ?
_minimizer.runtime_seconds            124.7
_minimizer.acceptance_rate_mean       0.27
_minimizer.gelman_rubin_max           1.03
_minimizer.effective_sample_size_min  482
_minimizer.best_log_posterior        -1234.56
_minimizer.reduced_chi2               1.18
```

`_fitting.minimizer_type` is gone; `_minimizer.optimizer_name`,
`_minimizer.method_name` are gone. The active backend is named exactly
once, as `_minimizer.type`.

Python:

```python
project.analysis.minimizer.show_supported()
project.analysis.minimizer.type = 'bumps (dream)'
project.analysis.minimizer.sampling_steps = 3000
project.analysis.minimizer.help()
```

Same shape for `experiment.background`, `experiment.peak`,
`experiment.extinction`, `experiment.calculation` — to be enumerated
exactly in the implementing plan.
