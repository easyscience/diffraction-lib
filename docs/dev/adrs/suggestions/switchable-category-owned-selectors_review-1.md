# Review 1: Switchable Category Owned Selectors ADR

Reviewed ADR:
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)

This review follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

No tests, lint, build, or verification commands were run. This is a
static review of the proposed ADR against the accepted ADRs and current
source layout.

## Findings

### F1 — The proposed base cannot cover `background`

The ADR's scope includes `background` as an in-scope switchable category
(`switchable-category-owned-selectors.md:225`), but the proposed
contract is a `SwitchableCategoryBase(CategoryItem)`
(`switchable-category-owned-selectors.md:141`). Current backgrounds are
not `CategoryItem`s; `BackgroundBase` extends `CategoryCollection`
(`src/easydiffraction/datablocks/experiment/categories/background/base.py:11`).

That makes the mechanism incomplete for one of the named migration
targets. A collection-owned selector also has a different persistence
problem from singleton categories: the current background content is
serialized through loop items, not a singleton category descriptor. The
ADR should either define a collection-aware switchable base/contract or
remove `background` from the uniform mechanism and document the explicit
exception.

### F2 — `calculation` is incorrectly included as an instance-swap selector

Section 6 lists `calculation` / `calculator` as in scope
(`switchable-category-owned-selectors.md:225`), but the accepted
selector-family ADR classifies `calculation.calculator_type` as a
backend selector, not a switchable-category selector
(`../accepted/selector-families.md:27`). The code matches that: the
`Calculation` category has one factory tag (`default`) and exposes a
`calculator_type` descriptor inside the category
(`src/easydiffraction/datablocks/experiment/categories/calculation/default.py:20`,
`src/easydiffraction/datablocks/experiment/categories/calculation/default.py:38`),
while `ExperimentBase._set_calculator_type()` swaps the live calculator
backend, not the `calculation` category instance
(`src/easydiffraction/datablocks/experiment/item/base.py:192`).

If this ADR leaves `calculation` in scope, implementers will conflate two
selector families and may rename a backend selector to `calculation.type`
without actually moving an instance-swap category. The ADR should remove
`calculation` from scope, or explicitly amend `selector-families.md` and
define how backend selectors differ from this new category-owned
contract.

### F3 — `show_supported()` cannot mark the current type as written

The public contract requires `category.show_supported()` to mark the
active type with `'*'` (`switchable-category-owned-selectors.md:94`),
but the implementation sketch makes it a `@classmethod`
(`switchable-category-owned-selectors.md:169`). A class method has no
current instance and no owner context, so it cannot reliably know the
active row.

The sketch also calls `cls._factory.show_supported(cls.__mro__[1])`
(`switchable-category-owned-selectors.md:172`), but
`FactoryBase.show_supported()` accepts only keyword filters after `*`
(`src/easydiffraction/core/factory.py:228`). That call would raise before
printing anything. Even if fixed to call the factory without a positional
argument, owner context is still required for filtered categories:
`show_peak_profile_types()` filters by calculator, scattering type, and
beam mode, and applies context-local aliases
(`src/easydiffraction/datablocks/experiment/item/base.py:561`), while
`show_background_types()` filters by calculator
(`src/easydiffraction/datablocks/experiment/item/bragg_pd.py:225`).

The ADR needs an instance-level `show_supported()` contract that obtains
current type and support filters from the owner, or an owner-side private
hook that the category delegates to.

### F4 — `type` is not persisted by the proposed mechanism

The ADR says each switchable category persists exactly one identity tag,
`_<cat>.type` (`switchable-category-owned-selectors.md:111`), but the
mechanism defines `type` as a computed string property over
`type_info.tag` (`switchable-category-owned-selectors.md:155`). Current
generic CIF serialization emits only descriptor parameters:
`CategoryItem.parameters` returns `GenericDescriptorBase` instances
(`src/easydiffraction/core/category.py:70`), and
`category_item_to_cif()` serializes only `item.parameters`
(`src/easydiffraction/io/cif/serialize.py:170`).

As written, `_minimizer.type` and other `_<cat>.type` tags will not be
emitted or read by the existing generic machinery. The ADR should specify
whether `type` is a real descriptor with a `CifHandler`, a computed
property handled by custom CIF hooks, or a category/collection-specific
serialization exception.

### F5 — The peak CIF tag decision is internally inconsistent

The ADR first says the replacement for switchable-category identity is
uniformly `_<cat>.type` (`switchable-category-owned-selectors.md:111`,
`switchable-category-owned-selectors.md:119`), but the footnote says
peak is already collapsed as `_peak.profile_type`
(`switchable-category-owned-selectors.md:126`). The current code indeed
persists peak identity through the `profile_type` descriptor and
`_peak.profile_type` tag
(`src/easydiffraction/datablocks/experiment/categories/peak/base.py:23`).

The implementing plan cannot tell whether peak should keep
`_peak.profile_type` as the one identity tag, rename it to `_peak.type`,
or expose Python `peak.type` while persisting the CIF spelling
`_peak.profile_type`. The ADR should make that choice explicit before it
is accepted.

### F6 — `optimizer_name` and `method_name` are not just selector echoes

The ADR removes `_minimizer.optimizer_name` and
`_minimizer.method_name` as identity echoes
(`switchable-category-owned-selectors.md:130`,
`switchable-category-owned-selectors.md:379`). That conflicts with the
accepted analysis fit-state ADR, which treats them as persisted
deterministic optimizer metadata
(`../accepted/analysis-cif-fit-state.md:93`). The current code stores
them from the live backend after a fit
(`src/easydiffraction/analysis/analysis.py:1387`) and uses them when
restoring `FitResults` from saved state
(`src/easydiffraction/analysis/analysis.py:739`).

They may be derivable from the minimizer tag in many cases, but the ADR
does not prove that equivalence or define the replacement restoration
path. Removing them as "duplicate by construction" risks dropping saved
fit metadata and breaking restored deterministic result objects. The ADR
should either keep these fields as fit-result metadata or explicitly
amend the accepted fit-state ADR and implementation contract for
restoring `FitResults.optimizer_name` and `FitResults.method_name`.

### F7 — Stale category references can still mutate the live owner

Section 5 documents stale references as an orphan-editing problem and
declares guarding out of scope
(`switchable-category-owned-selectors.md:212`). The proposed swap body
sets the new instance's parent and replaces the owner slot
(`switchable-category-owned-selectors.md:180`), but it never detaches the
old instance. Current guarded assignment automatically gives nested
objects a `_parent` reference when they are assigned to private owner
attributes (`src/easydiffraction/core/guard.py:77`).

After this sequence:

```python
m = project.analysis.minimizer
m.type = 'bumps (dream)'
```

`m` is stale, but it still has `_parent` pointing at `project.analysis`.
A later `m.type = 'lmfit'` would call the parent swap hook again from an
object that is no longer the live category. That is more dangerous than
editing an orphaned object's descriptors. The ADR should require the
swap hook to detach the old instance or require the setter to verify
that `self` is still the owner's live slot before mutating the owner.

## Checks Skipped

Per reviewer instructions, no tests, lint, build, or `pixi` commands were
run. The next implementer should run the normal verification sequence
after the ADR and implementation plan are updated.
