# How to check everything in this directory

All paths relative to `~/Documents/Cutout/Adiabatic_sweep`.
`ngspice -b` = batch. `-o FILE` sends the log (with the `.meas` results) to FILE.

---

## 0. What lives where

| file | what it is |
|---|---|
| `2LAL_inverter.sp` | 4-way cell comparison: BUF4 / BUF8P / naive-crossed NOT / quad-rail NOT |
| `2LAL_inverter_multi_test.sp` | inverter only, quad-rail, axes matched to ECRL |
| `ecrl_exp1/ecrl_baseline.sp` | your original ECRL deck (untouched) |
| `ecrl_exp1/ecrl_slowramp.sp` | ECRL with slow-ramp input + alternating data |
| `sky130_01v8_tt_fast.spice` | reduced model include (verified == full `.lib tt`) |
| `sky130-ngspice-models` | symlink -> `~/.volare/sky130A` |
| `*_sweep.csv` | sweep results |
| `*.png` | gnuplot renders |
| `*.cir` | ngspice plot decks (your original style) |

---

## 1. Run one simulation

    ngspice -b -o run.out 2LAL_inverter_multi_test.sp
    grep -iE "^e_a |^e_b |^e_c " run.out

    cd ecrl_exp1
    ngspice -b -o run.out ecrl_slowramp.sp
    grep -iE "^e_|^out" run.out
    cd ..

`e_a` = the 0->1 data cycle, `e_b` = the 1->0 cycle, `e_c` = their average.
All in joules. Multiply by 1e15 for fJ.

---

## 2. Change W / L / TPHASE for a one-off run

Edit the `.param` lines at the top, or override on a copy:

    sed -e 's/^\.param WN     = .*/.param WN     = 2.0/' \
        -e 's/^\.param WP     = .*/.param WP     = 2.0/' \
        -e 's/^\.param TPHASE = .*/.param TPHASE = 5n/' \
        2LAL_inverter_multi_test.sp > try.sp
    ngspice -b -o try.out try.sp && grep -iE "^e_c " try.out

WIDTHS ARE IN MICRONS (`2.0` means 2 um). The models set `.option scale=1.0u`.
Writing `2.0u` gives "could not find a valid modelname".

For ECRL the width is a literal on the instance lines, not a param:

    cd ecrl_exp1
    sed -e 's/l=0.15 w=1 m=1/l=0.15 w=2.0 m=1/g' \
        -e 's/^\.param TPHASE=.*/.param TPHASE=5n/' \
        ecrl_slowramp.sp > try.sp
    ngspice -b -o try.out try.sp && grep -i "^e_c" try.out

---

## 3. Check the circuit is FUNCTIONALLY correct (do this before trusting energy)

    ngspice -b -o run.out 2LAL_inverter_multi_test.sp
    grep -iE "^a[1-4]_b[01]_[tc] " run.out

