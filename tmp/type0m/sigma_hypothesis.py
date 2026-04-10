"""Test hypothesis: Z-Rietveld σ² = H_G² (Gaussian FWHM²), not standard deviation².

If Z-Rietveld treats σ² as FWHM², then CrysPy's calc_h_g(sigma) applies
sqrt(8·ln2) to what's already a FWHM, making it 2.355x too large.

Correct interpretation would be:
  H_G = sqrt(σ²)                         (σ² IS the FWHM²)
  σ_actual = H_G / sqrt(8·ln2)           (actual std dev for convolution)
  H_com = TCH(H_G, H_L)                  (using CORRECT H_G)
  rates = 1 / (prime * H_com)            (using CORRECT smaller H_com)
"""
import numpy as np
from cryspy.A_functions_base.powder_diffraction_tof_zcode import (
    calc_profile, calc_h_g, calc_h_com, calc_eta,
    calc_h_l, calc_sigma_square, calc_r_0,
    calc_e_beta_g, calc_e_beta_l,
)

# Z-Rietveld parameters
sigma_0_sq = 0.0
sigma_1_sq = 225.55267
sigma_2_sq = 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

zr_ref = {3.12: (156, 0.928), 1.91: (84, 0.821), 1.05: (44, 1.010), 0.72: (28, 0.923)}

# sqrt(8*ln2)
C = np.sqrt(8 * np.log(2))  # ≈ 2.3548

delta_t = np.linspace(-2000, 2000, 400001)
dt = delta_t[1] - delta_t[0]


def measure(prof):
    mx = np.max(prof)
    fwhm = np.sum(prof > 0.5 * mx) * dt
    pk = np.argmax(prof)
    left = np.sum(prof[:pk])
    right = np.sum(prof[pk:])
    asym = left / right if right > 0 else 999
    return fwhm, asym


print("=" * 100)
print("Hypothesis A: σ² = Gaussian std dev² (CrysPy current interpretation)")
print("  H_G = sqrt(8·ln2)·σ,  rates = 1/(prime * h_com)")
print("=" * 100)
print(f"{'d':>5} {'sigma':>7} {'H_G':>7} {'H_L':>6} {'H_com':>7} {'alpha':>8} {'beta0':>8} | {'FWHM':>6} ({'ZR':>3}) {'asym':>6} ({'ZR':>4})")
print("-" * 95)
for d in sorted(zr_ref.keys(), reverse=True):
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    sigma = np.sqrt(s2)
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_g = C * sigma  # CrysPy: σ² is std dev²
    h_com = calc_h_com(h_g, h_l)
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    alpha_rate = abs(1 / (A * h_com))
    beta0_rate = abs(1 / (B0 * h_com))
    beta1_rate = abs(1 / (B1 * h_com))
    prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure(prof)
    ref = zr_ref[d]
    print(f"{d:>5.2f} {sigma:>7.2f} {h_g:>7.1f} {h_l:>6.2f} {h_com:>7.1f} {alpha_rate:>8.5f} {beta0_rate:>8.5f} | {fwhm:>6.0f} ({ref[0]:>3}) {asym:>6.3f} ({ref[1]:>5.3f})")


