# How to check everything in this repository

Commands run from the repository root unless they start with `cd`.
Needs Linux or WSL with `ngspice` (tested with ngspice-42), `python3` and
`gnuplot` (plots and figures only).
`ngspice -b` = batch. `-o FILE` sends the log (with the `.meas` results) to FILE.
Run a deck from its own directory: its model include is a relative path.

---

## 0. Setup, once per machine

    models/link_pdk.sh                    # -> models/sky130-ngspice-models -> ~/.volare/sky130A
    models/link_pdk.sh /path/to/sky130A   # or any other sky130A install

Every deck reaches the device models through that one link, so without it
every run fails at the include step.  The link is not in git.

| directory | what it is |
|---|---|
| `models/` | `sky130_01v8_tt_fast.spice` (reduced include, verified == full `.lib tt`), `link_pdk.sh` |
| `ecrl/` | **ECRL deck in use** `ecrl_slowramp.sp`, its sweep script and CSV |
| `ecrl/baseline/` | your original ECRL deck, width sweep, CSV and ngspice plot decks (unchanged) |
| `2lal/` | **2LAL deck in use** `2LAL_inverter_ring.sp` (8-stage ring), its generator `make_2lal_ring.py`, sweep script and CSV |
| `2lal/superseded/` | the open-chain 2LAL decks: their last node is never restored, which inflates the energy (up to 47x); `2lal_inverter_sweep_openchain.csv` is their last sweep, kept as the negative case for section 5b |
| `plots/` | `make_plots.py` and the energy plots it writes (`.png`, `.png.dat`, ngspice `.cir`) |
| `verification/` | waveform dumps, the independent decoder, the mutation test, the energy-meter calibration, their reports and figures |
| `slides/` | `make_slides.py`, the deck it builds, and `figs/` |

---

## 1. Run one simulation

    cd 2lal && ngspice -b -o run.out 2LAL_inverter_ring.sp && grep -iE "^e_a |^e_b |^e_c " run.out; cd ..
    cd ecrl && ngspice -b -o run.out ecrl_slowramp.sp && grep -iE "^e_|^out" run.out; cd ..

2LAL ring: `e_a` = rail period 2, `e_b` = rail period 3 (must equal `e_a` once
settled), `e_c` = average of periods 2..5, the plotted value.
ECRL: `e_a` = the 0->1 data cycle, `e_b` = the 1->0 cycle, `e_c` = their average;
`e_a0` / `e_b0` = the same two cycles two clock periods earlier (must match).
All in joules per operation. Multiply by 1e15 for fJ.

---

## 2. Change W / L / TPHASE for a one-off run

Edit the `.param` lines at the top, or override on a copy:

    cd 2lal
    sed -e 's/^\.param WN     = .*/.param WN     = 2.0/' \
        -e 's/^\.param WP     = .*/.param WP     = 2.0/' \
        -e 's/^\.param TPHASE = .*/.param TPHASE = 5n/' \
        2LAL_inverter_ring.sp > try.sp
    ngspice -b -o try.out try.sp && grep -iE "^e_c " try.out

WIDTHS ARE IN MICRONS (`2.0` means 2 um). The models set `.option scale=1.0u`.
Writing `2.0u` gives "could not find a valid modelname".

For ECRL the width is a literal on the instance lines, not a param:

    cd ecrl
    sed -e 's/l=0.15 w=1 m=1/l=0.15 w=2.0 m=1/g' \
        -e 's/^\.param TPHASE=.*/.param TPHASE=5n/' \
        ecrl_slowramp.sp > try.sp
    ngspice -b -o try.out try.sp && grep -i "^e_c" try.out

To change the 2LAL *structure* (stages, seed, checked periods), edit
`2lal/make_2lal_ring.py` and run `python3 2lal/make_2lal_ring.py`; do not edit the
generated deck by hand.

---

## 3. Check the circuit is FUNCTIONALLY correct (do this before trusting energy)

    cd 2lal
    ngspice -b -o run.out 2LAL_inverter_ring.sp
    awk '/^chkhi_/ && $3<1.62 {print "BAD", $0} /^chklo_/ && $3>0.18 {print "BAD", $0}' run.out
    grep -cE "^chk(hi|lo)_" run.out          # 96

