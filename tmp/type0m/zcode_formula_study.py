"""Study the Z-code type0m formulas to match Z-Rietveld peak shapes.

Compare multiple formula variants for converting Z-code parameters into
the back-to-back exponential rates (alpha, beta_0, beta_1).

Z-Rietveld reference FWHM (from shape_check.py analysis):
  d=3.12  FWHM=156  asym=0.928
  d=1.91  FWHM=84   asym=0.821
  d=1.05  FWHM=44   asym=1.010
  d=0.72  FWHM=28   asym=0.923
"""
import numpy as np
from scipy.special import erfc, erfcx, exp1

# ── Z-Rietveld parameters (from screenshots) ──
sigma_0_sq = 0.0
sigma_1_sq = 225.55267
sigma_2_sq = 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

zr_ref = {3.12: (156, 0.928), 1.91: (84, 0.821), 1.05: (44, 1.010), 0.72: (28, 0.923)}


# ── Profile building blocks (from CrysPy, proven correct) ──
def calc_n(a, b):
    return 0.5 * a * b / (a + b)

def calc_h_g(sigma):
    return np.sqrt(8 * np.log(2)) * sigma

def calc_h_com(h_g, h_l):
    return (h_g**5 + 2.69269*h_g**4*h_l + 2.42843*h_g**3*h_l**2
            + 4.47163*h_g**2*h_l**3 + 0.07842*h_g*h_l**4 + h_l**5)**0.2

def calc_eta(h_l, h_com):
    x = h_l / h_com
    return 1.36603*x - 0.47719*x**2 + 0.11116*x**3

def calc_e_beta_g(delta_t, sigma, alpha, beta):
    """Back-to-back exponential convolved with Gaussian."""
    n = calc_n(alpha, beta)
    u = 0.5 * alpha * (alpha * sigma**2 + 2*delta_t)
    v = 0.5 * beta * (beta * sigma**2 - 2*delta_t)
    y = (alpha * sigma**2 + delta_t) / (sigma * np.sqrt(2))
    z = (beta * sigma**2 - delta_t) / (sigma * np.sqrt(2))
    w = -0.5 * (delta_t / sigma)**2
    with np.errstate(over='ignore', invalid='ignore'):
        t1 = np.exp(w) * erfcx(y)
        t2 = np.exp(w) * erfcx(z)
    mask1 = ~np.isfinite(t1)
    if np.any(mask1):
        with np.errstate(over='ignore'):
            t1[mask1] = 2.0 * np.exp(u[mask1])
    mask2 = ~np.isfinite(t2)
    if np.any(mask2):
        with np.errstate(over='ignore'):
            t2[mask2] = 2.0 * np.exp(v[mask2])
    return n * (t1 + t2)

def _stable_exp_times_exp1(z):
    result = np.zeros_like(z)
    large = np.abs(z.real) > 500
    small = ~large
    if np.any(small):
        zs = z[small]
        with np.errstate(over='ignore', invalid='ignore'):
            prod = np.exp(zs) * exp1(zs)
        prod[~np.isfinite(prod)] = 0
        result[small] = prod
    if np.any(large):
        iz = 1.0 / z[large]
        result[large] = iz * (1 - iz*(1 - iz*(2 - iz*(6 - iz*24))))
    return result

def calc_e_beta_l(delta_t, h_l, alpha, beta):
    """Back-to-back exponential convolved with Lorentzian."""
    n = calc_n(alpha, beta)
    p = alpha * delta_t + 0.5j * alpha * h_l
    q = -beta * delta_t + 0.5j * beta * h_l
    exp_p_E1_p = _stable_exp_times_exp1(p)
    exp_q_E1_q = _stable_exp_times_exp1(q)
    return -2*n/np.pi * (np.imag(exp_p_E1_p) + np.imag(exp_q_E1_q))

