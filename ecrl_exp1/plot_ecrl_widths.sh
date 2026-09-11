#!/bin/bash

set -e

CSV="width_sweep.csv"
PLOT_DECK="ngspice_energy_plot.cir"

if [ ! -f "$CSV" ]; then
    echo "ERROR: $CSV not found."
    exit 1
fi

echo "Creating ngspice plotting deck..."

cat > "$PLOT_DECK" <<'EOF'
* ============================================================
* ECRL ENERGY vs TPHASE
* All transistor widths
*
* Data source:
*   width_sweep.csv
*
* Units:
*   TPHASE -> ns
*   ENERGY -> fJ
* ============================================================

.control

set noaskquit

* ------------------------------------------------------------
* X-axis
* ------------------------------------------------------------

let TPH = vector(7)

let TPH[0] = 1
let TPH[1] = 2
let TPH[2] = 5
let TPH[3] = 10
let TPH[4] = 20
let TPH[5] = 50
let TPH[6] = 100

EOF

# ------------------------------------------------------------
# Generate one ngspice vector for each width
# ------------------------------------------------------------

for W in 0.84 1.0 1.2 1.5 2.0 3.0
do

    case "$W" in
        0.84) NAME="E084" ;;
        1.0)  NAME="E100" ;;
        1.2)  NAME="E120" ;;
        1.5)  NAME="E150" ;;
        2.0) NAME="E200" ;;
        3.0) NAME="E300" ;;
    esac

    echo "* W = $W um" >> "$PLOT_DECK"
    echo "let $NAME = vector(7)" >> "$PLOT_DECK"

    ROW=0

    awk -F',' -v width="$W" '$1 == width {print $5}' "$CSV" |
    while read ENERGY
    do
        echo "let $NAME[$ROW] = $ENERGY" >> "$PLOT_DECK"
        ROW=$((ROW + 1))
    done

    echo "" >> "$PLOT_DECK"

done

cat >> "$PLOT_DECK" <<'EOF'

* ------------------------------------------------------------
* DISPLAY DATA
* ------------------------------------------------------------

print TPH
print E084
print E100
print E120
print E150
print E200
print E300

* ------------------------------------------------------------
* PLOT ALL WIDTHS
* ------------------------------------------------------------

plot E084 vs TPH \
     E100 vs TPH \
     E120 vs TPH \
     E150 vs TPH \
     E200 vs TPH \
     E300 vs TPH

.endc

.end
EOF

echo "Plot deck created:"
echo "  $PLOT_DECK"
echo

echo "Launching ngspice..."

ngspice "$PLOT_DECK"