No `BAD` lines = pass.

    cd ecrl
    ngspice -b -o run.out ecrl_slowramp.sp
    grep -iE "^out_a|^outb_a|^out_b|^outb_b" run.out

IN=1 (cycle A) -> OUT ~0 and OUTB ~1.8.  IN=0 (cycle B) -> the opposite.

Both sweep scripts enforce these at every one of their 42 points (section 4).

### 3a. What the 96 2LAL checks are

They are `.meas` lines that `2lal/make_2lal_ring.py` writes into the deck:
8 nodes x 2 consecutive rail periods (3 and 4) x 6 measurements = 96.
With `ts` = the start of node m's pulse in period P = `P*TRAIL + (m%4)*TPHASE`:

| measurement | sub-chain | when | must be |
|---|---|---|---|
| T | the TRUE one | mid-plateau, `ts + 1.5*TPHASE` | > 0.9 VDD |
| C | the TRUE one | mid-plateau | < 0.1 VDD |
| T | the TRUE one | mid-rest, `ts + 3.5*TPHASE` | < 0.1 VDD (back at rest) |
| C | the TRUE one | mid-rest | > 0.9 VDD |
| MAX of T | the idle one | whole period `ts .. ts + 4*TPHASE` | < 0.1 VDD (never rises) |
| MIN of C | the idle one | whole period | > 0.9 VDD (never falls) |

Which sub-chain is TRUE at node m in period P is predicted *from the seed*,
not read from the simulation: the generator traces each data wave back to
its `.ic` position, using two rules (a wave moves one node per TPHASE, and
every stage crosses sub-chains, which is the inversion).  The deck records
the prediction as a comment above each group: `* node m, period P: TRUE on a`.

### 3b. Why they can be trusted, and where they stop

* **They can fail.** `verification/mutation_test_2lal.sh` breaks the ring in
  one place at a time and counts failing checks (`verification/mutation_report.txt`):

  | defect | checks failing | E_C |
  |---|---|---|
  | none | 0 / 96 | 6.29 fJ |
  | T/C outputs swapped on one stage | 24 / 96 | 33.5 fJ |
  | restore gate XR1 removed | 48 / 96 | 102 fJ |
  | one stage non-inverting | 16 / 96 | **6.29 fJ** |
  | one stage clocked a phase late | 40 / 96 | 154 fJ |
  | forward C gate XF2 removed | 16 / 96 | 64.6 fJ |
  | data seed not alternating | 32 / 96 | 6.25 fJ |
  | 1 MOhm leak on one node | 0 / 96 (expected) | 9.66 fJ |

  The non-inverting stage is why they matter: its energy is indistinguishable
  from the correct circuit, so only the logic checks see it.
* **An independent method agrees.** `verification/check_waveforms.py` never uses
  the generator's prediction to pass or fail.  It decodes every node in every
  rail period from the raw waveform and checks only that exactly one sub-chain
  pulses, the idle one stays at rest, and each stage's output is NOT its input
  one TPHASE later.  It then compares its decoded table with the deck's
  `TRUE on` comments: 16 / 16 agree at TPHASE = 1, 10 and 100 ns.
* **Where they stop.** (1) They check the *expected pattern* (alternating
  data); a deliberately different seed fails them, which is mutant M6.
  `check_waveforms.py` covers constant data separately.  (2) They are logic
  checks, not energy checks: a leak that wastes energy but keeps the logic
  intact passes (M7).  Energy is guarded by the settling check, the
  calibration in section 5b, and the chain-boundary experiment that
  motivated the ring.  (3) The TRUE side
  is sampled at two instants, not monitored continuously.  (4) Only rail periods
  3 and 4 are checked; the decoder covers periods 0..5 (and 0..19 in the long run).

---

## 4. Run the sweeps

    2lal/run_2lal_sweep.sh                   # ~5 min  -> 2lal/2lal_inverter_sweep.csv
    ecrl/run_ecrl_slowramp_sweep.sh          # ~3 min  -> ecrl/ecrl_slowramp_sweep.csv

Both stop at the first bad point (exit 1, `FAIL [W.._T..]: reason`) instead of
leaving a hole in the CSV.  Per point they check:
* the sed edits landed;
* ngspice exited 0 with no error/warning lines;
* every energy `.meas` is a number;
* the simulator used the requested W on every FET (`show m : w`, read back from
  an operating-point run) and the requested TPHASE (`chk_tphase` = 1.5*TPHASE);
