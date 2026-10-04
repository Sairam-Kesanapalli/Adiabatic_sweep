#!/usr/bin/env python3
"""
Decode the waveforms dumped by run_waveforms.sh into logic values, check
that both circuits invert, and draw the waveform figures.

This is a second, independent check on the decks' own .meas checks.  It
never uses the generator's expected-value table to decide pass/fail; it
reads every node in every period and asks only
  ECRL : is OUT = NOT IN in every clock cycle, with the other output
         held low?
  2LAL : does exactly one sub-chain of every node pulse in every rail
         period, with the idle one at rest, and is every stage's output
         the inverse of its input one TPHASE later?
Afterwards it compares its decoded values with the 2LAL deck's expected
table (the '* node m, period P: TRUE on x' lines make_2lal_ring.py
writes), so the two methods cross-check each other.

    python3 check_waveforms.py      # reads data/, writes figures/ and
                                    # waveform_report.txt; exit 1 on any failure

Standard library + gnuplot only, like ../plots/make_plots.py.
"""
import bisect, os, re, subprocess, sys

VDD = 1.8
HI, LO = 0.9 * VDD, 0.1 * VDD          # same thresholds as the decks' checks
N = 8                                  # ring stages
HERE = os.path.dirname(os.path.abspath(__file__))
DATA, FIGS = "data", "figures"
REPORT = "waveform_report.txt"
DECK_2LAL = "../2lal/2LAL_inverter_ring.sp"

out_lines = []
def say(s=""):
    print(s)
    out_lines.append(s)


# ------------------------------------------------------------------ data
class Wave:
    """One wrdata dump (single time scale, vector names on line 1)."""
    def __init__(self, path):
        self.path = path
        with open(path) as f:
            self.names = [n.lower() for n in f.readline().split()]
            cols = [[] for _ in self.names]
            for line in f:
                for c, v in zip(cols, line.split()):
                    c.append(float(v))
        self.col = dict(zip(self.names, cols))
        self.t = self.col["time"]

    def idx(self, name):                 # 1-based column number for gnuplot
        return self.names.index(name.lower()) + 1

    def at(self, name, t):
        ts, v = self.t, self.col[name]
        i = min(max(bisect.bisect_right(ts, t), 1), len(ts) - 1)
        t0, t1 = ts[i - 1], ts[i]
        return v[i - 1] + (v[i] - v[i - 1]) * (t - t0) / (t1 - t0)

    def span(self, name, t0, t1):        # (min, max) over [t0, t1]
        i, j = bisect.bisect_left(self.t, t0), bisect.bisect_right(self.t, t1)
        vals = self.col[name][i:j] + [self.at(name, t0), self.at(name, t1)]
        return min(vals), max(vals)


# ================================================================== ECRL
def check_ecrl(T):
    w = Wave(f"{DATA}/ecrl_T{T}.dat")
    tp = T * 1e-9
    ok = True
    say(f"\nECRL inverter, TPHASE = {T} ns   (cycle k = [4k, 4k+4]*TPHASE, sampled mid-hold)")
    say("  cycle  V(IN)  IN  V(OUT)  V(OUTB)  OUT=NOT IN   other output max during evaluate+hold")
    labels = []
    for k in range(5):
        tm = (4 * k + 2.5) * tp
        vin, vo, vob = w.at("v(in)", tm), w.at("v(out)", tm), w.at("v(outb)", tm)
        IN = 1 if vin > HI else 0 if vin < LO else None
        low = "v(out)" if IN == 1 else "v(outb)"
        worst = w.span(low, (4 * k + 1) * tp, (4 * k + 3) * tp)[1]
        good = (IN == 1 and vo < LO and vob > HI or IN == 0 and vo > HI and vob < LO) and worst < LO
        ok &= bool(good)
        say(f"    {k}    {vin:5.2f}  {IN}   {vo:5.2f}   {vob:5.2f}     {'yes' if good else 'NO '}"
            f"         {worst:.3f} V")
        labels.append((k, IN))
    say(f"  -> {'PASS' if ok else 'FAIL'}")
    return w, labels, ok


