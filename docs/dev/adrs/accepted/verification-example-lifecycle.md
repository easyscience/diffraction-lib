# ADR: Verification Example Lifecycle

## Status

Accepted.

## Date

2026-06-18

## Group

Quality.

## Context

Verification pages are both public documentation and regression tests.
They compare EasyDiffraction calculations against frozen FullProf
references, and they also explain to scientists what part of the model
has been verified.

Several accepted ADRs already define pieces of this workflow:

- [Test Suite and Validation Strategy](../accepted/test-suite-and-validation.md)
  establishes the Verification docs section and its regression role.
- [Notebook Generation Source of Truth](../accepted/notebook-generation.md)
  makes `.py` notebook sources the editable artifacts.
- [Notebook-Owned Verification Regression Gating](../accepted/verification-regression-flag.md)
  defines `known_discrepancy=True` and its two-sided gating behavior.
- [Software Version Labels on Verification Pages](../accepted/verification-software-version-labels.md)
  requires visible FullProf, EasyDiffraction, and calculator versions.

What is still missing is the authoring convention for future examples.
Recent X-ray and neutron verification work exposed recurring problems:

- filenames mixed abbreviations (`pv`, `tch-fcj`) with negative feature
  names (`noabs`, `nosldl`), making the docs hard to scan;
- diagnostic notebooks could become public pages even when they were
  only temporary investigation tools;
- top-of-notebook prose sometimes explained implementation history
  instead of the specific model term being verified;
- FullProf reference directories, notebook filenames, and documentation
  navigation drifted apart;
- fit sections were sometimes added before deciding whether the raw
  calculation already verified the feature.

This ADR defines how new verification examples are introduced, named,
documented, and retired.

## Decision

### 1. One page verifies one focused model scope

A verification page should verify exactly one baseline or one additional
model term relative to a baseline.

Good examples:

- `pd-neut-cwl_LBCO_basic` — baseline pseudo-Voigt powder neutron CW.
- `pd-neut-cwl_LBCO_preferred-orientation` — the same class of example
  with March-Dollase preferred orientation activated.
- `pd-xray-cwl_LiF_single` — baseline single-wavelength X-ray CW.
- `pd-xray-cwl_LiF_single_polarization` — the same X-ray case with
  polarization activated.

Combined-feature pages are allowed only when the interaction is itself
the thing being verified. Their feature block names every activated
feature, for example `absorption_fcj-asymmetry`.

Avoid negative feature names such as `noabs`, `nosldl`, or
`unpolarized`. The page name should say what the page verifies. A
baseline page uses `basic` or the relevant positive baseline descriptor
(`single`, `doublet`, `jorgensen`, etc.).

### 2. Diagnostic pages are not public verification pages by default

Exploratory notebooks used to isolate a discrepancy are diagnostics, not
Verification pages. They should stay outside the published Verification
navigation unless they have a stable user-facing purpose.

A diagnostic can be promoted only when all of the following are true:

- it has a clear scientific verification question;
- it uses a stable filename following this ADR;
- it has a rendered explanation of the known discrepancy or expected
  agreement;
- it is linked to an open issue when the discrepancy remains.

Otherwise the diagnostic is removed once the investigation is complete,
or kept as local scratch material outside `docs/docs/verification/`.

### 3. Filename convention is experiment, sample, feature

Use this file stem:

```text
<experiment-type>_<sample>_<feature>
```

`<experiment-type>` uses the compact supported experiment tags:

- `pd-neut-cwl`
- `pd-neut-tof`
- `pd-xray-cwl`
- `sc-neut-cwl`

Add new prefixes only when the corresponding experiment type is
supported and the first example lands.

`<sample>` is an ASCII sample or compound token with conventional
capitalization, such as `LBCO`, `PbSO4`, `LiF`, `Si`, `NCAF`,
`Tb2Ti2O7`, or `Pr2NiO4`.

`<feature>` is lowercase ASCII. Use underscores between filename blocks
and hyphens inside multi-word feature names:

```text
pd-neut-cwl_PbSO4_beba-asymmetry.py
pd-neut-cwl_LaB6_absorption.py
pd-neut-tof_Si_jorgensen-von-dreele.py
pd-xray-cwl_LiF_single_polarization.py
```

The `.py` source, generated `.ipynb`, and public docs links use the same
stem.

### 4. FullProf reference directories follow the same naming

By default the FullProf reference directory under
`docs/docs/verification/fullprof/` uses the same stem as the page.

Several closely related pages may share one reference directory when the
directory intentionally contains a family of PCR/profile files for the
same sample and experiment type. In that case the directory still uses a
clear non-cryptic stem, for example:

```text
docs/docs/verification/fullprof/pd-xray-cwl_lif/
```

Do not keep old implementation names such as `pv`, `tch-fcj`, `noabs`,
or temporary diagnostic labels in `FULLPROF_PROJECT_DIR`.

### 5. Store only reference inputs and consumed outputs

Committed FullProf reference folders should contain only files needed to
understand or load the reference:

- the frozen `.pcr`;
- the measured or synthetic input file when needed;
- the calculated profile/background/summary files consumed by the page
  (`.prf`, `.bac`, `.sum`);
- additional FullProf outputs only when the page or an ADR explicitly
  uses them as evidence.

Do not commit ordinary FullProf byproducts such as `.new`, `.sym`,
`.fst`, `.rpa`, `.fou`, `.inp`, or `.out` unless they are consumed or
documented as evidence.

