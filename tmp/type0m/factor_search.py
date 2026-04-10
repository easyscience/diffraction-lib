"""Fine-grained search for the optimal normalization factor.

Tests specific mathematically-meaningful factors near the optimum F≈1.2.
"""
import numpy as np
from scipy.special import erfcx, exp1

# Z-Rietveld parameters
sigma_0_sq, sigma_1_sq, sigma_2_sq = 0.0, 225.55267, 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

# Profile functions (minimal, from CrysPy)
def calc_n(a, b): return 0.5*a*b/(a+b)
def calc_h_g(sigma): return np.sqrt(8*np.log(2))*sigma
def calc_h_com(hg, hl): return (hg**5+2.69269*hg**4*hl+2.42843*hg**3*hl**2+4.47163*hg**2*hl**3+0.07842*hg*hl**4+hl**5)**0.2
def calc_eta(hl, hc): x=hl/hc; return 1.36603*x-0.47719*x**2+0.11116*x**3
def calc_e_beta_g(dt, s, a, b):
    n=calc_n(a,b); u=0.5*a*(a*s**2+2*dt); v=0.5*b*(b*s**2-2*dt); y=(a*s**2+dt)/(s*np.sqrt(2)); z=(b*s**2-dt)/(s*np.sqrt(2)); w=-0.5*(dt/s)**2
    with np.errstate(over='ignore',invalid='ignore'): t1=np.exp(w)*erfcx(y); t2=np.exp(w)*erfcx(z)
    m=~np.isfinite(t1);
    if np.any(m):
        with np.errstate(over='ignore'): t1[m]=2*np.exp(u[m])
    m=~np.isfinite(t2)
    if np.any(m):
        with np.errstate(over='ignore'): t2[m]=2*np.exp(v[m])
    return n*(t1+t2)
def _ee1(z):
    r=np.zeros_like(z); lg=np.abs(z.real)>500; sm=~lg
    if np.any(sm): zs=z[sm]; p=np.exp(zs)*exp1(zs); p[~np.isfinite(p)]=0; r[sm]=p
    if np.any(lg): iz=1/z[lg]; r[lg]=iz*(1-iz*(1-iz*(2-iz*(6-iz*24))))
    return r
def calc_e_beta_l(dt, hl, a, b):
    n=calc_n(a,b); p=a*dt+.5j*a*hl; q=-b*dt+.5j*b*hl; return -2*n/np.pi*(np.imag(_ee1(p))+np.imag(_ee1(q)))
def calc_profile(dt, s, hl, a, b0, b1, r0):
    hg=calc_h_g(s); hc=calc_h_com(hg,hl); eta=calc_eta(hl,hc)
    pv0=eta*calc_e_beta_l(dt,hl,a,b0)+(1-eta)*calc_e_beta_g(dt,s,a,b0)
    pv1=eta*calc_e_beta_l(dt,hl,a,b1)+(1-eta)*calc_e_beta_g(dt,s,a,b1)
    return r0*pv0+(1-r0)*pv1

def intermediates(d):
    s2=sigma_0_sq+sigma_1_sq*d**2+sigma_2_sq*d**4; s=np.sqrt(s2)
    hl=gamma_0+gamma_1*d+gamma_2*d**2; hg=calc_h_g(s); hc=calc_h_com(hg,hl)
    r0=r_01*np.exp(-r_02*d**(-r_03)); A=alpha_1+alpha_2/d; B0=beta_00+beta_01/d; B1=beta_10
    return s,hl,hg,hc,r0,A,B0,B1

# Load ZR data
zr_data=np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',skiprows=1,max_rows=9809)
zr_tof=zr_data[:,0]; zr_ycalc=zr_data[:,4]; zr_bg=zr_data[:,5]

peaks=[("111",31397,3.124418,500),("200",27192,2.705826,400),("220",19229,1.913308,250),
       ("311",16399,1.631674,180),("222",15701,1.562209,150),("400",13598,1.352913,150),
       ("331",12478,1.241518,120),("420",12162,1.210082,120),("422",11103,1.104649,100)]

