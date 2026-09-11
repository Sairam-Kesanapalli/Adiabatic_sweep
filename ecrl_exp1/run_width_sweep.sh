#!/bin/bash

set -e

TEMPLATE="ecrl_baseline.sp"
RESULTS="width_sweep.csv"

echo "W_um,Tphase_ns,Tclock_ns,E_J,E_fJ" > "$RESULTS"

WIDTHS=("0.84" "1.0" "1.2" "1.5" "2.0" "3.0")
TPHASES=("1" "2" "5" "10" "20" "50" "100")

for W in "${WIDTHS[@]}"; do
    for T in "${TPHASES[@]}"; do

        DECK="run_W${W}_T${T}.sp"
        LOG="run_W${W}_T${T}.out"

        # One power-clock period = 4*T
        # Measure one complete settled cycle from 4T to 8T.
        START_NS=$(awk -v t="$T" 'BEGIN {printf "%.12g", 4*t}')
        END_NS=$(awk -v t="$T" 'BEGIN {printf "%.12g", 8*t}')

        # Generate literal transistor width and TPHASE.
        sed \
            -e "s/l=0.15 w=1 m=1/l=0.15 w=${W} m=1/g" \
            -e "s/\.param TPHASE=.*/.param TPHASE=${T}n/" \
            -e "s/\.meas tran E_OP .*/.meas tran E_OP INTEG V(PCLK) FROM=${START_NS}n TO=${END_NS}n/" \
            "$TEMPLATE" > "$DECK"

        echo "Running W=${W} um, TPHASE=${T} ns"

        ngspice -b -o "$LOG" "$DECK"

        ENERGY=$(grep -i "e_op" "$LOG" |
            tail -1 |
            awk '{for(i=1;i<=NF;i++) if($i=="=") {print $(i+1); exit}}')

        if [ -z "$ENERGY" ]; then
            echo "ERROR: E_OP missing for W=${W}, TPHASE=${T}"
            continue
        fi

        EFJ=$(awk -v e="$ENERGY" 'BEGIN {printf "%.8g", e*1e15}')
        TCLOCK=$(awk -v t="$T" 'BEGIN {printf "%.8g", 4*t}')

        echo "${W},${T},${TCLOCK},${ENERGY},${EFJ}" >> "$RESULTS"

    done
done

echo
echo "========================================"
echo "WIDTH SWEEP COMPLETE"
echo "========================================"
column -t -s, "$RESULTS"