def calc_profile(delta_t, sigma, h_l, alpha, beta_0, beta_1, r_0):
    """Full type0m profile: weighted sum of two pseudo-Voigt-exponential convolutions."""
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)
    eta = calc_eta(h_l, h_com)
    pv0 = eta * calc_e_beta_l(delta_t, h_l, alpha, beta_0) + (1-eta) * calc_e_beta_g(delta_t, sigma, alpha, beta_0)
    pv1 = eta * calc_e_beta_l(delta_t, h_l, alpha, beta_1) + (1-eta) * calc_e_beta_g(delta_t, sigma, alpha, beta_1)
    return r_0 * pv0 + (1 - r_0) * pv1

def measure_peak(delta_t, prof):
    """Measure FWHM and asymmetry of a profile."""
    mx = np.max(prof)
    hm = mx / 2
    above = prof > hm
    dt = delta_t[1] - delta_t[0]
    fwhm = np.sum(above) * dt
    pk = np.argmax(prof)
    left = np.sum(prof[:pk]) * dt
    right = np.sum(prof[pk:]) * dt
    asym = left / right if right > 0 else float('inf')
    return fwhm, asym


# ── Z-code intermediate values for each d ──
def compute_intermediates(d):
    sigma_sq = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    sigma = np.sqrt(sigma_sq)
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)
    eta = calc_eta(h_l, h_com)
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    return sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1


# ── Formula variants ──
# The key question: how to convert A (alpha_prime), B0, B1 to actual rates?
# CrysPy current: alpha_prime = 1/A, then alpha = 1/(alpha_prime * h_com) = A/h_com  [BUG]
# Fix v1 (consistent): alpha = 1/(A*h_com), beta0 = 1/(B0*h_com), beta1 = 1/(B1*h_com)
# Fix v2 (Z-Rietveld?): maybe h_com is NOT used for the exponential rates?
# Fix v3: maybe the rates are alpha=A, beta=B directly (no h_com?)
# Fix v4: maybe it's 1/(param * sigma) not 1/(param * h_com)?

delta_t = np.linspace(-2000, 2000, 400001)

formulas = {
    "CrysPy bug:  A/H, 1/(B*H)":     lambda A, B, H, sig: (abs(A/H), abs(1/(B*H))),
    "Fix v1: 1/(A*H), 1/(B*H)":       lambda A, B, H, sig: (abs(1/(A*H)), abs(1/(B*H))),
    "Fix v2: A, B (no H)":            lambda A, B, H, sig: (abs(A), abs(B)),
    "Fix v3: 1/A, 1/B (no H)":        lambda A, B, H, sig: (abs(1/A), abs(1/B)),
    "Fix v4: 1/(A*sig), 1/(B*sig)":   lambda A, B, H, sig: (abs(1/(A*sig)), abs(1/(B*sig))),
    "Fix v5: 1/(A*h_g), 1/(B*h_g)":   lambda A, B, H, sig: (abs(1/(A*calc_h_g(sig))), abs(1/(B*calc_h_g(sig)))),
}

print(f"{'Formula':<35} | ", end="")
for d in sorted(zr_ref.keys(), reverse=True):
    print(f"d={d}: FWHM(asym)  ZR={zr_ref[d][0]}({zr_ref[d][1]:.2f}) | ", end="")
print()
print("-" * 180)

for name, fn in formulas.items():
    print(f"{name:<35} | ", end="")
    for d in sorted(zr_ref.keys(), reverse=True):
        sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1 = compute_intermediates(d)
        alpha_rate, beta0_rate = fn(A, B0, h_com, sigma)
        _, beta1_rate = fn(A, B1, h_com, sigma)
        try:
            prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
            fwhm, asym = measure_peak(delta_t, prof)
            print(f"  {fwhm:6.0f} ({asym:.2f})           | ", end="")
        except Exception as e:
            print(f"  ERROR: {e!s:.20s}   | ", end="")
    print()