* the logic is correct: 2LAL all 96 checks, ECRL `OUT_A/OUTB_A/OUT_B/OUTB_B`
  within 10% of VDD of 0 / 1.8 / 1.8 / 0;
* the circuit has settled: 2LAL `E_A`, `E_B` within 1% of `E_C`; ECRL `E_A0`, `E_B0`
  within 1% of `E_A`, `E_B`.

Every deck and log is kept in `2lal/runs_2lal/` and `ecrl/runs_ecrl_slowramp/`.

Your original ECRL sweep still works and is unchanged:

    cd ecrl/baseline && ./run_width_sweep.sh     # ~55 min -> width_sweep.csv

(That one is slow because it loads the full sky130 `.lib` on every one of its 42
runs, ~77 s each. Point it at `../../models/sky130_01v8_tt_fast.spice` to get
~1.5 s each.)

Read a result:

    column -t -s, 2lal/2lal_inverter_sweep.csv
    column -t -s, ecrl/ecrl_slowramp_sweep.csv

### 4b. Channel-length and load-capacitance sweeps

    2lal/run_2lal_lc_sweep.sh length   # -> 2lal/2lal_length_sweep.csv
    2lal/run_2lal_lc_sweep.sh cap      # -> 2lal/2lal_cap_sweep.csv
    ecrl/run_ecrl_lc_sweep.sh length   # -> ecrl/ecrl_length_sweep.csv
    ecrl/run_ecrl_lc_sweep.sh cap      # -> ecrl/ecrl_cap_sweep.csv
    2lal/run_2lal_lc_sweep.sh fast     # -> 2lal/2lal_fast_sweep.csv
    ecrl/run_ecrl_lc_sweep.sh fast     # -> ecrl/ecrl_fast_sweep.csv

(They are independent; the four length/load runs in parallel take about
8 min, the two fast runs under a minute.)  The `fast` mode runs the nominal
point (W = 1.0 um, L = 0.15 um, CL = 25 fF) at TPHASE = 0.5, 0.6, 0.65, 0.7,
0.8, 0.9 and 1 ns, where the ECRL and 2LAL curves cross: at TPHASE = 0.66 ns,
65.3 fJ (`plots/ecrl_vs_2lal_crossover.png`; `make_plots.py` finds the crossing
by interpolating between the two points that bracket it).  Its 1 ns point is
the anchor against the width sweep.

| sweep | swept | held fixed | TPHASE |
|---|---|---|---|
| length | L = 0.15, 0.18, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0 um | W = 1.0 um, CL = 25 fF | 1 .. 100 ns |
| load | CL = 5, 10, 25, 50, 100, 200 fF | W = 1.0 um, L = 0.15 um | 1 .. 100 ns |

The L grid includes sky130's characterised lengths (0.15, 0.18, 0.25, 0.5, 1,
2 um, where the model bins meet).  W = 1.0 um has model bins at every length.

**Why W = 1.0 um and L = 0.15 um are the fixed points.**
* *They are the anchor of every earlier result.*  Both sweeps pass through
  W = 1.0, L = 0.15, CL = 25 fF, and each script checks at the end that it
  reproduces the width sweep there (it does, to every printed digit).  A
  change in a deck or the models therefore shows up as a failed anchor.
