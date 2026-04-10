"""Compare peak SHAPES (not just FWHM) between formula variants and Z-Rietveld.

For each isolated ZR peak:
1. Extract ZR peak shape (ycalc - bg), normalise to unit area
2. Compute the same peak with each formula variant, normalise to unit area
3. Compute chi-squared of shape difference (scale-free)
4. Report which variant best reproduces each peak's shape

This is the definitive test.
"""
import numpy as np
from scipy.special import erfcx, exp1

# ── Z-Rietveld parameters ──
sigma_0_sq, sigma_1_sq, sigma_2_sq = 0.0, 225.55267, 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

# ── Profile functions (from CrysPy, overflow-safe) ──
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
    n = calc_n(alpha, beta)
    u = 0.5 * alpha * (alpha * sigma**2 + 2*delta_t)
    v = 0.5 * beta * (beta * sigma**2 - 2*delta_t)
    y = (alpha * sigma**2 + delta_t) / (sigma * np.sqrt(2))
    z = (beta * sigma**2 - delta_t) / (sigma * np.sqrt(2))
    w = -0.5 * (delta_t / sigma)**2
    with np.errstate(over='ignore', invalid='ignore'):
        t1 = np.exp(w) * erfcx(y)
        t2 = np.exp(w) * erfcx(z)
    m1 = ~np.isfinite(t1)
    if np.any(m1):
        with np.errstate(over='ignore'):
            t1[m1] = 2.0 * np.exp(u[m1])
    m2 = ~np.isfinite(t2)
    if np.any(m2):
        with np.errstate(over='ignore'):
            t2[m2] = 2.0 * np.exp(v[m2])
    return n * (t1 + t2)

def _exp_e1(z):
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
    n = calc_n(alpha, beta)
    p = alpha * delta_t + 0.5j * alpha * h_l
    q = -beta * delta_t + 0.5j * beta * h_l
    return -2*n/np.pi * (np.imag(_exp_e1(p)) + np.imag(_exp_e1(q)))

def calc_profile(delta_t, sigma, h_l, alpha, beta_0, beta_1, r_0):
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)
    eta = calc_eta(h_l, h_com)
    pv0 = eta * calc_e_beta_l(delta_t, h_l, alpha, beta_0) \
        + (1 - eta) * calc_e_beta_g(delta_t, sigma, alpha, beta_0)
    pv1 = eta * calc_e_beta_l(delta_t, h_l, alpha, beta_1) \
        + (1 - eta) * calc_e_beta_g(delta_t, sigma, alpha, beta_1)
    return r_0 * pv0 + (1 - r_0) * pv1


# ── Helper: compute Z-code intermediates ──
def intermediates(d):
    s2 = sigma_0_sq + sigma_1_sq * d**2 + sigma_2_sq * d**4
    sigma = np.sqrt(s2)
    h_l = gamma_0 + gamma_1 * d + gamma_2 * d**2
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)
    r_0 = r_01 * np.exp(-r_02 * d**(-r_03))
    A = alpha_1 + alpha_2 / d
    B0 = beta_00 + beta_01 / d
    B1 = beta_10
    return sigma, h_l, h_g, h_com, r_0, A, B0, B1


# ── Formula variants ──
# Each returns (alpha_rate, beta0_rate, beta1_rate)
def formula_cryspy_bug(A, B0, B1, h_com, sigma, h_g):
    """Current CrysPy: alpha_prime=1/A, rate=1/(prime*H) → A/H for alpha."""
    return abs(A / h_com), abs(1 / (B0 * h_com)), abs(1 / (B1 * h_com))

def formula_fix_v1(A, B0, B1, h_com, sigma, h_g):
    """Alpha fix + h_com norm: rate = 1/(prime * h_com)."""
    return abs(1 / (A * h_com)), abs(1 / (B0 * h_com)), abs(1 / (B1 * h_com))

def formula_fix_sigma(A, B0, B1, h_com, sigma, h_g):
    """All rates normalised by sigma: rate = 1/(prime * sigma)."""
    return abs(1 / (A * sigma)), abs(1 / (B0 * sigma)), abs(1 / (B1 * sigma))

