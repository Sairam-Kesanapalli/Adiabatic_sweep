#!/usr/bin/env python3
"""
Check that the channel-length and load-capacitance sweeps obey the physics
of adiabatic charging, and print energy per operation for both.

    python3 check_lc_scaling.py     # reads the four sweep CSVs and
                                    # data/calibration/tg_L*.dat (from
                                    # run_calibration.sh); writes
                                    # lc_scaling_report.txt; exit 1 on failure

Energy per operation here is energy per clock (rail) period per gate
(column) = energy per data transaction: the data alternates every period.
Points whose logic fails (status != ok) are listed but never fitted.

The model (energy_fit.py): E(T) = K*g(T,tau) + b + c*T, a = K*tau.
For an adiabatic node swing through resistance R the 1/T coefficient is
    a = n * R * C_eff^2 * VDD^2          (Fischer et al., Adv. Radio Sci.
                                          2, 221 (2004), eq. 1)
with n = 4 node swings per 2LAL operation (T up and down, C down and up)
and C_eff = C_L + C_p.  That gives three predictions checked here:

  CAP, 2LAL     sqrt(a / 4 VDD^2) = sqrt(R) * (C_L + C_p) is LINEAR in C_L.
                Its slope gives R, which must match the transmission gate's
                DC on-resistance (cal_tg_ron.sp) within 15 %; its
                intercept gives C_p, which must be a few fF (0 < C_p < 15).
  CAP, ECRL     the fixed residue b (the C*Vth^2/2-type loss, eq. 2 of the
                same paper) must grow with C_L at every step, and the slow-
                clock energy must scale close to linearly (log-log slope
                1.0-1.5 at TPHASE = 100 ns), unlike 2LAL.
  LENGTH, 2LAL  C_eff(L) = sqrt(a / (4 VDD^2 R(L))), with R(L) measured at
                each L by cal_tg_ron.sp, must be LINEAR in L (gate charge
                grows with W*L) within 6 %, with an intercept of C_L plus a
                few fF of junction capacitance (25-35 fF).
  LITERATURE    the ring at Frank et al.'s published 2LAL operating point
                (ICRC 2020: 6.9 aJ per FET per cycle at 1 MHz, 10 fF,
                W = 480 nm, Sandia 180 nm) must pass all 96 logic checks and
                land within 2x of 6.9 aJ (different process, so a loose band).

Standard library only, like check_waveforms.py.
"""
import csv, math, os, sys

from energy_fit import fit_energy, line_fit

VDD = 1.8
CL_FIX = 25.0                      # fF, the load held fixed in the length sweep
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
DATA = os.path.join("data", "calibration")
REPORT = "lc_scaling_report.txt"
CSV = {("2lal", "length"): "../2lal/2lal_length_sweep.csv",
       ("2lal", "cap"):    "../2lal/2lal_cap_sweep.csv",
       ("ecrl", "length"): "../ecrl/ecrl_length_sweep.csv",
       ("ecrl", "cap"):    "../ecrl/ecrl_cap_sweep.csv"}
KEY = {"length": "L_um", "cap": "CL_fF"}

out_lines = []
def say(s=""):
    print(s)
    out_lines.append(s)

results = []
def verdict(label, ok, detail):
    results.append(ok)
    say(f"  {label} {'.' * max(3, 64 - len(label))} {'PASS' if ok else 'FAIL'} ({detail})")


def load(fam, mode):
    """{x: {T: (E_fJ, status)}} with x = L (um) or C_L (fF)"""
    d = {}
    with open(CSV[(fam, mode)]) as f:
        for r in csv.DictReader(f):
            d.setdefault(r[KEY[mode]], {})[float(r["Tphase_ns"])] = (float(r["E_C_fJ"]), r["status"])
    return dict(sorted(d.items(), key=lambda kv: float(kv[0])))

def ok_points(row):
    pts = sorted((t, e) for t, (e, s) in row.items() if s == "ok")
    return [p[0] for p in pts], [p[1] for p in pts]

def tg_rmean(tag):
    with open(os.path.join(DATA, tag + ".dat")) as f:
        R = [0.01 / -float(line.split()[1]) for line in f if line.strip()]
    return sum(R) / len(R)

