"""Reverse-engineer Z-Rietveld's actual alpha/beta rates by fitting its peaks.

Extract isolated peaks from Z-Rietveld output and fit them with the
profile function to determine what rates ZR actually uses.

Focus on (220) at TOF≈19229 (strongest, well isolated).
"""
import numpy as np
from scipy.optimize import minimize
from cryspy.A_functions_base.powder_diffraction_tof_zcode import (
    calc_profile, calc_h_g, calc_h_com, calc_eta, calc_h_l,
    calc_sigma_square, calc_r_0,
)

# Z-Rietveld parameters
sigma_0_sq, sigma_1_sq, sigma_2_sq = 0.0, 225.55267, 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

# Load ZR data
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',
                      skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# ZR Bragg positions and d-spacings (from the file)
peaks = [
    ("111", 31397, 3.124418, 600),
    ("200", 27192, 2.705826, 400),
    ("220", 19229, 1.913308, 300),
    ("311", 16399, 1.631674, 200),
    ("222", 15701, 1.562209, 200),
    ("400", 13598, 1.352913, 200),
    ("331", 12478, 1.241518, 150),
    ("420", 12162, 1.210082, 150),
    ("422", 11103, 1.104649, 120),
]


def compute_zcode_intermediates(d):
    """Compute all intermediate Z-code values for a given d-spacing."""
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    sigma = np.sqrt(s2)
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)
    eta = calc_eta(h_l, h_com)
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    return sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1


def fit_single_peak(hkl, tof_center, d, hw, verbose=True):
    """Fit a single peak from ZR output to extract alpha, beta rates."""
    sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1 = compute_zcode_intermediates(d)

    # Extract ZR peak data
    mask = (zr_tof >= tof_center - hw) & (zr_tof <= tof_center + hw)
    t = zr_tof[mask]
    y_bragg = zr_ycalc[mask] - zr_bg[mask]  # subtract background

    # Skip if no signal
    if np.max(y_bragg) < 1e-5:
        if verbose:
            print(f"  ({hkl}): no signal")
        return None

    # Model: scale * profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
    # Fit for: alpha, beta0, beta1, scale, tof_offset
    def residual(params):
        log_alpha, log_beta0, log_beta1, log_scale, tof_off = params
        alpha = np.exp(log_alpha)
        beta0 = np.exp(log_beta0)
        beta1 = np.exp(log_beta1)
        scale = np.exp(log_scale)
        delta_t = t - tof_center - tof_off
        try:
            prof = calc_profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
            model = scale * prof
            return np.sum((model - y_bragg)**2)
        except Exception:
            return 1e30

    # Initial guess from Hypothesis A (alpha-fixed)
    alpha0 = abs(1 / (A * h_com))
    beta0_0 = abs(1 / (B0 * h_com))
    beta1_0 = abs(1 / (B1 * h_com))
    scale0 = np.max(y_bragg) / max(np.max(calc_profile(
        np.linspace(-hw, hw, 2*hw+1), sigma, h_l, alpha0, beta0_0, beta1_0, r_0)), 1e-10)

    x0 = [np.log(alpha0), np.log(beta0_0), np.log(beta1_0), np.log(max(scale0, 1e-10)), 0.0]

    result = minimize(residual, x0, method='Nelder-Mead',
                     options={'maxiter': 50000, 'xatol': 1e-10, 'fatol': 1e-12})

    alpha_fit = np.exp(result.x[0])
    beta0_fit = np.exp(result.x[1])
    beta1_fit = np.exp(result.x[2])
    scale_fit = np.exp(result.x[3])
    tof_off_fit = result.x[4]

    # What "normalization" factor would give these rates?
    # rate = 1/(prime * N), so N = 1/(prime * rate)
    N_alpha = 1 / (abs(A) * alpha_fit)
    N_beta0 = 1 / (abs(B0) * beta0_fit)
    N_beta1 = 1 / (abs(B1) * beta1_fit)

    if verbose:
        delta_t_plot = t - tof_center - tof_off_fit
        prof_fit = calc_profile(delta_t_plot, sigma, h_l, alpha_fit, beta0_fit, beta1_fit, r_0)
        fwhm_fit = np.sum(prof_fit > 0.5*np.max(prof_fit)) * (t[1]-t[0])
        fwhm_zr = np.sum(y_bragg > 0.5*np.max(y_bragg)) * (t[1]-t[0])

        print(f"\n  ({hkl}) at d={d:.4f}, TOF≈{tof_center}:")
        print(f"    sigma={sigma:.2f}, h_l={h_l:.2f}, h_g={h_g:.1f}, h_com={h_com:.1f}")
        print(f"    A={A:.4f}, B0={B0:.4f}, B1={B1:.4f}, r_0={r_0:.4f}")
        print(f"    Fitted: alpha={alpha_fit:.6f}, beta0={beta0_fit:.6f}, beta1={beta1_fit:.6f}")
        print(f"    Scale={scale_fit:.4f}, tof_offset={tof_off_fit:.1f}")
        print(f"    FWHM: fit={fwhm_fit:.0f}, ZR={fwhm_zr:.0f}")
        print(f"    N_alpha={N_alpha:.1f}, N_beta0={N_beta0:.1f}, N_beta1={N_beta1:.1f}")
        print(f"    h_com={h_com:.1f}, h_g={h_g:.1f}, sigma={sigma:.2f}")
        print(f"    Ratios: N_alpha/h_com={N_alpha/h_com:.4f}, N_beta0/h_com={N_beta0/h_com:.4f}")
        print(f"    Ratios: N_alpha/sigma={N_alpha/sigma:.4f}, N_beta0/sigma={N_beta0/sigma:.4f}")
        print(f"    RMS residual: {np.sqrt(result.fun/len(t)):.6f}")

    return alpha_fit, beta0_fit, beta1_fit, N_alpha, N_beta0, N_beta1


print("=" * 90)
print("Fitting Z-Rietveld peaks to extract actual alpha/beta rates")
print("=" * 90)

results = {}
for hkl, tof_c, d, hw in peaks:
    r = fit_single_peak(hkl, tof_c, d, hw)
    if r is not None:
        results[hkl] = r

# Summary
print(f"\n{'='*90}")
print("Summary: normalization factors N (where rate = 1/(|prime| * N))")
print(f"{'='*90}")
print(f"{'hkl':>5} {'d':>6} {'h_com':>7} {'N_alpha':>8} {'N_beta0':>8} {'N_beta1':>8} | {'N_a/hcom':>8} {'N_b0/hcom':>8}")
print("-" * 80)
for hkl, tof_c, d, hw in peaks:
    if hkl not in results:
        continue
    alpha_f, beta0_f, beta1_f, Na, Nb0, Nb1 = results[hkl]
    sigma, h_l, h_g, h_com, *_ = compute_zcode_intermediates(d)
    print(f"{hkl:>5} {d:>6.3f} {h_com:>7.1f} {Na:>8.1f} {Nb0:>8.1f} {Nb1:>8.1f} | {Na/h_com:>8.4f} {Nb0/h_com:>8.4f}")