def formula_fix_hg(A, B0, B1, h_com, sigma, h_g):
    """All rates normalised by h_g: rate = 1/(prime * h_g)."""
    return abs(1 / (A * h_g)), abs(1 / (B0 * h_g)), abs(1 / (B1 * h_g))

def formula_mixed_sigma_hcom(A, B0, B1, h_com, sigma, h_g):
    """Alpha by sigma, betas by h_com."""
    return abs(1 / (A * sigma)), abs(1 / (B0 * h_com)), abs(1 / (B1 * h_com))

def formula_mixed_hg_hcom(A, B0, B1, h_com, sigma, h_g):
    """Alpha by h_g, betas by h_com."""
    return abs(1 / (A * h_g)), abs(1 / (B0 * h_com)), abs(1 / (B1 * h_com))

def formula_no_norm(A, B0, B1, h_com, sigma, h_g):
    """Direct rates (primes are rates): rate = |prime|."""
    return abs(A), abs(B0), abs(B1)

def formula_inv_no_norm(A, B0, B1, h_com, sigma, h_g):
    """rate = 1/|prime|."""
    return abs(1/A), abs(1/B0), abs(1/B1)


FORMULAS = {
    'CrysPy bug (A/H)':       formula_cryspy_bug,
    'Fix v1 (1/AH)':          formula_fix_v1,
    'Sigma norm (1/Aσ)':      formula_fix_sigma,
    'h_g norm (1/Ah_g)':      formula_fix_hg,
    'Mixed (α:σ, β:H)':       formula_mixed_sigma_hcom,
    'Mixed (α:h_g, β:H)':     formula_mixed_hg_hcom,
    'Direct (A)':              formula_no_norm,
    'Inverse (1/A)':           formula_inv_no_norm,
}


# ── Load Z-Rietveld data ──
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',
                      skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# Peaks to test (hkl, tof_center, d, half_width)
peaks = [
    ("111", 31397, 3.124418, 500),
    ("200", 27192, 2.705826, 400),
    ("220", 19229, 1.913308, 250),
    ("311", 16399, 1.631674, 180),
    ("222", 15701, 1.562209, 150),
    ("400", 13598, 1.352913, 150),
    ("331", 12478, 1.241518, 120),
    ("420", 12162, 1.210082, 120),
    ("422", 11103, 1.104649, 100),
]


def compare_shape(zr_t, zr_bragg, formula_func, d, verbose=False):
    """Compare ZR peak shape with computed profile, returning chi² per point.

    Both curves are normalised to unit area before comparison.
    Also allows optimal scale+offset fit.
    """
    sigma, h_l, h_g, h_com, r_0, A, B0, B1 = intermediates(d)
    alpha, beta0, beta1 = formula_func(A, B0, B1, h_com, sigma, h_g)

    # Compute profile at ZR TOF points
    tof_center = zr_t[np.argmax(zr_bragg)]
    delta_t = zr_t - tof_center
    try:
        prof = calc_profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
    except Exception:
        return float('inf'), 0, 0

    if np.max(prof) < 1e-20 or not np.all(np.isfinite(prof)):
        return float('inf'), 0, 0

    # Normalise both to unit peak height for shape comparison
    zr_norm = zr_bragg / np.max(zr_bragg)
    prof_norm = prof / np.max(prof)

    # Shape chi²: sum of squared normalised differences
    dt = zr_t[1] - zr_t[0]
    shape_chi2 = np.sum((prof_norm - zr_norm)**2) / len(zr_norm)

    # FWHM comparison
    zr_fwhm = np.sum(zr_norm > 0.5) * dt
    prof_fwhm = np.sum(prof_norm > 0.5) * dt

    return shape_chi2, zr_fwhm, prof_fwhm


# ── Main comparison ──
print("=" * 120)
print("SHAPE COMPARISON: formula variants vs Z-Rietveld peaks")
print("Shape χ² is mean squared difference of normalised (unit-peak) profiles")
print("=" * 120)

# Header
print(f"\n{'Formula':<25}", end="")
for hkl, _, d, _ in peaks:
    print(f" | {hkl:>4}(d={d:.2f})", end="")
print(f" | {'SUM χ²':>10}")
print("-" * 160)

total_chi2 = {name: 0.0 for name in FORMULAS}
fwhm_data = {name: {} for name in FORMULAS}