* *A "formula" width does not stay optimal across a length sweep.*  The
  adiabatic term is a ~ R * (CL + k*W)^2 with R ~ 1/W, minimised at
  W* = CL / k (Fischer et al. 2003/2004: widening pays only while the
  transistor's own capacitance stays below the load).  At L = 0.15 um, the
  width sweep gives k = 7.1 fF/um, so W* = 3.5 um; but the gate part of k grows
  with L (12.6 fF/um per um of L, from the length sweep), so
  k = 7.1 + 12.6*(L - 0.15) and W* falls to about 1.4 um at L = 1 um and
  0.8 um at L = 2 um.  Fixing W at W*(0.15) = 3.5 um
  would make the long-L points mostly a measurement of gate capacitance.
* *The extremes are worse.*  Minimum width (0.42 um) maximises R, so the
  long-L points fail logic at even more speeds, and sits next to narrow-width
  bin edges.  The largest width makes the gate load W*L dominate CL.
* *L = 0.15 um for the load sweep* is the minimum length, which the length
  sweep shows is the lowest-energy length at every TPHASE except 100 ns, where
  0.18 um is 0.8 % lower (less leakage).

**A point whose logic fails is recorded, not fatal.**  Long channels and big
loads cannot reach the rails at the fastest clocks; those rows get
`status=logic_fail` (or `unsettled`) and are left out of fits and plots.
Everything else still stops the sweep: a substitution that did not land, an
ngspice error or warning, a missing `.meas`, or W, L or TPHASE read back from
the simulator differing from the request (`show m : w l` on every FET).

**Diffusion geometry no longer follows L.**  The 2LAL deck used to set
`as='WN*L*1.77'`, so a longer channel also grew the source/drain junctions.
`make_2lal_ring.py` now uses a separate `LDIF = 0.15` for as/ad/ps/pd.  At
L = 0.15 the deck is numerically identical (the width sweep and every
report are unchanged).  `verification/cal_tg_ron.sp` got the same fix.

Energy per operation = energy per clock (rail) period per gate (column) =
energy per data transaction, because the data alternates every period.

---

## 5. Check the inverters at the waveform level

    verification/verify_all.sh       # ~4 min, runs the steps below and section 5b

    verification/run_waveforms.sh            # -> verification/data/ (not in git)
    python3 verification/check_waveforms.py  # -> waveform_report.txt, figures/
    verification/mutation_test_2lal.sh       # -> mutation_report.txt

`check_waveforms.py` decodes the logic value of every output in every clock
period (ECRL: OUT = NOT IN in each cycle; 2LAL: per node per rail period, and
output = NOT input across every stage), at TPHASE = 1, 10 and 100 ns, plus two
2LAL stress runs: constant data, where every node must hold its value, and 20
rail periods at TPHASE = 100 ns, to check that the data does not leak away.
Figures in `verification/figures/`:

| figure | shows |
|---|---|
| `ecrl_inverter_T10.png` | PHI, IN, OUT, OUTB with the decoded values |
| `2lal_inverter_stage_T10.png` | one 2LAL stage: rails, input node 3, output node 4 |
| `2lal_ring_all_nodes_T10.png` | all 8 ring nodes, alternating data |
| `2lal_ring_constant_data_T10.png` | all 8 ring nodes, constant data |

### 5b. Check the energy meter, and that both families obey their energy model

    verification/run_calibration.sh          # ~2 min -> verification/data/calibration/
    python3 verification/check_calibration.py  # -> calibration_report.txt, exit 1 on failure

Check 1 asks whether the energy numbers can be trusted at all:

* **1a, against static CMOS.** `cal_cmos.sp` puts a CMOS inverter through the
  2LAL deck's own 1 F energy integrator at CL = 0..100 fF.  Energy per cycle is
  (CL + Cpar)*VDD^2 + short-circuit energy, so dE/dCL must be VDD^2 = 3.24 fJ/fF
  whatever the unknowns are.  Measured 3.250 (+0.3 %), the same at 40 and
  400 ns.  It also gives the "no adiabatic benefit" line: 43.8 fJ per transition.
* **1b, convergence.** Both decks at TPHASE = 1, 10, 100 ns with the maximum
  step cut 4x (2LAL TPHASE/2000, ECRL 4 ps) and reltol 1e-6: nothing moves by
  more than 0.06 %.  (TPHASE/2500 and 2 ps hit "timestep too small" at a pulse
  corner, which is why the cut is 4x and 2.5x.)
* **1c, an adiabatic case with an exact answer.** `cal_rc.sp` drives an ideal
  10 kohm / 25 fF from the rail trapezoid.  About 81 fJ goes out and comes back
  each period; the meter has to find the 0.4-30 fJ residue between two nearly
  cancelling flows, which static CMOS never tests.  The checker solves the RC
  equation itself and the meter agrees to 0.01 %.

Check 2 fits both sweeps to E(T) = K*g(T, tau) + b + c*T, where g is the exact
loss of one RC ramp (-> tau/T for T >> tau), b a fixed residue and c*T leakage:

* **2LAL is fully adiabatic.** Fit RMS 0.4-1.1 %, residue |b| <= 0.17 % of
  CL*VDD^2 at every width.  The 1/T coefficient matches the transmission gate's
  measured on-resistance (`cal_tg_ron.sp`): solving a = 4*C_eff^2*VDD^2*R_mean
  for the node capacitance gives C_eff = 24.7 fF + 7.1 fF/um * W, and the
  intercept lands on the deck's 25 fF load.
* **ECRL keeps a threshold residue**, b ~ 15 fJ = 18 % of CL*VDD^2.  An energy
  split by device and clock phase closes on the total within 1.5 %; 69 % of it
  at 100 ns is the pull-up pFET on the clock rise.  Integrating that catch-up
  from the pFET's DC table alone (`cal_pfet_rise.sp`, no transient) predicts
  83-84 % of it at 10 and 100 ns.  The fitted c comes out negative because the
  residue shrinks slowly with T: the output's residual voltage falls from
  0.72 V at 1 ns to 0.42 V at 100 ns.

**The 2LAL test is run against the bug it exists to catch, every time.**
`2lal/superseded/2lal_inverter_sweep_openchain.csv` is the last sweep of the
open-chain deck (from commit d8369e0^, before the ring).  The checker runs the
same fit on it and *requires* every width to be rejected; today all six are
(RMS 11-21 %, residue 16-83 % of CL*VDD^2).  If a later change to the fit or
its thresholds let that data pass, the check `open-chain 2LAL rejected at
every width` fails.

### 5c. Check the length and load sweeps against the energy model

    verification/run_calibration.sh            # also measures R_TG(L) and Vth(L)
    python3 verification/check_lc_scaling.py   # -> lc_scaling_report.txt, exit 1 on failure

The adiabatic loss of a node swing through resistance R is
a = n * R * C_eff^2 * VDD^2 per 1/T (Fischer et al., Adv. Radio Sci. 2, 221,
2004, eq. 1), with n = 4 node swings per 2LAL operation.  That predicts:

* **Load, 2LAL.**  sqrt(a / 4 VDD^2) = sqrt(R) * (CL + Cp) is a straight line in
  CL.  Measured: linear within 1.0 % at all six loads; its slope gives
  R = 4.54 kohm against the transmission gate's DC on-resistance of 4.92 kohm
  (-8 %), its intercept Cp = 7.7 fF.  Energy per doubling of CL approaches
  x4 (log-log slope 1.6-1.8 at TPHASE = 10 ns).
* **Load, ECRL.**  The fixed threshold residue (CL*Vth^2/2, eq. 2 of the same
  paper) grows with CL, 2.5 -> 153 fJ, and the slow-clock energy is close to
  linear in CL (log-log slope 1.2-1.3 at 100 ns).
* **Length, 2LAL.**  With R(L) measured at each length (`cal_tg_ron.sp`),
  C_eff(L) = sqrt(a / (4 VDD^2 R(L))) = 28.2 fF + 12.6 fF/um * L, linear within
  5.3 %: the 25 fF load plus junctions, plus gate charge growing with W*L.
  12.6 fF/um lies between two estimates from the oxide (Cox = 8.3 fF/um^2):
  2 gates in inversion per node (16.6) and the same gates inverted only above
  Vth (~10).  Four full gates would be 33.
* **Length, ECRL.**  The threshold residue grows with L, 15.1 -> 27.6 fJ
  (L = 0.15 -> 1 um), as the pull-up pFET's |Vth| does (0.73 -> 0.94 V,
  `cal_vth.sp`).  The nFET's Vth goes the other way (0.68 -> 0.55 V,
  sky130's reverse short-channel effect).
