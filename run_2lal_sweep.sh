#!/bin/bash
# ============================================================
# 2LAL quad-rail inverter: width x TPHASE sweep.
#
# Same grid as ecrl_exp1/run_ecrl_slowramp_sweep.sh so the two
# families can be plotted on identical axes.
#   TPHASE = transition time (== ECRL TPHASE)
#   f_tr   = 1/TPHASE
#   energy = J per quad-rail column operation
# ============================================================
set -e
cd "$(dirname "$0")"

TEMPLATE="2LAL_inverter_multi_test.sp"
RESULTS="2lal_inverter_sweep.csv"
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT

echo "W_um,Tphase_ns,Trail_ns,f_tr_MHz,E_A_fJ,E_B_fJ,E_C_fJ" > "$RESULTS"

WIDTHS=("0.84" "1.0" "1.2" "1.5" "2.0" "3.0")
TPHASES=("1" "2" "5" "10" "20" "50" "100")

for W in "${WIDTHS[@]}"; do
  for T in "${TPHASES[@]}"; do
    sed -e "s/^\.param WN     = .*/.param WN     = ${W}/" \
        -e "s/^\.param WP     = .*/.param WP     = ${W}/" \
        -e "s/^\.param TPHASE = .*/.param TPHASE = ${T}n/" \
        "$TEMPLATE" > "$WORK/d.sp"
    ngspice -b -o "$WORK/d.out" "$WORK/d.sp" >/dev/null 2>&1 || true
    get() { grep -i "^$1 " "$WORK/d.out" | tail -1 | awk '{print $3}'; }
    EA=$(get e_a); EB=$(get e_b); EC=$(get e_c)
    if [ -z "$EA" ]; then echo "ERROR: W=$W T=$T produced no E_A"; continue; fi
    awk -v w="$W" -v t="$T" -v a="$EA" -v b="$EB" -v c="$EC" \
        'BEGIN{printf "%s,%s,%g,%g,%.6g,%.6g,%.6g\n", w,t,4*t,1000/t, a*1e15,b*1e15,c*1e15}' \
        | tee -a "$RESULTS"
  done
done
echo "-> $RESULTS"