print()
print("=" * 100)
print("Hypothesis B: σ² = H_G² (Gaussian FWHM²), so σ_actual = sqrt(σ²)/sqrt(8·ln2)")
print("  H_G = sqrt(σ²),  σ_actual = H_G/sqrt(8·ln2),  rates = 1/(prime * h_com)")
print("=" * 100)
print(f"{'d':>5} {'σ_act':>7} {'H_G':>7} {'H_L':>6} {'H_com':>7} {'alpha':>8} {'beta0':>8} | {'FWHM':>6} ({'ZR':>3}) {'asym':>6} ({'ZR':>4})")
print("-" * 95)
for d in sorted(zr_ref.keys(), reverse=True):
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    h_g_actual = np.sqrt(s2)           # σ² is already H_G²
    sigma_actual = h_g_actual / C      # actual Gaussian std dev
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_com = calc_h_com(h_g_actual, h_l)
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    alpha_rate = abs(1 / (A * h_com))
    beta0_rate = abs(1 / (B0 * h_com))
    beta1_rate = abs(1 / (B1 * h_com))
    # Use the ACTUAL sigma for the Gaussian convolution
    prof = calc_profile(delta_t, sigma_actual, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure(prof)
    ref = zr_ref[d]
    print(f"{d:>5.2f} {sigma_actual:>7.2f} {h_g_actual:>7.1f} {h_l:>6.2f} {h_com:>7.1f} {alpha_rate:>8.5f} {beta0_rate:>8.5f} | {fwhm:>6.0f} ({ref[0]:>3}) {asym:>6.3f} ({ref[1]:>5.3f})")


print()
print("=" * 100)
print("Hypothesis C: σ² = H_G², and rates use σ (not h_com)")
print("  H_G = sqrt(σ²),  σ_actual = H_G/C,  rates = 1/(prime * σ_actual)")
print("=" * 100)
print(f"{'d':>5} {'σ_act':>7} {'H_G':>7} {'H_L':>6} {'H_com':>7} {'alpha':>8} {'beta0':>8} | {'FWHM':>6} ({'ZR':>3}) {'asym':>6} ({'ZR':>4})")
print("-" * 95)
for d in sorted(zr_ref.keys(), reverse=True):
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    h_g_actual = np.sqrt(s2)
    sigma_actual = h_g_actual / C
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_com = calc_h_com(h_g_actual, h_l)
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    alpha_rate = abs(1 / (A * sigma_actual))
    beta0_rate = abs(1 / (B0 * sigma_actual))
    beta1_rate = abs(1 / (B1 * sigma_actual))
    prof = calc_profile(delta_t, sigma_actual, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure(prof)
    ref = zr_ref[d]
    print(f"{d:>5.2f} {sigma_actual:>7.2f} {h_g_actual:>7.1f} {h_l:>6.2f} {h_com:>7.1f} {alpha_rate:>8.5f} {beta0_rate:>8.5f} | {fwhm:>6.0f} ({ref[0]:>3}) {asym:>6.3f} ({ref[1]:>5.3f})")


print()
print("=" * 100)
print("Hypothesis D: σ² = H_G², and rates use H_G (= sqrt(σ²))")
print("  H_G = sqrt(σ²),  σ_actual = H_G/C,  rates = 1/(prime * H_G)")
print("=" * 100)
print(f"{'d':>5} {'σ_act':>7} {'H_G':>7} {'H_L':>6} {'H_com':>7} {'alpha':>8} {'beta0':>8} | {'FWHM':>6} ({'ZR':>3}) {'asym':>6} ({'ZR':>4})")
print("-" * 95)
for d in sorted(zr_ref.keys(), reverse=True):
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    h_g_actual = np.sqrt(s2)
    sigma_actual = h_g_actual / C
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_com = calc_h_com(h_g_actual, h_l)
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    alpha_rate = abs(1 / (A * h_g_actual))
    beta0_rate = abs(1 / (B0 * h_g_actual))
    beta1_rate = abs(1 / (B1 * h_g_actual))
    prof = calc_profile(delta_t, sigma_actual, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure(prof)
    ref = zr_ref[d]
    print(f"{d:>5.2f} {sigma_actual:>7.2f} {h_g_actual:>7.1f} {h_l:>6.2f} {h_com:>7.1f} {alpha_rate:>8.5f} {beta0_rate:>8.5f} | {fwhm:>6.0f} ({ref[0]:>3}) {asym:>6.3f} ({ref[1]:>5.3f})")


# ── For Hypothesis B, also compute the percentage error ──
print()
print("=" * 100)
print("Summary: FWHM error (%) for each hypothesis")
print("=" * 100)
hypotheses = {
    "A: σ²=σ², rates/h_com": lambda d, A, B0, B1, sig, hloc, hg, hcom, r0: (
        sig, abs(1/(A*hcom)), abs(1/(B0*hcom)), abs(1/(B1*hcom))
    ),
    "B: σ²=H²_G, rates/h_com": lambda d, A, B0, B1, sig, hloc, hg, hcom, r0: (
        np.sqrt(sig**2 + hloc**2 * 0) and (np.sqrt(sigma_0_sq + sigma_1_sq*d**2 + sigma_2_sq*d**4)/C),
        abs(1/(A*calc_h_com(np.sqrt(sigma_0_sq + sigma_1_sq*d**2 + sigma_2_sq*d**4), hloc))),
        abs(1/(B0*calc_h_com(np.sqrt(sigma_0_sq + sigma_1_sq*d**2 + sigma_2_sq*d**4), hloc))),
        abs(1/(B1*calc_h_com(np.sqrt(sigma_0_sq + sigma_1_sq*d**2 + sigma_2_sq*d**4), hloc)))
    ),
}
# Simpler summary: just list the FWHM values
for label in ["Hyp A (CrysPy+alpha_fix)", "Hyp B (σ²=H_G²)", "Hyp C (σ²=H_G², rate/σ_act)", "Hyp D (σ²=H_G², rate/H_G)"]:
    print(f"\n{label}:")
    for d in sorted(zr_ref.keys(), reverse=True):
        ref = zr_ref[d]
        s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
        h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2

        if "Hyp A" in label:
            sigma = np.sqrt(s2)
            h_g = C * sigma
            h_com = calc_h_com(h_g, h_l)
            sig_prof = sigma
        else:
            h_g = np.sqrt(s2)  # σ² is H_G²
            sigma = h_g / C
            h_com = calc_h_com(h_g, h_l)
            sig_prof = sigma

        A = alpha_1 + alpha_2 / d
        B0 = beta_00 + beta_01 / d
        B1 = beta_10
        r_0 = r_01 * np.exp(-r_02 * d**(-r_03))

        if "rate/σ" in label:
            norm = sig_prof
        elif "rate/H_G" in label:
            norm = h_g
        else:
            norm = h_com

        ar = abs(1 / (A * norm))
        b0r = abs(1 / (B0 * norm))
        b1r = abs(1 / (B1 * norm))

        prof = calc_profile(delta_t, sig_prof, h_l, ar, b0r, b1r, r_0)
        fwhm, asym = measure(prof)
        err = (fwhm - ref[0]) / ref[0] * 100
        print(f"  d={d:.2f}: FWHM={fwhm:>6.0f} (ZR={ref[0]:>3}) err={err:>+5.1f}%  asym={asym:.3f} (ZR={ref[1]:.3f})")
