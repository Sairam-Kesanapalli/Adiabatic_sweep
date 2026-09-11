#!/bin/bash
# ============================================================
# ECRL width x TPHASE sweep, adiabatic (slow-ramp) input.
#
# Same grid as run_width_sweep.sh, but drives ecrl_slowramp.sp and
# records the 0->1 cycle, the 1->0 cycle and their average separately,
# so switching activity can be matched against 2LAL rather than assumed.
#
# Uses sky130_01v8_tt_fast.spice (verified bit-identical to the full
# .lib tt corner at four points of this grid, ~50x faster to parse).
# ============================================================
set -e
cd "$(dirname "$0")"

TEMPLATE="ecrl_slowramp.sp"
RESULTS="ecrl_slowramp_sweep.csv"

echo "W_um,Tphase_ns,Tclock_ns,f_tr_MHz,E_A_fJ,E_B_fJ,E_C_fJ" > "$RESULTS"

WIDTHS=("0.84" "1.0" "1.2" "1.5" "2.0" "3.0")
TPHASES=("1" "2" "5" "10" "20" "50" "100")

for W in "${WIDTHS[@]}"; do
  for T in "${TPHASES[@]}"; do
    DECK="sr_W${W}_T${T}.sp"
    LOG="sr_W${W}_T${T}.out"
    sed -e "s/l=0.15 w=1 m=1/l=0.15 w=${W} m=1/g" \
        -e "s/^\.param TPHASE=.*/.param TPHASE=${T}n/" \
        "$TEMPLATE" > "$DECK"
    ngspice -b -o "$LOG" "$DECK" >/dev/null 2>&1 || true
    get() { grep -i "^$1 " "$LOG" | tail -1 | awk '{print $3}'; }
    EA=$(get e_a); EB=$(get e_b); EC=$(get e_c)
    if [ -z "$EA" ]; then echo "ERROR: W=$W T=$T produced no E_A"; continue; fi
    awk -v w="$W" -v t="$T" -v a="$EA" -v b="$EB" -v c="$EC" \
        'BEGIN{printf "%s,%s,%g,%g,%.6g,%.6g,%.6g\n", w,t,4*t,1000/t, a*1e15,b*1e15,c*1e15}' \
        | tee -a "$RESULTS"
  done
done
echo "-> $RESULTS"