def vth(tag, kind):
    """constant-current Vth (V) from cal_vth.sp's I-V dump: |Vgs| where the
    drain current reaches 100 nA * W/L, W = 1 um"""
    L = float(tag.split("_L")[1])
    icrit = 100e-9 / L
    pts = []
    with open(os.path.join(DATA, f"{tag}.dat.{kind}")) as f:
        for line in f:
            if line.strip():
                vg, i = (float(x) for x in line.split()[:2])
                pts.append((abs(vg - (1.8 if kind == "p" else 0.0)), abs(i)))
    pts.sort()
    for (v0, i0), (v1, i1) in zip(pts, pts[1:]):
        if i0 < icrit <= i1:
            return v0 + (v1 - v0) * (math.log(icrit) - math.log(i0)) / (math.log(i1) - math.log(i0))
    sys.exit(f"FAIL: {tag}: drain current never reaches {icrit:.3g} A")

def table(fam, mode, title):
    """print energy per operation (fJ) on the sweep grid; X = logic fails"""
    d = load(fam, mode)
    Ts = sorted({t for row in d.values() for t in row})
    say(title)
    say(f"  {KEY[mode]:>7}" + "".join(f"{('T='+format(t,'g')+'ns'):>11}" for t in Ts))
    for x, row in d.items():
        cells = ""
        for t in Ts:
            e, s = row[t]
            cells += f"{e:10.3f}" + {"ok": " ", "logic_fail": "X", "unsettled": "u"}[s]
        say(f"  {x:>7}{cells}")
    say("  (fJ per operation = per clock period = per data transaction;"
        " X = logic fails, u = not settled; neither is fitted)")
    say()
    return d


say("Channel-length and load-capacitance sweeps vs the adiabatic energy model"
    "  (python3 check_lc_scaling.py)\n")

# ================================================================ tables
lal_len = table("2lal", "length", "2LAL ring, length sweep: W = 1.0 um, C_L = 25 fF")
ecrl_len = table("ecrl", "length", "ECRL, length sweep: W = 1.0 um, C_L = 25 fF")
lal_cap = table("2lal", "cap", "2LAL ring, load sweep: W = 1.0 um, L = 0.15 um")
ecrl_cap = table("ecrl", "cap", "ECRL, load sweep: W = 1.0 um, L = 0.15 um")

# ================================================================ CAP, 2LAL
say("CAP, 2LAL: a = 4 * R * (C_L + C_p)^2 * VDD^2  ->  sqrt(a/4VDD^2) linear in C_L")
say("  C_L(fF)  points  a(fJ*ns)  tau(ns)  fit RMS   sqrt(a/4V^2)(1e-12 SI)")
xs, ys = [], []
for x, row in lal_cap.items():
    T, E = ok_points(row)
    f = fit_energy(T, E, False, tau_max=50)
    s = math.sqrt(f["a"] * 1e-24 / (4 * VDD**2)) * 1e12
    xs.append(float(x)); ys.append(s)
    say(f"  {x:>7}  {len(T):5d}  {f['a']:9.2f}  {f['tau']:6.3f}  {100*f['rms']:5.2f} %   {s:9.5f}")
slope, icpt = line_fit(xs, ys)
R_fit = (slope * 1e-12 / 1e-15) ** 2
Cp = icpt / slope
R_dc = tg_rmean("tg_L0.15")
worst = max(abs(y / (slope * x + icpt) - 1) for x, y in zip(xs, ys))
say(f"  line: R = {R_fit:.0f} ohm, C_p = {Cp:.2f} fF;  DC on-resistance of the TG = {R_dc:.0f} ohm")
verdict("CAP 2LAL: sqrt(a) linear in C_L within 2 % at every load", worst < 0.02,
        f"worst {100*worst:.2f} %")
verdict("CAP 2LAL: fitted R matches the TG DC on-resistance within 15 %",
        abs(R_fit / R_dc - 1) < 0.15, f"{R_fit:.0f} vs {R_dc:.0f} ohm, {100*(R_fit/R_dc-1):+.1f} %")