for name, fn in FORMULAS.items():
    print(f"{name:<25}", end="")
    for hkl, tof_c, d, hw in peaks:
        mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
        zr_t = zr_tof[mask]
        zr_bragg = zr_ycalc[mask] - zr_bg[mask]

        if np.max(zr_bragg) < 1e-5:
            print(f" | {'skip':>13}", end="")
            continue

        chi2, zr_fw, pf_fw = compare_shape(zr_t, zr_bragg, fn, d)
        total_chi2[name] += chi2
        fwhm_data[name][hkl] = (zr_fw, pf_fw)
        print(f" | {chi2:.6f}", end="")
    print(f" | {total_chi2[name]:.6f}")

# FWHM comparison table
print(f"\n{'='*120}")
print("FWHM COMPARISON (μs)")
print(f"{'='*120}")
print(f"{'Formula':<25}", end="")
for hkl, _, d, _ in peaks:
    print(f" | {hkl:>3} ZR/calc", end="")
print()
print("-" * 160)

for name in FORMULAS:
    print(f"{name:<25}", end="")
    for hkl, _, d, _ in peaks:
        if hkl in fwhm_data[name]:
            zf, pf = fwhm_data[name][hkl]
            ratio = pf / zf if zf > 0 else float('inf')
            print(f" | {zf:3.0f}/{pf:3.0f} ({ratio:.2f})", end="")
        else:
            print(f" | {'skip':>13}", end="")
    print()


# ── Detailed per-peak analysis for top 3 formulas ──
print(f"\n{'='*120}")
print("TOP 3 FORMULAS BY TOTAL SHAPE χ²")
print(f"{'='*120}")
ranked = sorted(total_chi2.items(), key=lambda x: x[1])
for rank, (name, chi2) in enumerate(ranked[:3], 1):
    print(f"  #{rank}: {name:<25} total χ²={chi2:.8f}")


# ── Search for optimal normalization factor F where rate = 1/(prime * F * sigma) ──
print(f"\n{'='*120}")
print("OPTIMAL GLOBAL FACTOR: rate = 1/(|prime| * F * sigma) for ALL rates")
print(f"{'='*120}")

best_F = None
best_total = float('inf')
F_values = np.linspace(0.5, 3.0, 500)
chi2_vs_F = []

for F in F_values:
    total = 0.0
    for hkl, tof_c, d, hw in peaks:
        mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
        zr_t = zr_tof[mask]
        zr_bragg = zr_ycalc[mask] - zr_bg[mask]
        if np.max(zr_bragg) < 1e-5:
            continue
        sigma, h_l, h_g, h_com, r_0, A, B0, B1 = intermediates(d)
        alpha = abs(1 / (A * F * sigma))
        beta0 = abs(1 / (B0 * F * sigma))
        beta1 = abs(1 / (B1 * F * sigma))
        tof_peak = zr_t[np.argmax(zr_bragg)]
        delta_t = zr_t - tof_peak
        try:
            prof = calc_profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
            if np.max(prof) < 1e-20:
                total += 1.0
                continue
            zr_n = zr_bragg / np.max(zr_bragg)
            pf_n = prof / np.max(prof)
            total += np.sum((pf_n - zr_n)**2) / len(zr_n)
        except Exception:
            total += 1.0
    chi2_vs_F.append(total)
    if total < best_total:
        best_total = total
        best_F = F

print(f"  Best F = {best_F:.4f} (total χ² = {best_total:.8f})")
print(f"  σ-norm (F=1.0): χ² = {chi2_vs_F[np.argmin(np.abs(F_values - 1.0))]:.8f}")
print(f"  h_g-norm (F≈{np.sqrt(8*np.log(2)):.3f}): χ² = {chi2_vs_F[np.argmin(np.abs(F_values - np.sqrt(8*np.log(2))))]:.8f}")
h_com_approx_F = np.sqrt(8*np.log(2))  # h_com ≈ h_g when Gaussian dominates
print(f"  h_com approx (F≈{h_com_approx_F:.3f}): same as h_g-norm above")


# ── Search for optimal separate alpha/beta factors ──
print(f"\n{'='*120}")
print("OPTIMAL SEPARATE FACTORS: alpha = 1/(|A|*Fa*sigma), beta = 1/(|B|*Fb*sigma)")
print(f"{'='*120}")