# ================================================================== 2LAL
def decode_2lal(w, T, periods):
    """{(node, period): 1 if the a-sub-chain is TRUE, 0 if the n one}; list of problems."""
    tp = T * 1e-9
    val, bad = {}, []
    for P in range(periods):
        for m in range(N):
            ts = P * 4 * tp + (m % 4) * tp          # this node's pulse starts here
            if ts + 4 * tp > w.t[-1]:
                continue
            pl, rest = ts + 1.5 * tp, ts + 3.5 * tp
            fire = {s: w.at(f"v({s}t{m})", pl) > HI and w.at(f"v({s}c{m})", pl) < LO for s in "an"}
            if fire["a"] == fire["n"]:
                bad.append(f"node {m} period {P}: {'both' if fire['a'] else 'neither'} sub-chain TRUE")
                continue
            t, f = ("a", "n") if fire["a"] else ("n", "a")
            if not (w.at(f"v({t}t{m})", rest) < LO and w.at(f"v({t}c{m})", rest) > HI):
                bad.append(f"node {m} period {P}: TRUE sub-chain not back at rest")
            if w.span(f"v({f}t{m})", ts, ts + 4 * tp)[1] > LO or w.span(f"v({f}c{m})", ts, ts + 4 * tp)[0] < HI:
                bad.append(f"node {m} period {P}: idle sub-chain left rest")
            val[(m, P)] = 1 if t == "a" else 0
    return val, bad


def inversions(val):
    """Every stage m: value at node m+1 one TPHASE later must be NOT value at m."""
    n, bad = 0, []
    for (m, P), v in sorted(val.items()):
        nxt = ((m + 1) % N, P + (1 if m % 4 == 3 else 0))   # node 3 -> node 4 wraps to phi0
        if nxt in val:
            n += 1
            if val[nxt] != 1 - v:
                bad.append(f"stage {m}: node {m} P{P} = {v} but node {nxt[0]} P{nxt[1]} = {val[nxt]}")
    return n, bad


def table(val, periods):
    say("    period | " + "  ".join(f"n{m}" for m in range(N)))
    for P in range(periods):
        say(f"      {P:2d}   |  " + "   ".join(str(val.get((m, P), "-")) for m in range(N)))


def check_2lal(tag, T, periods, title, expect=None, constant=False):
    w = Wave(f"{DATA}/{tag}.dat")
    val, bad = decode_2lal(w, T, periods)
    n_inv, bad_inv = inversions(val)
    say(f"\n2LAL ring, {title}")
    say("  decoded logic value per node per rail period (1 = TRUE on a, 0 = TRUE on n):")
    table(val, periods)
    ok = not bad and not bad_inv
    say(f"  every node, every period: exactly one sub-chain TRUE, idle one at rest .. "
        f"{'PASS' if not bad else 'FAIL'} ({len(val)} node-periods)")
    say(f"  every stage: output = NOT input one TPHASE later ......................... "
        f"{'PASS' if not bad_inv else 'FAIL'} ({n_inv - len(bad_inv)}/{n_inv})")
    if expect is not None:
        mism = [k for k, x in expect.items() if k in val and val[k] != (x == "a")]
        cov = sum(k in val for k in expect)
        ok &= not mism and cov == len(expect)
        say(f"  agrees with the deck's own expected table ({DECK_2LAL}) ........ "
            f"{'PASS' if not mism and cov == len(expect) else 'FAIL'} ({cov - len(mism)}/{len(expect)})")
    if constant:
        moving = [m for m in range(N) if len({v for (mm, _), v in val.items() if mm == m}) != 1]
        ok &= not moving
        say(f"  constant data: every node holds one value in all periods ............. "
            f"{'PASS' if not moving else 'FAIL ' + str(moving)}")
    for s in (bad + bad_inv)[:12]:
        say("    " + s)
    say(f"  -> {'PASS' if ok else 'FAIL'}")
    return w, val, ok