# ── Now try the correct Z-code interpretation ──
# In the Z-code paper (Ikeda-Carpenter), the profile is:
#   Ω(t) = (1-R)·α·β₀/(α-β₀)·[exp(-β₀·Δt) - exp(-α·Δt)]     for Δt > 0
#        + R·α·β₁/(α-β₁)·[exp(-β₁·Δt) - exp(-α·Δt)]          for Δt > 0
#   convolved with a pseudo-Voigt
#
# Where α, β₀, β₁ are RATES (1/μs), and the Z-code parametrizes:
#   α(d) = α₁ + α₂/d     ← direct rate, NOT inverted through h_com!
#   β₀(d) = β₀₀ + β₀₁/d  ← direct rate
#   β₁(d) = β₁₀            ← direct rate
#
# The "type0m" MULTIPLIES by h_com to make them dimensionless, then
# the profile function divides back. Let me try direct rates.

print(f"\n{'='*80}")
print("Direct-rate interpretation: alpha = A, beta = B (actual rates in 1/μs)")
print(f"{'='*80}")
for d in sorted(zr_ref.keys(), reverse=True):
    sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1 = compute_intermediates(d)
    alpha_rate = abs(A)
    beta0_rate = abs(B0)
    beta1_rate = abs(B1)
    prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure_peak(delta_t, prof)
    ref_fwhm, ref_asym = zr_ref[d]
    print(f"  d={d:.2f}: alpha={alpha_rate:.4f}, beta0={beta0_rate:.4f}, beta1={beta1_rate:.4f}")
    print(f"          FWHM={fwhm:.0f} (ZR={ref_fwhm}), asym={asym:.3f} (ZR={ref_asym:.3f})")


# ── What alpha/beta values would give the correct FWHM? ──
# Use binary search for each d
print(f"\n{'='*80}")
print("What global scale factor F gives correct FWHM? (alpha = F/|A*h_com|, beta = F/|B*h_com|)")
print(f"{'='*80}")
for d in sorted(zr_ref.keys(), reverse=True):
    sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1 = compute_intermediates(d)
    ref_fwhm = zr_ref[d][0]

    lo, hi = 0.01, 100.0
    for _ in range(50):
        mid = (lo + hi) / 2
        alpha_rate = mid * abs(1/(A * h_com))
        beta0_rate = mid * abs(1/(B0 * h_com))
        beta1_rate = mid * abs(1/(B1 * h_com))
        prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
        fwhm, _ = measure_peak(delta_t, prof)
        if fwhm > ref_fwhm:
            lo = mid
        else:
            hi = mid
    best_F = (lo + hi) / 2
    alpha_rate = best_F * abs(1/(A * h_com))
    beta0_rate = best_F * abs(1/(B0 * h_com))
    beta1_rate = best_F * abs(1/(B1 * h_com))
    prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure_peak(delta_t, prof)
    print(f"  d={d:.2f}: F={best_F:.4f}, alpha={alpha_rate:.6f}, beta0={beta0_rate:.6f} → FWHM={fwhm:.0f}, asym={asym:.3f} (ZR={zr_ref[d][1]:.3f})")

# ── What if h_com is computed without the Lorentzian part? ──
print(f"\n{'='*80}")
print("What if rates use h_g instead of h_com? (sigma-only, no gamma)")
print(f"{'='*80}")
for d in sorted(zr_ref.keys(), reverse=True):
    sigma, h_l, h_g, h_com, eta, r_0, A, B0, B1 = compute_intermediates(d)
    # Use h_g instead of h_com
    alpha_rate = abs(1/(A * h_g))
    beta0_rate = abs(1/(B0 * h_g))
    beta1_rate = abs(1/(B1 * h_g))
    prof = calc_profile(delta_t, sigma, h_l, alpha_rate, beta0_rate, beta1_rate, r_0)
    fwhm, asym = measure_peak(delta_t, prof)
    ref_fwhm, ref_asym = zr_ref[d]
    print(f"  d={d:.2f}: h_g={h_g:.1f} vs h_com={h_com:.1f}, alpha={alpha_rate:.6f}")
    print(f"          FWHM={fwhm:.0f} (ZR={ref_fwhm}), asym={asym:.3f} (ZR={ref_asym:.3f})")
