# Verification pages: absolute-scale comparison from FullProf parameters

Reference: [`AGENTS.md`](../../../AGENTS.md). This plan deliberately
removes the peak-normalisation ("autoscaling") currently applied in the
verification comparison helpers and the comparison plots, replacing it
with an **absolute** comparison seeded from each FullProf reference's
own refined parameters (including the PCR scale factor). Where an engine
then disagrees, the differing parameter is refined per engine — the same
pattern the `pd-neut-cwl_pv-asym_empir_pbso4` page already uses for the
empirical asymmetry.

## ADR

No new ADR. This is a methodology change to the documentation
Verification pages and their backing helpers, within the scope of the
accepted `test-strategy.md`. If the absolute-comparison methodology
proves durable it can be promoted to an ADR later; flag in
`docs/dev/issues/open.md` instead for now.

## Motivation

The comparison helpers and plots peak-normalise both curves, which hides
each engine's absolute intensity scale. Investigation showed:

- The EasyDiffraction→FullProf scale equals FullProf's **refined
  Rietveld scale** stored in each `.pcr` (e.g. asym PbSO₄
  `Scale = 1.463902`). `crysfml` reproduces it to 0.01–0.04% for CWL
  pseudo-Voigt.
- `cryspy` and `crysfml` agree to ~0.3% for **CWL** but diverge by **84×
  (TOF Si)** and **282× (TOF NCAF)** — a real engine-convention
  difference that normalisation hid.
- Starting every page from FullProf's exact parameters and comparing
  absolute makes "what differs, per engine, and by how much" explicit
  and consistent across pages.

## Decisions (settled with the user)

1. **Metrics → relative %.** Drop peak-normalisation in
   `pattern_closeness`. Keep `profile_difference_percent` (relative RMS)
   and `correlation` (scale-free). Rename `max_deviation` →
   `max_deviation_percent` = `100 · max|ref−cand| / max(ref)`.
   `intensity_ratio` becomes the **absolute** area ratio
   `sum(cand)/sum(ref)` (≈1 when the scale matches). Existing tolerance
   _values_ carry over unchanged because the old normalisation peak was
   100 (deviations were already effectively percentages).
2. **Refinement → per-engine, conditional.** Each page sets scale from
   the PCR and compares absolute. Only where an engine disagrees does
   the page add a refinement section that frees the differing
   parameter(s) for **that engine** and reports the refined value,
   following the asym-PbSO₄ template.
3. **Scope → powder + single-crystal.** De-normalise both the powder
   pattern comparison and the SC reflection comparison; set each page's
   PCR scale. Leave the broken `lab6` peak-shape issue as a separately
   flagged problem (not fixed here).
4. **Remove** `scale_to_reference` and `report_reference_scales` and the
   "Absolute intensity scale" report cells added earlier — superseded by
   setting the PCR scale directly and the absolute metrics.

## Open questions / known limitations

- **SC extinction:** FullProf `F2cal = Scale · Corr_ext · |F|²` with
  `Ext1 = 0.1054E-03` (model 1) for `pr2nio4`; EasyDiffraction cryspy
  has no extinction model, so the absolute SC comparison keeps a
  per-reflection extinction residual that **cannot** be refined away.
  The page should state this explicitly: extinction is the differing
  "parameter", and it is not yet modelled. Tolerances for the SC page
  may need to stay reporting-only (`raise_on_failure=False`).
- **TOF cryspy shape:** Si cryspy carries a ~21.8% _shape_ difference
  (not just scale); refining scale will not close it. The page should
  refine scale to expose the residual and note the remaining shape gap.
- **lab6:** _not_ broken — a deliberate, ready-to-finish skeleton
  already skipped via `ci_skip.txt` and `raise_on_failure=False`,
  pending issue #117 (`SyCos`/`SySin`), the ¹¹B scattering length, the
  Thompson–Cox–Hastings profile, and the FullProf polynomial background.
  The large mismatch is expected. Keep it skipped; the `SyCos`/`SySin`
  values are kept as commented-out code lines (FullProf `.pcr` values)
  so they can be uncommented when the feature lands. Note its scale
  comment claims `# FullProf Scale` but uses `136.0485` while the `.pcr`
  refined value is `141.0817`; reconcile to the PCR value.
