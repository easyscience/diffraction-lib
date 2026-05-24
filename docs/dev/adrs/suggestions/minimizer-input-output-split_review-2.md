# Review 2: Minimizer Input/Output Split

Context: no `minimizer-input-output-split_reply-1.md` file was present.
This review covers the direct edits made to
`minimizer-input-output-split.md` after review 1.

## Findings

1. **High — The `fit_result` selector exception is still internally inconsistent and not actually wired into the amended-ADR list.** The updated text says `fit_result` is not a user-facing switchable category, and claims this is an explicit exception to `switchable-category-owned-selectors.md` with new exception text added there and listed under "ADRs amended" (`minimizer-input-output-split.md:88-99`). But the same ADR still calls it "the new `fit_result` switchable" and says "`fit_result` becomes a switchable category" in later sections (`:269-278`, `:302-311`, `:342-345`), while the "ADRs amended" list still omits `switchable-category-owned-selectors.md` (`:320-333`). That leaves the core architectural contract unresolved: is `fit_result` a switchable category with an exception, or an internal paired projection that should not use switchable terminology? Please make the terminology consistent and either add the actual selector-ADR amendment/list entry or remove the claim that it has been amended.

2. **High — Configurable credible interval levels make the persisted `_fit_parameter` interval columns misleading.** The update promotes `credible_interval_inner` and `credible_interval_outer` to user-writable settings, but keeps the persisted per-parameter columns named `posterior_interval_68_*` and `posterior_interval_95_*` even when the user chooses different levels; the ADR only says to warn at fit time (`minimizer-input-output-split.md:138-153`). That means a saved CIF can contain, for example, a 50% interval in a column named `posterior_interval_68_low`, which is a data-integrity problem rather than just a UX warning. Please either constrain those settings to the two fixed levels until generalized column names are designed, or include the generalized persistence shape in this ADR so the saved column names match the values they contain.

3. **Medium — `objective_value` and `reduced_chi_square` are still described as duplicates after the ADR now says they are distinct fields.** The decision now says `LeastSquaresFitResult.objective_value` is raw χ² and `FitResultBase.reduced_chi_square` is χ² divided by degrees of freedom, and explicitly says they are not duplicates (`minimizer-input-output-split.md:175-183`). However the context still lists `minimizer.objective_value` vs `fit_result.reduced_chi_square` as the overlapping χ² concept (`:40-46`), and the consequences still say the `objective_value`/`reduced_chi_square` duplication collapses to one location (`:284-289`). Please revise the context/consequences so the duplication being fixed is the old cross-category placement, not a claim that raw objective and reduced χ² are the same scalar.

4. **Medium — `analysis.show_fit_summary()` still bypasses the accepted display facade.** The ADR still adds an analysis-level display method and uses it as the mitigation for two-place reads (`minimizer-input-output-split.md:255-258`, `:304-307`). The accepted Display UX ADR makes `project.display` the user-facing display facade and puts fit reporting under `project.display.fit.results()` (`../accepted/display-ux.md:42-46`, `:66-101`, `:190-201`), and this ADR still does not list `display-ux.md` as amended (`minimizer-input-output-split.md:320-333`). Please move this summary to the accepted display facade or explicitly amend the display ADR.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
