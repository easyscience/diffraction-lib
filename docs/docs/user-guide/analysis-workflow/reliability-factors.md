---
title: Reliability Factors
icon: material/chart-bell-curve-cumulative
---

# :material-chart-bell-curve-cumulative: Reliability Factors

EasyDiffraction reports several complementary measures of agreement
between observed and calculated diffraction data. They are ratios
internally; values shown with a percent sign are multiplied by 100.

For the equations below, $y_i^{\mathrm{obs}}$ and $y_i^{\mathrm{calc}}$
are the observed and calculated intensities, $\sigma_i$ is the standard
uncertainty of the observed intensity, and

$$
w_i = \frac{1}{\sigma_i^2}
$$

is its inverse-variance weight. The sum runs over the $N$ data points
included in the reported value.

## R-factor (Rf)

The unweighted profile R-factor is the absolute difference between
observed and calculated intensities, normalized by the total absolute
observed intensity:

$$
R_f =
\frac{\sum_i \left|y_i^{\mathrm{obs}}-y_i^{\mathrm{calc}}\right|}
     {\sum_i \left|y_i^{\mathrm{obs}}\right|}.
$$

Lower values indicate closer agreement. This factor does not use the
measurement uncertainties, so every data point contributes according to
the magnitude of its absolute residual.

## Squared-residual R-factor (Rf²)

The value labelled `Rf²` in the fit summary is the unweighted
root-squared-residual ratio:

$$
R_{f^2} =
\left[
\frac{\sum_i \left(y_i^{\mathrm{obs}}-y_i^{\mathrm{calc}}\right)^2}
     {\sum_i \left(y_i^{\mathrm{obs}}\right)^2}
\right]^{1/2}.
$$

Despite the compact `Rf²` label, this is not the algebraic square of
$R_f$. The label indicates that squared intensities and residuals are
used before taking the square root.

## Weighted R-factor (wR)

The weighted R-factor is the root ratio of weighted squared residuals:

$$
wR =
\left[
\frac{\sum_i w_i
    \left(y_i^{\mathrm{obs}}-y_i^{\mathrm{calc}}\right)^2}
     {\sum_i w_i \left(y_i^{\mathrm{obs}}\right)^2}
\right]^{1/2},
\qquad
w_i = \frac{1}{\sigma_i^2}.
$$

Consequently, a point with a smaller standard uncertainty has more
influence than a less precise point. EasyDiffraction expects standard
uncertainties as input and converts them to inverse-variance weights; it
does not use $\sigma_i$ itself as the weight.

## Chi-square and reduced chi-square

The uncertainty-weighted sum of squared residuals is

$$
\chi^2 =
\sum_i \left(
\frac{y_i^{\mathrm{obs}}-y_i^{\mathrm{calc}}}{\sigma_i}
\right)^2
= \sum_i w_i
\left(y_i^{\mathrm{obs}}-y_i^{\mathrm{calc}}\right)^2.
$$

If $p$ free parameters were fitted, the number of degrees of freedom is
$\nu=N-p$, and the reported goodness-of-fit is the reduced chi-square:

$$
\chi_\nu^2 = \frac{\chi^2}{\nu}.
$$

A value near 1 means that the size of the residuals is consistent with
the stated standard uncertainties. A much larger value can indicate a
poor model or underestimated uncertainties; a much smaller value can
indicate overestimated uncertainties or an over-flexible model.

For a joint fit, EasyDiffraction also multiplies each experiment's
squared normalized residuals by its normalized joint-fit weight. Those
experiment weights are normalized so that their sum equals the number of
experiments.

## Expected weighted profile R-factor

For powder fits, the expected weighted profile R-factor is

$$
wR_{\mathrm{expected}} =
\left[
\frac{\nu}
     {\sum_i w_i \left(y_i^{\mathrm{obs}}\right)^2}
\right]^{1/2}.
$$

It is the weighted profile R-factor expected when $\chi_\nu^2=1$.
Therefore, $wR / wR_{\mathrm{expected}} = \sqrt{\chi_\nu^2}$ when the
same data points and weights are used for both values.

## Bragg R-factor (BR)

When observed and calculated structure-factor magnitudes are available,
EasyDiffraction can report the Bragg R-factor:

$$
BR =
\frac{\sum_h \left|F_h^{\mathrm{obs}}-F_h^{\mathrm{calc}}\right|}
     {\sum_h F_h^{\mathrm{obs}}}.
$$

Here $h$ indexes reflections and $F_h$ is a structure-factor magnitude.
Lower values indicate closer agreement between observed and calculated
reflection amplitudes.

## Names and data subsets

The fit summary uses the short labels `Rf`, `Rf²`, `wR`, and `BR`. Saved
deterministic fit results also expose IUCr-style names:

| Saved result         | Definition and scope                                             |
| -------------------- | ---------------------------------------------------------------- |
| `R_factor_all`       | $R_f$ for all included observations                              |
| `wR_factor_all`      | $wR$ for all included observations                               |
| `R_factor_gt`        | $R_f$ for observations satisfying $y_i^{\mathrm{obs}}>3\sigma_i$ |
| `wR_factor_gt`       | $wR$ for observations satisfying $y_i^{\mathrm{obs}}>3\sigma_i$  |
| `prof_R_factor`      | $R_f$ for all included powder-profile points                     |
| `prof_wR_factor`     | $wR$ for all included powder-profile points                      |
| `prof_wR_expected`   | $wR_{\mathrm{expected}}$ for all included powder-profile points  |
| `reduced_chi_square` | $\chi_\nu^2$ for the fitted residual vector                      |

Only finite observations with finite calculated values and positive,
finite standard uncertainties are included in saved deterministic
statistics. A metric is unavailable when its denominator is zero or when
it does not apply to the fitted data.
