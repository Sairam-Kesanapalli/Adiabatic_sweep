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
#
# Every point is checked before its row is written.  Any failure
# stops the sweep and leaves that point's deck and log in $RUNS:
#   - the sed substitutions actually landed in the deck
#   - ngspice exited 0 and its log has no error/warning lines
#   - every .meas it needs appears exactly once, as a number
#   - the simulator used the requested W on every FET (read back
#     with `show`) and the requested TPHASE (chk_tphase = 1.5*TPHASE)
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

TEMPLATE="ecrl_slowramp.sp"
RESULTS="ecrl_slowramp_sweep.csv"
RUNS="runs_ecrl_slowramp"        # every deck and log is kept here
NFET=4                           # 2 cross-coupled pFETs + 2 nFETs
BAD='error|warning|timestep too small|singular|abort|interrupted|could not|undefined|unknown|failed'

WIDTHS=("0.84" "1.0" "1.2" "1.5" "2.0" "3.0")
TPHASES=("1" "2" "5" "10" "20" "50" "100")

fail() { echo "FAIL [$1]: $2   (see $RUNS/$1.*)" >&2; exit 1; }

# value of one .meas: must appear exactly once and be a number
meas() {
  awk -v n="$2" 'tolower($1)==n && $2=="=" {v=$3; c++}
    END {if (c!=1 || v !~ /^[-+]?[0-9.]+([eE][-+]?[0-9]+)?$/) exit 1; print v}' "$1"
}

rm -rf "$RUNS"; mkdir -p "$RUNS"
echo "W_um,Tphase_ns,Tclock_ns,f_tr_MHz,E_A_fJ,E_B_fJ,E_C_fJ" > "$RESULTS"

for W in "${WIDTHS[@]}"; do
  for T in "${TPHASES[@]}"; do
    tag="W${W}_T${T}"; deck="$RUNS/$tag.sp"; log="$RUNS/$tag.out"

    sed -e "s/l=0.15 w=1 m=1/l=0.15 w=${W} m=1/g" \
        -e "s/^\.param TPHASE=.*/.param TPHASE=${T}n/" \
        "$TEMPLATE" > "$deck"
    [ "$(grep -c "l=0.15 w=${W} m=1" "$deck")" -eq "$NFET" ] || fail "$tag" "W not substituted on all $NFET FETs"
    grep -q "^\.param TPHASE=${T}n$" "$deck" || fail "$tag" "TPHASE not substituted"

    ngspice -b -o "$log" "$deck" >/dev/null 2>&1 || fail "$tag" "ngspice exited non-zero"
    if grep -qiE "$BAD" "$log"; then
      grep -iE "$BAD" "$log" | head -5 >&2; fail "$tag" "log has error/warning lines"
    fi

    EA=$(meas "$log" e_a) || fail "$tag" "e_a missing or not a number"
    EB=$(meas "$log" e_b) || fail "$tag" "e_b missing or not a number"
    EC=$(meas "$log" e_c) || fail "$tag" "e_c missing or not a number"
    CT=$(meas "$log" chk_tphase) || fail "$tag" "chk_tphase missing"
    awk -v c="$CT" -v t="$T" 'BEGIN{e=1.5*t*1e-9; exit !((c-e)^2 < (1e-4*e)^2)}' \
      || fail "$tag" "simulator TPHASE: chk_tphase=$CT, expected $(awk -v t="$T" 'BEGIN{print 1.5*t}')n"

    # Read W back from the simulator itself: operating point + `show`.
    sed 's/^\.end$//' "$deck" > "$RUNS/$tag.w.sp"
    printf '.control\nop\nshow m : w\nquit\n.endc\n.end\n' >> "$RUNS/$tag.w.sp"
    ngspice -b "$RUNS/$tag.w.sp" > "$RUNS/$tag.w.out" 2>&1 || fail "$tag" "W read-back run failed"
    # `show` prints devices in columns: a `device` row of names, then a `w`
    # row of values.  Pair them by column and key on the device name.
    awk -v w="$W" -v n="$NFET" '$1=="device"{m=NF-1; for(i=2;i<=NF;i++) name[i]=$i}
      $1=="w"{for(i=2;i<=m+1;i++) val[name[i]]=$i}
      END{for(d in val){k++; if((val[d]-w*1e-6)^2>(1e-9*w*1e-6)^2) bad++}
          if (k!=n || bad) {printf "FETs=%d mismatched=%d\n", k, bad; exit 1}}' \
      "$RUNS/$tag.w.out" >&2 || fail "$tag" "simulator W differs from ${W} um (expected $NFET FETs)"

    awk -v w="$W" -v t="$T" -v a="$EA" -v b="$EB" -v c="$EC" \
        'BEGIN{printf "%s,%s,%g,%g,%.6g,%.6g,%.6g\n", w,t,4*t,1000/t, a*1e15,b*1e15,c*1e15}' \
        | tee -a "$RESULTS"
  done
done

rows=$(( $(wc -l < "$RESULTS") - 1 ))
[ "$rows" -eq $(( ${#WIDTHS[@]} * ${#TPHASES[@]} )) ] || { echo "FAIL: $rows rows written" >&2; exit 1; }
echo "-> $RESULTS  ($rows points, all checks passed; decks and logs in $RUNS/)"