* **A published 2LAL number.**  Frank et al. (ICRC 2020, Sandia talk SAND,
  slide 19) report 6.9 aJ per cycle per FET for a 2LAL shift register at
  f = 1 MHz, CL = 10 fF, 50 % activity, W = 480 nm in Sandia's 180 nm process
  (37 aJ in their 350 nm process).  `run_calibration.sh` runs this ring at the
  same point in SKY130 (TPHASE = 250 ns, W = 0.48 um, L = 0.18 um): all 96
  logic checks pass and it dissipates 8.11 aJ per FET per cycle, 1.17x the
  published value.  A quad-rail column has 16 FETs and one of its two
  sub-chains pulses per cycle, which is 50 % activity per sub-chain.

---

## 6. Make and view the graphs

    python3 plots/make_plots.py      # regenerates every PNG and the 4 .cir decks in plots/

    xdg-open plots/2lal_energy_vs_length.png      # length sweep, one line per TPHASE
    xdg-open plots/ecrl_energy_vs_length.png
    xdg-open plots/2lal_energy_vs_cap.png         # load sweep, with E ~ CL and E ~ CL^2 guides
    xdg-open plots/ecrl_energy_vs_cap.png
    xdg-open plots/ecrl_vs_2lal_length_T10.png    # the two families at TPHASE = 10 ns
    xdg-open plots/ecrl_vs_2lal_cap_T10.png

    xdg-open plots/ecrl_vs_2lal_W1.0.png          # x-axis = transition freq 1/TPHASE
    xdg-open plots/ecrl_vs_2lal_W1.0_fclock.png   # x-axis = power-clock freq 1/(4*TPHASE)
    xdg-open plots/2lal_energy_vs_ftr.png
    xdg-open plots/ecrl_slowramp_energy_vs_ftr.png