Read it as: TRUE = (T=1.8, C=0), FALSE = (T=0, C=1.8).
Every stage inverts, so for input bit b:  a1=NOT b, a2=b, a3=NOT b, a4=b.
(Stage 4's sample lands in the next rail period - that is expected.)

ECRL:

    cd ecrl_exp1 && ngspice -b -o run.out ecrl_slowramp.sp
    grep -iE "^out_a|^outb_a|^out_b|^outb_b" run.out

IN=1 -> OUT ~0 and OUTB ~1.8.  IN=0 -> the opposite.

---

## 4. Run the sweeps

    ./run_2lal_sweep.sh                      # ~5 min  -> 2lal_inverter_sweep.csv
    ecrl_exp1/run_ecrl_slowramp_sweep.sh     # ~3 min  -> ecrl_slowramp_sweep.csv

Both stop at the first bad point (exit 1, `FAIL [W.._T..]: reason`) instead of
leaving a hole in the CSV.  Per point they check: the sed edits landed, ngspice
exited 0 with no error/warning lines, every energy `.meas` is a number, the
simulator used the requested W on every FET (`show m : w`, read back from an
operating-point run) and the requested TPHASE (`chk_tphase` = 1.5*TPHASE).
Every deck and log is kept in `runs_2lal/` and `ecrl_exp1/runs_ecrl_slowramp/`.

The PDK symlinks are not in git; recreate them once per machine:

    ln -s ~/.volare/sky130A sky130-ngspice-models
    ln -s ~/.volare/sky130A ecrl_exp1/sky130-ngspice-models

Your original ECRL sweep still works and is unchanged:

    cd ecrl_exp1 && ./run_width_sweep.sh     # ~55 min -> width_sweep.csv

(That one is slow because it loads the full sky130 `.lib` on every one of its 42
runs, ~77 s each. Point it at `sky130_01v8_tt_fast.spice` to get ~1.5 s each.)

Read a result:

    column -t -s, 2lal_inverter_sweep.csv
    column -t -s, ecrl_exp1/ecrl_slowramp_sweep.csv

---

## 5. Make and view the graphs

    python3 make_plots.py        # regenerates all 6 PNGs and all 4 .cir decks

    xdg-open ecrl_vs_2lal_W1.0.png            # x-axis = transition freq 1/TPHASE
    xdg-open ecrl_vs_2lal_W1.0_fclock.png     # x-axis = power-clock freq 1/(4*TPHASE)
    xdg-open 2lal_energy_vs_ftr.png
    xdg-open ecrl_slowramp_energy_vs_ftr.png

Same data in ngspice's own plotter, your original style (needs a desktop session):

    ngspice 2lal_energy_vs_ftr.cir
    ngspice ecrl_slowramp_energy_vs_ftr.cir

---

## 6. Prove a plotted point came from a real simulation

    grep "^100 " 2lal_energy_vs_ftr.png.dat     # what gnuplot was handed
    grep "^1.0,10," 2lal_inverter_sweep.csv     # the CSV row behind it
    ngspice -b -o p.out 2LAL_inverter_multi_test.sp && grep -i "^e_c " p.out

All three must agree (2.16179e-14 J = 21.6179 fJ at W=1.0 um, TPHASE=10 ns).

---

## 7. Prove the fast model include equals the full PDK library

    cd ecrl_exp1
    sed '/^\.print tran/d' ecrl_baseline.sp > full.sp        # full .lib  (~77 s)
    sed -e '/^\.print tran/d' \
        -e 's|^\.lib ".*" tt|.include "./sky130_01v8_tt_fast.spice"|' \
        ecrl_baseline.sp > fast.sp                            # fast      (~1.5 s)
    ngspice -b -o full.out full.sp; ngspice -b -o fast.out fast.sp
    grep -i "^e_op" full.out fast.out
    grep "^1.0,10," width_sweep.csv          # your original number

All three: 1.80491e-14.

---

## 8. Reproduce the main ECRL finding

The old curve was measuring a cycle in which the DATA NEVER CHANGED.
Hold the data static in the new deck and it reproduces your old number exactly:

    cd ecrl_exp1
    sed -e 's|^VIN IN 0 PULSE.*|VIN IN 0 DC 0|' \
        -e 's/^\.param TPHASE=.*/.param TPHASE=100n/' ecrl_slowramp.sp > static.sp
    ngspice -b -o static.out static.sp
    grep -i "^e_a " static.out          # 5.3622e-15 J  == your 5.36221 fJ

Now the same deck with data alternating every cycle:

    grep "^1.0,100," ecrl_slowramp_sweep.csv    # 12.4589 fJ  (2.3x higher)

---

## 9. Useful one-liners

    grep -n "^\.param" 2LAL_inverter_multi_test.sp        # all the knobs
    grep -iE "error|could not find|Undefined" run.out     # did it actually run?

Device counts (2 FETs per transmission gate):

    grep -cE "^X.* TG *(;|$)"      2LAL_inverter_multi_test.sp   # 4  TG per BUF8P cell = 8 FETs
    grep -cE "^X[PN][0-9].* BUF8P *$" 2LAL_inverter_multi_test.sp # 12 cells (6 stages x 2 sub-chains)
    grep -cE "^XM"                 ecrl_exp1/ecrl_slowramp.sp    # 4  FETs in the whole ECRL gate

So one quad-rail 2LAL column = 2 cells = 16 FETs, against 4 for an ECRL gate.
Only stages 1-4 are metered; stage 0 drives and stage 5 loads.

If a run produces no `e_c` line, it errored - always check with the grep above
rather than assuming a blank result means zero.
