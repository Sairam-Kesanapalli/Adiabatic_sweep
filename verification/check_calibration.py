#!/usr/bin/env python3
"""
Check that the energy numbers can be trusted (check 1) and that both
families obey the energy model their physics predicts (check 2).

    python3 check_calibration.py    # reads data/calibration/ (from
                                    # run_calibration.sh) and the two sweep
                                    # CSVs; writes calibration_report.txt;
                                    # exit 1 on any failure

Check 1 -- the meter and the solver
  1a  Static CMOS through the 2LAL energy meter: dE/dCL must equal VDD^2,
      whatever the parasitic and short-circuit energy are.
  1b  Max step / 4 and reltol 1e-6 must not move any energy by > 0.5 %.
  1c  An ideal R-C on the rail trapezoid must match the exact solution of
      the RC equation (solved here, independently of ngspice) within 0.1 %.

Check 2 -- the physics
  Both sweeps are fitted to  E(T) = K*g(T, tau) + b + c*T,  where g is the
  exact loss of one RC ramp (-> tau/T when T >> tau), b a fixed residue
  and c*T leakage.
  The residue is judged against CL*VDD^2 = 81 fJ, the energy one node swing
  moves; a fraction of the sweep's own smallest point would be meaningless,
  since that point is itself only ~1 fJ.
  2LAL  must be fully adiabatic: fit RMS < 3 % and |b| < 1 % of CL*VDD^2,
        at every width.  Its 1/T coefficient a = K*tau
        must match the measured TG on-resistance: a = 4*C_eff^2*V^2*R_mean
        (4 node swings per op) gives C_eff = c0 + k*W, and c0 must land
        within 10 % of the 25 fF load.
  ECRL  must keep a threshold residue: b > 5 % of CL*VDD^2.  Its device-by-phase
        energy split must close on the total within 2 %, and the clock-rise
        loss predicted from the pFET DC table alone must be 75-100 % of the
        simulated one at TPHASE = 10 and 100 ns.

Standard library only, like check_waveforms.py.
"""
import csv, math, os, sys

VDD = 1.8
CL = 25e-15
CV2 = CL * VDD**2 * 1e15      # fJ, energy of one full node swing
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
DATA = os.path.join("data", "calibration")
REPORT = "calibration_report.txt"
CSV_2LAL = os.path.join("..", "2lal", "2lal_inverter_sweep.csv")
CSV_ECRL = os.path.join("..", "ecrl", "ecrl_slowramp_sweep.csv")

out_lines = []
def say(s=""):
    print(s)
    out_lines.append(s)

results = []
def verdict(label, ok, detail):
    results.append(ok)
    say(f"  {label} {'.' * max(3, 60 - len(label))} {'PASS' if ok else 'FAIL'} ({detail})")


# ------------------------------------------------------------------ input
def meas(tag, name):
    """value of one .meas line in data/calibration/TAG.out (must appear once)"""
    vals = []
    with open(os.path.join(DATA, tag + ".out")) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[0].lower() == name.lower() and p[1] == "=":
                vals.append(float(p[2]))
    if len(vals) != 1:
        sys.exit(f"FAIL: {tag}.out has {len(vals)} '{name}' lines -- rerun run_calibration.sh")
    return vals[0]

def wrdata(tag):
    """(scale, value) pairs from a one-vector wrdata file"""
    with open(os.path.join(DATA, tag + ".dat")) as f:
        return [tuple(float(x) for x in line.split()[:2]) for line in f if line.strip()]

def sweep_csv(path):
    """{W: [(T_ns, E_fJ), ...]} sorted by T, from a sweep CSV's E_C column"""
    d = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            d.setdefault(float(r["W_um"]), []).append((float(r["Tphase_ns"]), float(r["E_C_fJ"])))
    return {w: sorted(v) for w, v in sorted(d.items())}