- **PCR scale per page** (refined Rietveld scales): asym-pbso4
  `1.463902`, pv-pbso4 `1.467791`, lbco `9.405646`, lab6 `141.0817`, si
  `0.6750988`, ncaf `4.019921` (main phase), pr2nio4 `0.06298`
  (`linked_crystal.scale`).

## Concrete files likely to change

- `src/easydiffraction/analysis/verification.py` — remove
  `_PEAK_NORMALISATION`, `_peak_normalised`, `scale_to_reference`,
  `report_reference_scales`; rewrite `pattern_closeness` for absolute +
  relativised metrics; rename `max_deviation` field; update
  `ClosenessMetrics`, `_agreement_checks`, `closeness_annotation`,
  `report_refinement_closeness`.
- `src/easydiffraction/display/plotting.py` — drop `_peak_normalized` in
  `plot_calc_comparison` (line ~784) and `plot_reflection_comparison`
  (line ~863); plot absolute ref/cand and raw residual. Remove the
  `_peak_normalized` staticmethod (~893) if unused afterwards.
- `docs/docs/verification/*.py` (7) + regenerated `*.ipynb` — set PCR
  scale; remove the report cell; add per-engine refinement sections
  where agreement is poor; SC page sets `linked_crystal.scale` and
  documents extinction.
- `tests/unit/easydiffraction/analysis/test_verification.py`,
  `tests/unit/easydiffraction/display/plotters/test_plotly_coverage.py`
  — update for the new metric names/semantics (Phase 2).
- `docs/dev/issues/open.md` — log TOF engine-scale disparity, Si cryspy
  shape gap, lab6 shape failure, SC extinction.

## Implementation steps (Phase 1)

- [ ] **P1.1 — Rewrite metrics in `verification.py`.** Remove
      normalisation + the two scale helpers; absolute + relativised
      metrics; rename `max_deviation` → `max_deviation_percent`; keep
      tolerance values. Commit:
      `Compare verification patterns on absolute intensities`.
- [ ] **P1.2 — De-normalise the comparison plots.** Update
      `plot_calc_comparison` and `plot_reflection_comparison`; remove
      the unused helper. Commit:
      `Plot verification comparisons at absolute scale`.
- [ ] **P1.3 — CWL pseudo-Voigt pages (lbco, pv-pbso4).** PCR scale
      already set; remove the report cell; confirm absolute agreement
      passes. Commit:
      `Drop scale report from CWL pseudo-Voigt verification pages`.
- [ ] **P1.4 — asym-PbSO₄ page.** Remove report cell; keep PCR scale;
      keep the existing cryspy asymmetry refinement (now the per-engine
      conditional section). Commit:
      `Seed asym-PbSO4 verification from FullProf scale`.
- [ ] **P1.5 — TOF pages (si, ncaf).** Set PCR scale; remove report
      cell; add a per-engine scale-refinement section that exposes the
      84×/282× convention gap (and the Si cryspy shape residual).
      Commit: `Refine engine scale in TOF verification pages`.
- [ ] **P1.6 — SC page (pr2nio4).** Set
      `linked_crystal.scale = 0.06298`; de-normalised reflection
      comparison; document the un-modelled extinction residual;
      `raise_on_failure=False`. Commit:
      `Compare single-crystal F-squared at absolute scale`.
- [ ] **P1.7 — lab6 page.** Keep CI-skipped; reconcile scale to the PCR
      value (`141.0817`); keep `SyCos`/`SySin` as uncomment-ready
      commented code lines with the FullProf `.pcr` values (done).
      Commit: `Prepare lab6 SyCos/SySin lines for uncommenting`.
- [ ] **P1.8 — Regenerate notebooks.** `pixi run notebook-prepare`;
      commit the regenerated `*.ipynb`. Commit:
      `Regenerate verification notebooks`.
- [ ] **P1.9 — Phase 1 review gate.** No code; mark complete and request
      review.

## Verification commands (Phase 2)

```
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

## Suggested Pull Request

**Title:** Compare verification pages against FullProf at absolute scale

**Description:** The cross-engine Verification pages now start from each
FullProf reference's own refined parameters — including its intensity
scale — and compare calculated patterns on their true absolute scale
instead of peak-normalising them. Where a calculation engine disagrees,
the page refines the specific parameter that differs (scale, asymmetry)
and reports it, so each page shows clearly and consistently how the two
calculators differ from FullProf and from each other.