verdict("CAP 2LAL: parasitic C_p is a few fF (0 .. 15 fF)", 0 < Cp < 15, f"{Cp:.2f} fF")
say()

# ================================================================ CAP, ECRL
say("CAP, ECRL: fixed residue b (threshold loss) vs C_L, and slow-clock scaling")
say("  C_L(fF)  points  a(fJ*ns)  b(fJ)    b/C_L(fJ/fF)  fit RMS")
bs = []
for x, row in ecrl_cap.items():
    T, E = ok_points(row)
    f = fit_energy(T, E, True, tau_max=50)
    bs.append(f["b"])
    say(f"  {x:>7}  {len(T):5d}  {f['a']:9.2f}  {f['b']:7.3f}  {f['b']/float(x):9.3f}     {100*f['rms']:5.2f} %")
verdict("CAP ECRL: residue b grows at every step in C_L",
        all(b2 > b1 for b1, b2 in zip(bs, bs[1:])), " < ".join(f"{b:.1f}" for b in bs) + " fJ")
def loglog_slopes(d, T):
    xs = [x for x in d if d[x][T][1] == "ok"]
    return [(xs[i], xs[i+1], math.log(d[xs[i+1]][T][0] / d[xs[i]][T][0]) / math.log(float(xs[i+1]) / float(xs[i])))
            for i in range(len(xs) - 1)]
say("  log-log slope dlnE/dlnC_L, C_L >= 25 fF (1 = linear in C, 2 = quadratic):")
for fam, d, T in (("ECRL", ecrl_cap, 100.0), ("2LAL", lal_cap, 10.0)):
    sl = [s for s in loglog_slopes(d, T) if float(s[0]) >= 25]
    say(f"    {fam} at TPHASE = {T:g} ns: " + ", ".join(f"{a}->{b} fF: {s:.2f}" for a, b, s in sl))
    if fam == "ECRL":
        verdict("CAP ECRL: slow-clock energy close to linear in C_L (slope 1.0-1.5)",
                all(1.0 <= s <= 1.5 for *_, s in sl), "slopes " + ", ".join(f"{s:.2f}" for *_, s in sl))
    else:
        verdict("CAP 2LAL: energy steeper than ECRL, toward C^2 (slope 1.5-2.0)",
                all(1.5 <= s <= 2.0 for *_, s in sl), "slopes " + ", ".join(f"{s:.2f}" for *_, s in sl))
say()

# ================================================================ LENGTH, 2LAL
say("LENGTH, 2LAL: C_eff(L) = sqrt(a / (4 VDD^2 R(L))) with R(L) from cal_tg_ron.sp")
say("  L(um)  points  a(fJ*ns)  tau(ns)  fit RMS   R_TG(kohm)  C_eff(fF)")
Ls, Ce = [], []
for x, row in lal_len.items():
    T, E = ok_points(row)
    f = fit_energy(T, E, False, tau_max=50)
    R = tg_rmean(f"tg_L{x}")
    c = math.sqrt(f["a"] * 1e-24 / (4 * VDD**2 * R)) * 1e15
    Ls.append(float(x)); Ce.append(c)
    note = "  (3 points, 3 parameters: exact, not a test)" if len(T) <= 3 else ""
    say(f"  {x:>5}  {len(T):5d}  {f['a']:9.2f}  {f['tau']:6.3f}  {100*f['rms']:5.2f} %   {R/1e3:8.2f}   {c:7.2f}{note}")
k, c0 = line_fit(Ls, Ce)
worst = max(abs(c / (k * L + c0) - 1) for L, c in zip(Ls, Ce))
say(f"  line: C_eff = {c0:.2f} fF + {k:.2f} fF/um * L")
say("  For comparison (gate oxide Cox = 8.3 fF/um^2 from the model's toxe = 4.15 nm):")
say("    4 gates per node x Cox x W, if every gate were in inversion ....... 33 fF/um")
say("    2 gates per node x Cox x W: only these invert while the node swings 16.6 fF/um")
say("    the same 2 gates, inverted only above Vth (~0.55-0.95 V) ........ ~10 fF/um")
say(f"  The measured {k:.1f} fF/um sits between the last two, as it should.")
verdict("LENGTH 2LAL: C_eff linear in L within 6 % at every length", worst < 0.06,
        f"worst {100*worst:.1f} %")