Same data in ngspice's own plotter, your original style (needs a desktop session):

    cd plots
    ngspice 2lal_energy_vs_ftr.cir
    ngspice ecrl_slowramp_energy_vs_ftr.cir

---

## 7. Prove a plotted point came from a real simulation

    grep "^100 " plots/2lal_energy_vs_ftr.png.dat     # what gnuplot was handed
    grep "^1.0,10," 2lal/2lal_inverter_sweep.csv      # the CSV row behind it
    (cd 2lal && ngspice -b -o p.out 2LAL_inverter_ring.sp && grep -i "^e_c " p.out)

All three must agree (6.28912e-15 J = 6.28912 fJ at W=1.0 um, TPHASE=10 ns).

---

## 8. Prove the fast model include equals the full PDK library

    cd ecrl/baseline
    sed '/^\.print tran/d' ecrl_baseline.sp > full.sp        # full .lib  (~77 s)
    sed -e '/^\.print tran/d' \
        -e 's|^\.lib ".*" tt|.include "../../models/sky130_01v8_tt_fast.spice"|' \
        ecrl_baseline.sp > fast.sp                            # fast      (~1.5 s)
    ngspice -b -o full.out full.sp; ngspice -b -o fast.out fast.sp
    grep -i "^e_op" full.out fast.out
    grep "^1.0,10," width_sweep.csv          # your original number

All three: 1.80491e-14.

---

## 9. Reproduce the main ECRL finding

The old curve was measuring a cycle in which the DATA NEVER CHANGED.
Hold the data static in the new deck and it reproduces your old number exactly:

    cd ecrl
    sed -e 's|^VIN IN 0 PULSE.*|VIN IN 0 DC 0|' \
        -e 's/^\.param TPHASE=.*/.param TPHASE=100n/' ecrl_slowramp.sp > static.sp
    ngspice -b -o static.out static.sp
    grep -i "^e_a " static.out          # 5.3622e-15 J  == your 5.36221 fJ

Now the same deck with data alternating every cycle:

    grep "^1.0,100," ecrl_slowramp_sweep.csv    # 12.4589 fJ  (2.3x higher)

---

## 10. Useful one-liners

    grep -n "^\.param" 2lal/2LAL_inverter_ring.sp         # all the knobs
    grep -iE "error|could not find|Undefined" run.out     # did it actually run?

Device counts (2 FETs per transmission gate):

    grep -cE "^X.* TG *(;|$)"         2lal/2LAL_inverter_ring.sp   # 4  TG per BUF8P cell = 8 FETs
    grep -cE "^X[PN][0-9].* BUF8P *$" 2lal/2LAL_inverter_ring.sp   # 16 cells (8 stages x 2 sub-chains)
    grep -cE "^XM"                    ecrl/ecrl_slowramp.sp        # 4  FETs in the whole ECRL gate

So one quad-rail 2LAL column = 2 cells = 16 FETs, against 4 for an ECRL gate.
All 8 ring stages are metered (128 FETs); energy is divided by 8 columns.

If a run produces no `e_c` line, it errored - always check with the grep above
rather than assuming a blank result means zero.