When a `.pcr` changes, regenerate the consumed outputs with FullProf and
commit the `.pcr` plus the regenerated consumed outputs together.

### 6. Notebook titles and index entries are intentionally short

The first markdown cell uses this title shape:

```text
# <Sample> — <experiment type> — <feature>
```

The first paragraph is one or two sentences that state what is verified.
It should not explain implementation history, open design debates, or
long discrepancy background.

Detailed caveats belong next to the relevant calculation, fit, or
agreement section. The Verification index mirrors the same discipline:
one short line per page describing the verified feature.

### 7. Keep source and generated notebooks in lockstep

Verification pages follow the same source-of-truth rule as tutorials:
edit the `.py` source, regenerate the `.ipynb`, and strip outputs.

Manual `.ipynb` edits are allowed only for emergency repair of generated
metadata, and the `.py` source must still be the canonical content.

### 8. Reference-loading blocks use one order

Powder pages that load a FullProf profile use this order:

```python
FULLPROF_PROJECT_DIR = '...'
FULLPROF_PRF_FILE = '...'
FULLPROF_SUM_FILE = '...'
FULLPROF_BAC_FILE = '...'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = ...
```

The blank line after `FULLPROF_LABEL` separates reference provenance
from the experiment parameters.

### 9. Calculate first, fit only to isolate a known difference

Every page first calculates from the frozen FullProf parameters.

Add a fit section only when one of these is true:

- the raw calculation does not agree and the fit isolates a known
  convention or scale difference;
- a `known_discrepancy=True` page needs to show that the engine can
  match when its own equivalent parameters are freed;
- the page is explicitly about refinement behavior.

Fit sections free the smallest parameter set that explains the
difference. Scale-only differences free only scale. Broad "fit
everything" sections are diagnostics and should not be normal published
verification examples.

### 10. Known discrepancies stay explicit and issue-linked

Expected-good comparisons use the default `verify.assert_patterns_agree`
behavior. Known-bad comparisons use `known_discrepancy=True` with a
reason that names the missing feature or convention mismatch and links
to an issue where practical.

Expected-good and known-bad comparisons stay in separate
`assert_patterns_agree` calls, as required by
[Notebook-Owned Verification Regression Gating](../accepted/verification-regression-flag.md).

### 11. Documentation navigation is grouped by experiment type

`docs/docs/verification/index.md` and `docs/mkdocs.yml` use the same
experiment-type groups. Current groups are:

- Powder, neutron, constant wavelength
- Powder, neutron, time-of-flight
- Powder, X-ray, constant wavelength
- Single crystal, neutron, constant wavelength

Add a new group only when the first stable page for that experiment type
is added.

### 12. New-page checklist

Adding or promoting a verification page requires:

- `.py` source and generated `.ipynb` with matching stems;
- a stable FullProf reference directory and `FULLPROF_PROJECT_DIR`;
- a short first markdown cell and one-line index entry;
- versioned labels via `verify.fullprof_label` and
  `verify.engine_label`;
- an agreement check, or a `known_discrepancy=True` check with a reason;
- `docs/docs/verification/index.md` and `docs/mkdocs.yml` entries;
- regenerated consumed FullProf outputs when the `.pcr` changed;
- no temporary diagnostic files or unused FullProf byproducts.

At minimum, run:

```shell
pixi run python -m py_compile docs/docs/verification/*.py
```

Run the new page as a script when it is expected to agree. If the page
is known-discrepant, run enough of the page locally to confirm the
expected known-bad behavior and issue-linked reason.

## Consequences

### Positive

- Verification pages become easier for scientists to scan.
- Future filenames describe experiment type, sample, and verified
  feature instead of FullProf implementation details.
- Diagnostics no longer linger as public documentation by accident.
- FullProf references and notebook pages stay aligned.
- Fit sections carry a clear purpose and do not hide raw calculator
  disagreement.

### Trade-offs

- Adding a page requires more up-front naming and documentation
  discipline.
- Some existing reference directories may remain shared where that is
  clearer than duplicating files.
- Regenerating `.ipynb` files remains noisy, but the source `.py` files
  stay reviewable.

## Compatibility

This ADR is a convention for future work. Existing pages should be
migrated opportunistically when touched, except for stale public
diagnostics or broken navigation links, which should be cleaned up
immediately.

It extends the notebook source-of-truth convention to Verification pages
explicitly. It does not change the accepted `known_discrepancy` or
version-label behavior.

## Alternatives Considered

### Keep verification notebooks free-form

Rejected. Free-form examples are quick to add but make the public
Verification page inconsistent and hard to maintain.

### Separate documentation examples from regression scripts

Rejected. The project deliberately uses Verification pages as both
published explanation and executable cross-engine checks. Splitting them
would duplicate setup and let documentation drift away from tested
behavior.

### Publish every diagnostic notebook

Rejected. Diagnostics are useful during investigation, but public docs
should present stable verification questions. A diagnostic that remains
valuable can be promoted after it meets the same naming, scope, and
gating rules.

### One exhaustive notebook per sample

Rejected. Exhaustive pages become hard to read and hard to debug. Small
feature-focused pages make it clear which model term agrees or fails.

## Deferred Work

- Add a lightweight checker for filename conventions, nav/index target
  existence, `FULLPROF_LABEL` block ordering, and orphaned FullProf
  directories.
- Decide whether large or rarely used FullProf references should move to
  the pinned diffraction data repository instead of staying under
  `docs/docs/verification/fullprof/`.
