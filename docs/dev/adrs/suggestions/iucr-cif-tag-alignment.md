# ADR: IUCr CIF Tag Alignment for Fit Outputs

**Status:** Proposed **Date:** 2026-05-24

## Status Note

This suggestion captures research done during the
[`minimizer-input-output-split`](accepted/minimizer-input-output-split.md)
work. That ADR's `_fit_result.*` CIF prefix is functional but
diverges from the IUCr core and powder dictionaries. This proposal
records the divergence and a plausible alignment path so it is not
lost; the work is **not** in scope for the input/output-split PR.

## Context

After the input/output split, fit outputs persist under
`_fit_result.*`. The IUCr maintains two relevant dictionaries that
already cover much of the same ground:

- [`COMCIFS/cif_core`](https://github.com/COMCIFS/cif_core) — core
  CIF dictionary, refinement parameters under `_refine_ls.*` (51
  items) and aggregate reflection statistics under `_reflns.*`.
- [`COMCIFS/Powder_Dictionary`](https://github.com/COMCIFS/Powder_Dictionary)
  (`cif_pow.dic`) — powder-specific refinement under
  `_pd_proc_ls.*` (9 items).

Cross-reference today:

| Concept | Our `_fit_result.*` | IUCr core (`_refine_ls.*`) | IUCr powder (`_pd_proc_ls.*`) |
| --- | --- | --- | --- |
| Reduced χ² / GoF | `reduced_chi_square` | `goodness_of_fit_all` (S, plus `_su`) | derived from `prof_wR_factor`/`prof_wR_expected` |
| R-factor unweighted | — | `r_factor_all`, `r_factor_gt` | `prof_R_factor` |
| R-factor weighted | — | `wr_factor_all`, `wr_factor_gt`, `wr_factor_ref` | `prof_wR_factor` |
| R-expected | — | (derived from S and counts) | `prof_wR_expected` |
| Number of data points | `n_data_points` | `number_reflns`, `number_reflns_gt` | derive from `_pd_proc.number_of_points` |
| Number of parameters | `n_parameters` | `number_parameters` | (in `_refine_ls.*`) |
| Number of restraints | — | `number_restraints` | same |
| Number of constraints | — | `number_constraints` | same |
| Shift / σ | — | `shift_over_su_max`, `shift_over_su_mean` | same |
| Profile function | — | — | `profile_function` |
| Background function | — | — | `background_function` |
| Wall time | `fitting_time` | (none) | (none) |
| Iteration count | `iterations` | (none) | (none) |
| Success flag, message | `success`, `message` | (none) | (none) |
| Bayesian R̂, ESS, accept | various | (none) | (none) |

Two consequences:

1. **Real gaps.** Our serialization omits R-factors,
   restraint/constraint counts, shift/σ diagnostics, and powder
   profile/background function names. These are fields that
   crystallographers expect in a saved CIF.
2. **Naming divergence.** Where IUCr does have a tag, we use a
   different prefix (`_fit_result.*` vs `_refine_ls.*` /
   `_pd_proc_ls.*`). Our CIFs are valid but cannot be consumed by
   external tools that expect IUCr-standard names.

## Decision

### 1. Use IUCr tag names where they exist

For every `_fit_result.*` field that has a one-to-one IUCr
counterpart, emit the IUCr tag instead. The Python attribute name
stays (`analysis.fit_result.reduced_chi_square`); only the
`cif_handler` `names` tuple changes. Examples:

- `fit_result.reduced_chi_square` → emits
  `_refine_ls.goodness_of_fit_all` for single-crystal,
  `_pd_proc_ls.prof_wR_factor` + `_pd_proc_ls.prof_wR_expected` for
  powder (or both, with the GoF derived on the powder side).
- `fit_result.n_data_points` → `_refine_ls.number_reflns`
  (single-crystal), `_pd_proc.number_of_points` (powder).
- `fit_result.n_parameters` → `_refine_ls.number_parameters`.

The emitted prefix becomes shape-shifting based on
`experiment.type.scattering_type` and `experiment.type.sample_form`
— the same convention powder packages use today. The Python API
remains uniform.

### 2. Add the missing IUCr fields to `fit_result`

Promote the following from "gap" to "available" on the existing
`LeastSquaresFitResult`:

- `r_factor_all`, `wr_factor_all` — emitted as the standard tags;
  computed by the LSQ projection writer from residuals.
- `prof_r_factor`, `prof_wr_factor`, `prof_wr_expected` —
  powder-specific variants, computed the same way against the
  profile data.
- `number_restraints`, `number_constraints` — current count from
  the analysis model.
- `shift_over_su_max`, `shift_over_su_mean` — last-iteration
  convergence diagnostic.
- `profile_function`, `background_function` (powder) — string-form
  descriptions of the active peak and background categories.

### 3. Keep our own prefix for fields IUCr does not cover

`fitting_time`, `iterations`, `success`, `message`, every Bayesian
diagnostic (`gelman_rubin_max`, `acceptance_rate_mean`, etc.), and
the `result_kind`/`point_estimate_name` markers have no IUCr home
today. They stay under a project-specific prefix. Two options for
that prefix:

- Keep `_fit_result.*` for the non-IUCr fields only. The CIF then
  mixes prefixes (`_refine_ls.*` + `_fit_result.*`) which is
  unusual but legal.
- Use a clearly-namespaced extension like `_easydiffraction.*` or
  `_eddict_fit.*` so external tools recognise the fields as
  non-IUCr.

Decide during implementation; the second option is friendlier to
external CIF readers.

### 4. Bayesian Rietveld output has no IUCr precedent today

There is no IUCr convention for sampler convergence (R̂, ESS,
acceptance) or posterior diagnostics. This proposal does not invent
one. The Bayesian-specific fields stay under the project prefix
chosen in §3. If a community standard emerges, a follow-on ADR can
absorb it.

## Consequences

### Positive

- Saved CIFs become consumable by standard IUCr tools (publCIF,
  checkCIF, journal submission pipelines).
- The "what is the R-factor of this fit?" question has an answer in
  the saved file — currently we only record reduced χ².
- Powder users get the conventional Rp / Rwp / Rexp triplet.
- We pick up restraint/constraint accounting that the structure
  side of the project already tracks but does not currently emit.

### Trade-offs

- Shape-shifting CIF prefix per experiment family is more work to
  implement than a single `_fit_result.*` prefix. Roughly: one
  `cif_handler` per descriptor that maps to a different IUCr tag
  depending on context; the Python API stays uniform.
- Bayesian fields remain non-standard. There is no way around that
  until IUCr defines tags for Bayesian Rietveld.
- Existing saved projects from the post-split layout cannot load
  unchanged. Beta posture applies; one more legacy-rename pass in
  tutorial `ed-24` covers it.

### ADRs amended by this ADR

- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — replace the `_fit_result.*` projection description with the
  IUCr-aligned tag set; document the per-experiment-family
  shape-shifting.
- [`minimizer-input-output-split.md`](../accepted/minimizer-input-output-split.md)
  — the `_fit_result.*` examples in §3 are updated to use IUCr tags
  for the covered fields; the non-IUCr fields keep the
  project-prefix examples.

## Deferred Work

- The exact prefix for non-IUCr fields (§3 option choice).
- IUCr-Bayesian alignment if a community standard appears.
- Single-crystal `r_factor_gt` / `wr_factor_gt` (greater-than-σ
  subsets) need a "threshold expression" decision. The
  `_reflns.threshold_expression` field already covers it on the
  reflection side; the LSQ projection writer needs to know the
  threshold to compute the `_gt` variants.
- Whether to also emit `_refine.special_details` for human-readable
  fit notes.

## Alternatives Considered

### A. Keep `_fit_result.*` as-is

Simplest. Saved CIFs stay self-contained but are not IUCr-portable.
Defensible if the project never targets external CIF interop.

### B. Emit both prefixes for the covered fields

`_fit_result.reduced_chi_square` and
`_refine_ls.goodness_of_fit_all` both present, holding the same
value. Belt-and-braces, doubles the surface area of every saved
file, and the two values can drift.

### C. Adopt IUCr tags only for tags we already need

Add the R-factor fields (§2) under our own `_fit_result.*` prefix.
Smaller diff, fixes the missing-field gap but not the naming
divergence. Pick if IUCr interop is genuinely not a goal.