def deck_expectations():
    exp = {}
    for line in open(DECK_2LAL):
        m = re.match(r"\* node (\d+), period (\d+): TRUE on ([an])\s*$", line)
        if m:
            exp[(int(m.group(1)), int(m.group(2)))] = m.group(3)
    return exp


# =============================================================== figures
def stack(out, title, w, xexpr, xlab, xr, size, panels, key_first_only=False, fs=1.0):
    """Vertical stack of 0..VDD panels sharing one x axis (gnuplot, pngcairo).
    fs scales every font, e.g. 1.6 for a figure that is shrunk onto a slide."""
    f = lambda pt: round(pt * fs)
    g = [f'set terminal pngcairo noenhanced size {size[0]},{size[1]} font "Sans,{f(12)}"',   # keep _ literal
         f"set output '{out}'",
         "set datafile columnheaders",
         f"set multiplot layout {len(panels)},1 margins {0.06 + 0.02 * fs:.3f},0.985,"
         f"{75 * fs / size[1]:.3f},{1 - 75 * fs / size[1]:.3f} spacing 0,0.010",
         f"set xrange [{xr[0]}:{xr[1]}]", "set yrange [-0.3:2.25]",
         f'set ytics ("0" 0, "1.8" 1.8) font "Sans,{f(10)}"', "set grid xtics ytics",
         f'set xtics font "Sans,{f(11)}"', f'set xlabel font "Sans,{f(12)}"',
         f'set key top right font "Sans,{f(10)}" samplen 1.5 horizontal opaque',
         'set format x ""', "unset xlabel",
         f'set title "{title}" font "Sans,{f(13)}"']
    for i, p in enumerate(panels):
        if i == 1:
            g.append("unset title")
        if i == len(panels) - 1:
            g += ['set format x "%g"', f'set xlabel "{xlab}"']
        if key_first_only and i == 1:
            g.append("unset key")
        g.append("unset label")
        g.append(f'set label "{p["name"]}" at graph 0.005, graph 0.86 left font "Sans,{f(11)}" '
                 f'front tc rgb "#333"')
        for x, y, txt in p.get("marks", []):
            g.append(f'set label "{txt}" at {x},{y} center font "Sans:Bold,{f(15)}" front tc rgb "#c0242c"')
        series = [f"'{w.path}' using ({xexpr}):{w.idx(c)} with lines lw {lw} dt {dt} "
                  f"lc rgb '{col}' title '{lab}'" for c, lab, col, lw, dt in p["series"]]
        g.append("plot " + ", ".join(series))
    g.append("unset multiplot")
    subprocess.run(["gnuplot"], input="\n".join(g) + "\n", text=True, check=True)
    say(f"  wrote {out}")


GRN, BLU, PUR, GLD = "#1a7f37", "#0969da", "#8B008B", "#B8860B"
RAIL = ["#a4237a", "#12866B", "#0969da", "#C2704A"]


def fig_ecrl(w, labels, T):
    tp = T  # ns
    out_marks = [((4 * k + 2.5) * tp, 1.0, str(1 - IN)) for k, IN in labels if IN == 0]
    outb_marks = [((4 * k + 2.5) * tp, 1.0, str(IN)) for k, IN in labels if IN == 1]
    in_marks = [((4 * k + 2.5) * tp, 1.0, f"IN={IN}") for k, IN in labels]
    stack(f"{FIGS}/ecrl_inverter_T{T}.png",
          f"ECRL inverter (ecrl/ecrl_slowramp.sp), sky130 tt, W = 1 um, CL = 25 fF, TPHASE = {T} ns"
          "   |   red = decoded output: OUT pulses when IN = 0, OUTB when IN = 1",
          w, "$1*1e9", "time  (ns)", (0, 20 * tp), (1700, 720),
          [dict(name="PHI", series=[("v(phi)", "power clock", PUR, 2.5, 1)]),
           dict(name="IN", series=[("v(in)", "input (slow ramp in the wait window)", GLD, 2.5, 1)],
                marks=in_marks),
           dict(name="OUT", series=[("v(out)", "OUT", GRN, 2.5, 1)], marks=out_marks),
           dict(name="OUTB", series=[("v(outb)", "OUTB", BLU, 2.5, 1)], marks=outb_marks)])


