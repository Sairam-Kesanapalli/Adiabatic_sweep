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
| `2lal/superseded/` | the open-chain 2LAL decks: their last node is never restored, which inflates the energy (up to 47x) |
| `plots/` | `make_plots.py` and the energy plots it writes (`.png`, `.png.dat`, ngspice `.cir`) |
| `verification/` | waveform dumps, the independent decoder, the mutation test, their reports and figures |
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
  intact passes (M7).  Energy is guarded by the settling check, section 5,
  and the chain-boundary experiment that motivated the ring.  (3) The TRUE side
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

---

## 5. Check the inverters at the waveform level

    verification/verify_all.sh       # ~3 min, runs the three steps below

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

---

## 6. Make and view the graphs

    python3 plots/make_plots.py      # regenerates all 6 PNGs and all 4 .cir decks in plots/

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
