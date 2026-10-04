#!/bin/sh
# Energy-per-stage vs rail frequency for the 2LAL cells in 2LAL_inverter.sp.
# Adiabatic scaling predicts E_diss ~ RC/T * CV^2, i.e. LINEAR in frequency,
# until the transition time approaches the RC of the pass gate and the cell
# reverts to CV^2/2 non-adiabatic behaviour.
set -e
DECK=$(cd "$(dirname "$0")" && pwd)/2LAL_inverter.sp
cd "$(dirname "$DECK")"
OUT=${1:-2LAL_energy_sweep.csv}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "Frail_Hz,E_BUF4_J,E_BUF8P_J,E_NAIVE_NOT_J,E_QUADRAIL_NOT_J" > "$OUT"
for F in 1e6 2e6 5e6 1e7 2e7 5e7 1e8 2e8 5e8 1e9; do
    sed "s/^\.param Frail = .*; SWEEPVAR/.param Frail = $F   ; SWEEPVAR/" "$DECK" > "$WORK/d.sp"
    ngspice -b "$WORK/d.sp" 2>/dev/null > "$WORK/log" || true
    get() { grep -i "^$1 " "$WORK/log" | head -1 | awk '{print $3}'; }
    printf '%s,%s,%s,%s,%s\n' "$F" \
        "$(get e_buf4)" "$(get e_buf8p)" "$(get e_naive_not)" "$(get e_quadrail_not)" \
        | tee -a "$OUT"
done
echo "-> $OUT"