# ------------------------------------------------------------------ maths
def solve(A, y):
    """Gaussian elimination with partial pivoting, small dense systems"""
    n = len(y)
    M = [row[:] + [y[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / M[r][r]
    return x

def lstsq(cols, y, w=None):
    """least squares y ~ sum_j p_j*cols[j], optional per-point weights"""
    w = w or [1.0] * len(y)
    A = [[sum(w[i] ** 2 * ci[i] * cj[i] for i in range(len(y))) for cj in cols] for ci in cols]
    b = [sum(w[i] ** 2 * ci[i] * y[i] for i in range(len(y))) for ci in cols]
    return solve(A, b)

def line_fit(x, y):
    slope, icpt = lstsq([x, [1.0] * len(x)], y)
    return slope, icpt

def g(T, tau):
    """loss of one RC ramp of duration T, in units of C*V^2"""
    r = tau / T
    return r * (1 - r * (1 - math.exp(-T / tau)))

def fit_energy(T, E, with_b):
    """best tau on a log grid; K, c (and b) by relative-error least squares"""
    best = None
    w = [1 / e for e in E]
    for i in range(1200):
        tau = 0.01 * (500 ** (i / 1199))          # 0.01 .. 5 ns
        cols = [[g(t, tau) for t in T], list(T)] + ([[1.0] * len(T)] if with_b else [])
        p = lstsq(cols, E, w)
        pred = [sum(p[j] * cols[j][k] for j in range(len(cols))) for k in range(len(T))]
        rel = [pk / ek - 1 for pk, ek in zip(pred, E)]
        rms = math.sqrt(sum(r * r for r in rel) / len(rel))
        if best is None or rms < best["rms"]:
            best = dict(tau=tau, K=p[0], c=p[1], b=p[2] if with_b else 0.0,
                        rms=rms, max=max(abs(r) for r in rel))
    best["a"] = best["K"] * best["tau"]                  # fJ*ns
    return best

def rc_exact(tphase, R=10e3, C=25e-15, n=100000, periods=3):
    """energy per rail period of an ideal RC on the trapezoid, settled"""
    tau, trail = R * C, 4 * tphase
    dt = trail / n
    a = math.exp(-dt / tau)
    def vin(t):
        t %= trail
        if t < tphase:     return VDD * t / tphase
        if t < 2 * tphase: return VDD
        if t < 3 * tphase: return VDD * (3 * tphase - t) / tphase
        return 0.0
    v, E = 0.0, 0.0
    for _ in range(periods):
        E = 0.0
        x0 = vin(0.0)
        for k in range(n):
            x1 = vin((k + 1) * dt)
            s = (x1 - x0) / dt
            v1 = x0 + s * dt - s * tau + (v - x0 + s * tau) * a   # exact for a linear input
            E += 0.5 * dt * ((x0 - v) ** 2 + (x1 - v1) ** 2) / R
            v, x0 = v1, x1
    return E


# ============================================================ check 1a
say("Calibration of the energy meter, and the energy model  (python3 check_calibration.py)")
say(f"VDD = {VDD} V, so VDD^2 = {VDD**2:.3f} fJ/fF\n")
say("1a. Static CMOS inverter through the 2LAL meter (W = 1 um, 100 ps input edges)")
say("  TPER    CL(fF)  E/cycle(fJ)  INTEG meter(fJ)  meters differ")
cmos = {}
for T in ("40n", "400n"):
    for C in ("0", "10f", "25f", "50f", "100f"):
        tag = f"cmos_CL{C}_T{T}"
        e1, e2 = meas(tag, "e_cyc") * 1e15, meas(tag, "e_cyc2") * 1e15
        hi, lo = meas(tag, "vout_hi"), meas(tag, "vout_lo")
        cl = float(C.rstrip("f") or 0)
        cmos[(T, cl)] = (e1, e2, hi, lo)
        say(f"  {T:6} {cl:6.0f}   {e1:9.3f}     {e2:9.3f}        {100*(e2/e1-1):+6.2f} %")
for T in ("40n", "400n"):
    pts = [(cl, v[0]) for (t, cl), v in cmos.items() if t == T and cl >= 10]
    slope, icpt = line_fit([p[0] for p in pts], [p[1] for p in pts])
    say(f"  TPER {T}: slope {slope:.4f} fJ/fF ({100*(slope/VDD**2-1):+.2f} % vs VDD^2), "
        f"intercept {icpt:.2f} fJ")
    verdict(f"1a slope = VDD^2 within 1 %, TPER {T}", abs(slope / VDD**2 - 1) < 0.01,
            f"{100*(slope/VDD**2-1):+.2f} %")
e40, e400 = cmos[("40n", 25.0)][0], cmos[("400n", 25.0)][0]
verdict("1a frequency-independent: 40 vs 400 ns at 25 fF within 1 %",
        abs(e40 / e400 - 1) < 0.01, f"{100*(e40/e400-1):+.2f} %")
dmax = max(abs(v[1] / v[0] - 1) for (t, cl), v in cmos.items() if cl >= 10)
verdict("1a the two meters agree within 1 % (CL >= 10 fF)", dmax < 0.01, f"max {100*dmax:.2f} %")
okf = all(v[2] > 0.9 * VDD and v[3] < 0.1 * VDD for v in cmos.values())
verdict("1a inverter output full-swing in every run", okf, "high > 0.9 VDD, low < 0.1 VDD")
say(f"  -> static CMOS costs {e40/2:.1f} fJ per transition at CL = 25 fF: the 'no adiabatic"
    f" benefit' line\n")

# ============================================================ check 1b
say("1b. Convergence: as shipped / max step / 4 / and reltol 1e-6   (E_C, fJ)")
say("  family  TPHASE   shipped     step/4      tight     worst change")
worst = 0.0
for fam in ("2lal", "ecrl"):
    for T in (1, 10, 100):
        v = [meas(f"conv_{fam}_T{T}_{k}", "e_c") * 1e15 for k in ("base", "step", "tight")]
        ch = max(abs(x / v[0] - 1) for x in v[1:])
        worst = max(worst, ch)
        say(f"  {fam.upper():6} {T:4} ns  {v[0]:9.4f}  {v[1]:9.4f}  {v[2]:9.4f}    {100*ch:.3f} %")
verdict("1b no energy moves by more than 0.5 %", worst < 0.005, f"worst {100*worst:.3f} %")
say()

# ============================================================ check 1c
say("1c. Ideal 10 kohm / 25 fF on the rail trapezoid, tau = 250 ps   (fJ per rail period)")
say("  TPHASE   exact      ngspice    error")
for T in (1, 10, 100):
    ex = rc_exact(T * 1e-9) * 1e15
    sim = meas(f"rc_T{T}n", "e_per") * 1e15
    say(f"  {T:4} ns  {ex:9.5f}  {sim:9.5f}  {100*(sim/ex-1):+.4f} %")
    verdict(f"1c meter matches the exact RC solution within 0.1 %, {T} ns",
            abs(sim / ex - 1) < 0.001, f"{100*(sim/ex-1):+.4f} %")
say()

# ============================================================ check 2: 2LAL
say("2. Fit E(T) = K*g(T,tau) + b + c*T   (T = TPHASE in ns, E in fJ)")
say("2LAL ring (" + CSV_2LAL + ")")
say("  W(um)  a=K*tau(fJ*ns)  tau(ns)  b(fJ)   c(fJ/ns)   RMS     max    b / CL*VDD^2")
lal = sweep_csv(CSV_2LAL)
a0 = {}
for W, pts in lal.items():
    T, E = [p[0] for p in pts], [p[1] for p in pts]
    f = fit_energy(T, E, True)
    a0[W] = fit_energy(T, E, False)["a"]
    bfrac = f["b"] / CV2
    say(f"  {W:5}  {f['a']:10.2f}     {f['tau']:6.3f}  {f['b']:6.3f}  {f['c']:9.5f}  "
        f"{100*f['rms']:5.2f} %  {100*f['max']:5.2f} %  {100*bfrac:+6.2f} %")
    verdict(f"2 2LAL fully adiabatic, W = {W}: RMS < 3 %, |b| < 1 % CV^2",
            f["rms"] < 0.03 and abs(bfrac) < 0.01,
            f"RMS {100*f['rms']:.2f} %, b {100*bfrac:+.2f} %")

say("\n  TG on-resistance (cal_tg_ron.sp) and the node capacitance it implies, using the")
say("  b = 0 fit:  a = 4 * C_eff^2 * VDD^2 * R_mean")
say("  W(um)  R_mean(kohm)  a(fJ*ns)  C_eff(fF)")
Ws, Ce = [], []
for W in lal:
    R = [0.01 / -i for _, i in wrdata(f"tg_W{W}")]
    rm = sum(R) / len(R)
    c = math.sqrt(a0[W] * 1e-24 / (4 * VDD**2 * rm)) * 1e15
    Ws.append(W); Ce.append(c)
    say(f"  {W:5}  {rm/1e3:9.3f}    {a0[W]:8.2f}   {c:7.2f}")
k, c0 = line_fit(Ws, Ce)
say(f"  C_eff = {c0:.1f} fF + {k:.2f} fF/um * W   (deck load CL = {CL*1e15:.0f} fF)")
verdict("2 2LAL C_eff intercept within 10 % of CL", abs(c0 / (CL * 1e15) - 1) < 0.10,
        f"{c0:.1f} fF")
say()

# ============================================================ check 2: ECRL
say("ECRL (" + CSV_ECRL + ")")
say("  W(um)  a=K*tau(fJ*ns)  tau(ns)  b(fJ)   c(fJ/ns)   RMS     max    b / CL*VDD^2")
for W, pts in sweep_csv(CSV_ECRL).items():
    T, E = [p[0] for p in pts], [p[1] for p in pts]
    f = fit_energy(T, E, True)
    say(f"  {W:5}  {f['a']:10.2f}     {f['tau']:6.3f}  {f['b']:6.2f}  {f['c']:9.5f}  "
        f"{100*f['rms']:5.2f} %  {100*f['max']:5.2f} %  {100*f['b']/CV2:+6.2f} %")
    verdict(f"2 ECRL keeps a threshold residue, W = {W}: b > 5 % CV^2", f["b"] > 0.05 * CV2,
            f"b = {100*f['b']/CV2:.1f} %")
say("  (c < 0 means the residue itself shrinks slowly with T: a slower clock lets the")
say("   subthreshold pFET drain the output further; see vres below)")

say("\n  Energy split of one clock cycle (TEST A), W = 1 um, fJ")
say("  TPHASE  total  pFET:wait  rise   hold   fall  nFET  n-well  sum-total  vres(V)")
# pFET DC table: rows are Vn-major, Vphi-minor, both 0..1.8 V in 10 mV steps
dc = wrdata("pfet_rise")
N = 181
if len(dc) != N * N or any(abs(dc[k][0] - (k % N) * 0.01) > 1e-6 for k in range(0, N * N, 997)):
    sys.exit("FAIL: pfet_rise.dat is not the expected 181 x 181 Vphi-minor table")
I = [[dc[j * N + i][1] for j in range(N)] for i in range(N)]       # I[phi][vn]
def ip(phi, vn):
    x, y = min(max(phi / 0.01, 0), N - 1.0001), min(max(vn / 0.01, 0), N - 1.0001)
    i, j = int(x), int(y); fx, fy = x - i, y - j
    return (I[i][j] * (1 - fx) * (1 - fy) + I[i + 1][j] * fx * (1 - fy)
            + I[i][j + 1] * (1 - fx) * fy + I[i + 1][j + 1] * fx * fy)
def rise_loss(T, C=CL, n=100000):
    """integrate C dVn/dt = I(PHI, Vn) over the ramp and a settling hold"""
    vn, E, dt = 0.0, 0.0, T / n
    for k in range(n):
        phi = VDD * (k + 0.5) / n
        i = ip(phi, vn); E += (phi - vn) * i * dt; vn += i * dt / C
    for k in range(n // 10):
        i = ip(VDD, vn); E += (VDD - vn) * i * dt; vn += i * dt / C
    return E

for T in (1, 10, 100):
    tag = f"ecrl_split_T{T}"
    p = {k: meas(tag, k) * 1e15 for k in ("e_a", "ep_wait", "ep_rise", "ep_hold", "ep_fall",
                                          "en_cyc", "ewell")}
    s = sum(v for k, v in p.items() if k != "e_a")
    say(f"  {T:4} ns {p['e_a']:6.2f}  {p['ep_wait']:6.2f}  {p['ep_rise']:6.2f} {p['ep_hold']:6.2f} "
        f"{p['ep_fall']:6.2f} {p['en_cyc']:5.2f}  {p['ewell']:6.2f}   {100*(s/p['e_a']-1):+5.2f} %   "
        f"{meas(tag, 'vres'):.3f}")
    verdict(f"2 ECRL energy split closes within 2 %, {T} ns", abs(s / p["e_a"] - 1) < 0.02,
            f"{100*(s/p['e_a']-1):+.2f} %")
    pred = rise_loss(T * 1e-9) * 1e15
    r = pred / p["ep_rise"]
    say(f"          clock-rise loss predicted from the pFET DC table: {pred:.2f} fJ "
        f"= {100*r:.0f} % of simulated")
    if T >= 10:
        verdict(f"2 ECRL rise loss predicted from DC data, {T} ns: 75-100 %", 0.75 <= r <= 1.0,
                f"{100*r:.0f} %")
say("  (at 1 ns the ramp is only 4 tau, so the RC term the DC model leaves out dominates)")

ok = all(results)
say(f"\nOVERALL: {'PASS' if ok else 'FAIL'}  ({sum(results)}/{len(results)} checks)")
with open(REPORT, "w") as f:
    f.write("\n".join(out_lines) + "\n")
print("->", REPORT)
sys.exit(0 if ok else 1)