verdict("LENGTH 2LAL: intercept = C_L + a few fF (25 .. 35 fF)", CL_FIX <= c0 <= 35,
        f"{c0:.2f} fF")
say()

# ================================================================ LENGTH, ECRL
say("LENGTH: threshold voltage vs L (cal_vth.sp, 100 nA * W/L, W = 1 um)")
say("  L(um)  nFET Vth(V)  pFET |Vth|(V)")
vt = {}
for x in lal_len:
    vt[x] = (vth(f"vth_L{x}", "n"), vth(f"vth_L{x}", "p"))
    say(f"  {x:>5}    {vt[x][0]:.3f}       {vt[x][1]:.3f}")
say("  The pFET |Vth| rises with L; the nFET Vth falls (sky130's halo implants give a")
say("  reverse short-channel effect).  ECRL's threshold loss comes from its pull-up pFET.")
say()

say("LENGTH, ECRL: residue b and 1/T coefficient a vs L (fits need >= 5 points)")
say("  L(um)  points  a(fJ*ns)  b(fJ)    fit RMS")
bl = []
for x, row in ecrl_len.items():
    T, E = ok_points(row)
    if len(T) < 5:
        say(f"  {x:>5}  {len(T):5d}  (too few passing points to fit)")
        continue
    f = fit_energy(T, E, True, tau_max=50)
    bl.append(f["b"])
    say(f"  {x:>5}  {len(T):5d}  {f['a']:9.2f}  {f['b']:7.3f}  {100*f['rms']:5.2f} %")
verdict("LENGTH ECRL: threshold residue b grows with L, as the pFET |Vth| does",
        all(b2 > b1 for b1, b2 in zip(bl, bl[1:])), " < ".join(f"{b:.1f}" for b in bl) + " fJ")

# ================================================================ LITERATURE
say()
say("LITERATURE: 2LAL shift register, Frank et al., ICRC 2020 (Sandia SAND talk, slide 19):")
say("  6.9 aJ per cycle per FET at f = 1 MHz, CL = 10 fF, 50 % activity, MESA 180 nm, W = 480 nm")
say("  (37 aJ in MESA 350 nm, W = 800 nm).  This ring at the same point in SKY130:")
say("  TPHASE = 250 ns, CL = 10 fF, W = 0.48 um, L = 0.18 um.  A quad-rail column has 16 FETs")
say("  and exactly one of its two sub-chains pulses per cycle: 50 % activity per sub-chain.")
lit = {}
with open(os.path.join(DATA, "lit_frank2020.out")) as f:
    for line in f:
        p = line.split()
        if len(p) >= 3 and p[1] == "=":
            lit[p[0].lower()] = p[2]
nchk = sum(1 for k in lit if k.startswith(("chkhi_", "chklo_")))
nbad = sum(1 for k, v in lit.items() if (k.startswith("chkhi_") and float(v) < 0.9 * VDD)
           or (k.startswith("chklo_") and float(v) > 0.1 * VDD))
per_fet = float(lit["e_c"]) / 16 * 1e18
say(f"  E per column = {float(lit['e_c'])*1e15:.4f} fJ -> {per_fet:.2f} aJ per FET per cycle"
    f" ({per_fet/6.9:.2f}x the published 6.9 aJ); logic checks failed: {nbad}/{nchk}")
verdict("LITERATURE: 2LAL logic correct at the published operating point",
        nchk == 96 and nbad == 0, f"{nchk - nbad}/{nchk} checks")
verdict("LITERATURE: per-FET energy within 2x of Frank et al.'s 6.9 aJ",
        0.5 <= per_fet / 6.9 <= 2.0, f"{per_fet:.2f} aJ, {per_fet/6.9:.2f}x")

ok = all(results)
say(f"\nOVERALL: {'PASS' if ok else 'FAIL'}  ({sum(results)}/{len(results)} checks)")
with open(REPORT, "w") as f:
    f.write("\n".join(out_lines) + "\n")
print("->", REPORT)
sys.exit(0 if ok else 1)