def chi2_for_factor(F):
    total=0
    for hkl,tof_c,d,hw in peaks:
        mask=(zr_tof>=tof_c-hw)&(zr_tof<=tof_c+hw); t=zr_tof[mask]; yb=zr_ycalc[mask]-zr_bg[mask]
        if np.max(yb)<1e-5: continue
        s,hl,hg,hc,r0,A,B0,B1=intermediates(d)
        a=abs(1/(A*F*s)); b0=abs(1/(B0*F*s)); b1=abs(1/(B1*F*s))
        tp=t[np.argmax(yb)]; dt=t-tp
        try:
            pf=calc_profile(dt,s,hl,a,b0,b1,r0)
            if np.max(pf)<1e-20: total+=1; continue
            total+=np.sum((pf/np.max(pf)-yb/np.max(yb))**2)/len(yb)
        except: total+=1
    return total

# Named constants to test
C = np.sqrt(8*np.log(2))  # sqrt(8*ln2) = 2.355
named = {
    'F=1.0 (σ)':             1.0,
    'F=√(2ln2)≈1.177':       np.sqrt(2*np.log(2)),   # HWHM_G / σ
    'F=√(π/2)≈1.253':        np.sqrt(np.pi/2),       # Gaussian integral factor
    'F=2/√π≈1.128':          2/np.sqrt(np.pi),       # error function factor
    'F=√(πln2)≈1.476':       np.sqrt(np.pi*np.log(2)),
    'F=½√(2π)≈1.253':        0.5*np.sqrt(2*np.pi),   # 1/(σ*gauss_peak)
    'F=1/(1-1/e)≈1.582':     1/(1-1/np.e),
    'F=√2≈1.414':            np.sqrt(2),
    'F=1.2 (empirical)':      1.2,
    'F=C=√(8ln2)≈2.355':     C,                       # = h_g/σ = h_com norm
}

# Fine search
F_fine = np.linspace(0.8, 2.0, 2000)
chi2_fine = [chi2_for_factor(f) for f in F_fine]
best_idx = np.argmin(chi2_fine)
best_F = F_fine[best_idx]
best_chi2 = chi2_fine[best_idx]

print(f"Fine-tuned optimal: F = {best_F:.4f} (χ² = {best_chi2:.8f})")
print()

# Report named constants
print(f"{'Name':<30} {'F':>8} {'χ²':>12} {'vs optimal':>12}")
print("-"*65)
for name, F in sorted(named.items(), key=lambda x: x[1]):
    c = chi2_for_factor(F)
    print(f"{name:<30} {F:>8.4f} {c:>12.8f} {c/best_chi2:>10.2f}x")

# Print the per-peak FWHM for the best F
print(f"\n{'='*80}")
print(f"FWHM at best F = {best_F:.4f}")
for hkl,tof_c,d,hw in peaks:
    mask=(zr_tof>=tof_c-hw)&(zr_tof<=tof_c+hw); t=zr_tof[mask]; yb=zr_ycalc[mask]-zr_bg[mask]
    if np.max(yb)<1e-5: continue
    s,hl,hg,hc,r0,A,B0,B1=intermediates(d)
    a=abs(1/(A*best_F*s)); b0=abs(1/(B0*best_F*s)); b1=abs(1/(B1*best_F*s))
    tp=t[np.argmax(yb)]; dt=t-tp
    pf=calc_profile(dt,s,hl,a,b0,b1,r0)
    zr_fw=np.sum(yb>0.5*np.max(yb))*(t[1]-t[0])
    pf_fw=np.sum(pf>0.5*np.max(pf))*(t[1]-t[0])
    print(f"  ({hkl}) d={d:.3f}: ZR={zr_fw:3.0f} calc={pf_fw:3.0f} ratio={pf_fw/zr_fw:.3f}")

# Also check: what is h_com/(C*best_F) vs sigma for each peak?
print(f"\n{'='*80}")
print(f"Normalization check: best_F * σ vs h_com/(C)  and  h_com/best_F")
print(f"{'='*80}")
for hkl,_,d,_ in peaks:
    s,hl,hg,hc,r0,A,B0,B1=intermediates(d)
    eta=calc_eta(hl,hc)
    print(f"  ({hkl}) d={d:.3f}: σ={s:.2f}, h_l={hl:.2f}, h_g={hg:.1f}, h_com={hc:.1f}, η={eta:.3f}")
    print(f"         F*σ={best_F*s:.1f}, h_com/C={hc/C:.1f}, ratio h_l/h_g={hl/hg:.4f}")