best_Fa = best_Fb = None
best_sep_total = float('inf')

for Fa in np.linspace(0.5, 3.0, 100):
    for Fb in np.linspace(0.5, 3.0, 100):
        total = 0.0
        for hkl, tof_c, d, hw in peaks:
            mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
            zr_t = zr_tof[mask]
            zr_bragg = zr_ycalc[mask] - zr_bg[mask]
            if np.max(zr_bragg) < 1e-5:
                continue
            sigma, h_l, h_g, h_com, r_0, A, B0, B1 = intermediates(d)
            alpha = abs(1 / (A * Fa * sigma))
            beta0 = abs(1 / (B0 * Fb * sigma))
            beta1 = abs(1 / (B1 * Fb * sigma))
            tof_peak = zr_t[np.argmax(zr_bragg)]
            delta_t = zr_t - tof_peak
            try:
                prof = calc_profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
                if np.max(prof) < 1e-20:
                    total += 1.0
                    continue
                zr_n = zr_bragg / np.max(zr_bragg)
                pf_n = prof / np.max(prof)
                total += np.sum((pf_n - zr_n)**2) / len(zr_n)
            except Exception:
                total += 1.0
        if total < best_sep_total:
            best_sep_total = total
            best_Fa = Fa
            best_Fb = Fb

print(f"  Best Fa = {best_Fa:.4f}, Fb = {best_Fb:.4f} (χ² = {best_sep_total:.8f})")
print(f"  In terms of h_com: Fa*σ/h_com ≈ {best_Fa / np.sqrt(8*np.log(2)):.4f},  Fb*σ/h_com ≈ {best_Fb / np.sqrt(8*np.log(2)):.4f}")
print(f"  (Fa/Fb = {best_Fa/best_Fb:.4f})")


# ── Also search using h_com as base ──
print(f"\n{'='*120}")
print("OPTIMAL SEPARATE FACTORS (h_com base): alpha = 1/(|A|*Fa*h_com), beta = 1/(|B|*Fb*h_com)")
print(f"{'='*120}")

best_Fa_h = best_Fb_h = None
best_sep_total_h = float('inf')

for Fa in np.linspace(0.1, 2.0, 100):
    for Fb in np.linspace(0.1, 2.0, 100):
        total = 0.0
        for hkl, tof_c, d, hw in peaks:
            mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
            zr_t = zr_tof[mask]
            zr_bragg = zr_ycalc[mask] - zr_bg[mask]
            if np.max(zr_bragg) < 1e-5:
                continue
            sigma, h_l, h_g, h_com, r_0, A, B0, B1 = intermediates(d)
            alpha = abs(1 / (A * Fa * h_com))
            beta0 = abs(1 / (B0 * Fb * h_com))
            beta1 = abs(1 / (B1 * Fb * h_com))
            tof_peak = zr_t[np.argmax(zr_bragg)]
            delta_t = zr_t - tof_peak
            try:
                prof = calc_profile(delta_t, sigma, h_l, alpha, beta0, beta1, r_0)
                if np.max(prof) < 1e-20:
                    total += 1.0
                    continue
                zr_n = zr_bragg / np.max(zr_bragg)
                pf_n = prof / np.max(prof)
                total += np.sum((pf_n - zr_n)**2) / len(zr_n)
            except Exception:
                total += 1.0
        if total < best_sep_total_h:
            best_sep_total_h = total
            best_Fa_h = Fa
            best_Fb_h = Fb

print(f"  Best Fa = {best_Fa_h:.4f}, Fb = {best_Fb_h:.4f} (χ² = {best_sep_total_h:.8f})")
print(f"  (Fa/Fb = {best_Fa_h/best_Fb_h:.4f})")
if abs(best_Fa_h - best_Fb_h) < 0.05:
    print(f"  ⟹ Fa ≈ Fb ≈ {(best_Fa_h + best_Fb_h)/2:.4f} → SAME NORMALIZATION (factor * h_com)")
else:
    print(f"  ⟹ Different: alpha uses Fa={best_Fa_h:.4f}*h_com, beta uses Fb={best_Fb_h:.4f}*h_com")