def node_series(m):
    return [(f"v(at{m})", "a.T", GRN, 2.2, 1), (f"v(nt{m})", "n.T", BLU, 2.2, 1),
            (f"v(ac{m})", "a.C", GRN, 1.2, 2), (f"v(nc{m})", "n.C", BLU, 1.2, 2)]


def marks(val, m, periods, y=1.0):
    return [(4 * P + (m % 4) + 1.5, y, str(val[(m, P)])) for P in range(periods) if (m, P) in val]


def fig_2lal_stage(w, val, T, m=3):
    o = m + 1
    tp = T * 1e-9
    stack(f"{FIGS}/2lal_inverter_stage_T{T}.png",
          f"2LAL inverter stage, node {m} -> node {o}, TPHASE = {T} ns      "
          "red = decoded value: 1 = a TRUE, 0 = n TRUE",
          w, f"$1/{tp}", "time  (units of TPHASE)", (0, 24), (1700, 900),
          [dict(name="rails", series=[(f"v(p{i})", f"phi{i}", RAIL[i], 1.8, 1) for i in range(4)]),
           dict(name=f"IN  = node {m}", series=node_series(m), marks=marks(val, m, 6)),
           dict(name=f"OUT = node {o}", series=node_series(o), marks=marks(val, o, 6))],
          fs=1.7)


def fig_2lal_ring(w, val, T, out, note):
    tp = T * 1e-9
    stack(out, f"2LAL 8-stage quad-rail inverter ring, TPHASE = {T} ns, {note}"
               "\\nred = decoded logic value per node per rail period (1 = a TRUE, 0 = n TRUE); "
               "solid = T rail, dashed = C rail",
          w, f"$1/{tp}", "time  (units of TPHASE)", (0, 25), (1700, 1500),
          [dict(name=f"node {m} (phi{m % 4})", series=node_series(m), marks=marks(val, m, 6))
           for m in range(N)], key_first_only=True)


# ================================================================== main
if __name__ == "__main__":
    os.chdir(HERE)
    if not os.path.isdir(DATA):
        sys.exit("no data/ -- run ./run_waveforms.sh first")
    os.makedirs(FIGS, exist_ok=True)
    allok = True
    say("Waveform decode of the ECRL and 2LAL inverters  (python3 check_waveforms.py)")
    say(f"Thresholds: high > {HI:.2f} V, low < {LO:.2f} V  (0.9 / 0.1 of VDD, same as the decks)")

    for T in (1, 10, 100):
        w, labels, ok = check_ecrl(T)
        allok &= ok
        if T == 10:
            fig_ecrl(w, labels, T)

    exp = deck_expectations()
    for T in (1, 10, 100):
        w, val, ok = check_2lal(f"2lal_T{T}", T, 6, f"alternating data, TPHASE = {T} ns", expect=exp)
        allok &= ok
        if T == 10:
            fig_2lal_stage(w, val, T)
            fig_2lal_ring(w, val, T, f"{FIGS}/2lal_ring_all_nodes_T{T}.png", "alternating data")
    w, val, ok = check_2lal("2lal_const_T10", 10, 6,
                            "CONSTANT data (wave 1 seeded like wave 0), TPHASE = 10 ns", constant=True)
    allok &= ok
    fig_2lal_ring(w, val, 10, f"{FIGS}/2lal_ring_constant_data_T10.png",
                  "CONSTANT data: every node holds its value")
    _, _, ok = check_2lal("2lal_long_T100", 100, 20,
                          "20 rail periods at TPHASE = 100 ns (does the data leak away?)")
    allok &= ok

    say(f"\nOVERALL: {'PASS' if allok else 'FAIL'}")
    open(REPORT, "w", newline="\n").write("\n".join(out_lines) + "\n")
    print(f"-> {REPORT}")
    sys.exit(0 if allok else 1)
