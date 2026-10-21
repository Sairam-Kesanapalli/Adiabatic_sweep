#!/bin/bash
# ============================================================
# ECRL inverter (slow-ramp input): channel-length or load-capacitance sweep.
#
#   ./run_ecrl_lc_sweep.sh length   L  x TPHASE at W = 1.0 um, CL = 25 fF
#                                   -> ecrl_length_sweep.csv
#   ./run_ecrl_lc_sweep.sh cap      CL x TPHASE at W = 1.0 um, L = 0.15 um
#                                   -> ecrl_cap_sweep.csv
#   ./run_ecrl_lc_sweep.sh fast     TPHASE = 0.5 .. 1 ns at W = 1.0 um, L = 0.15 um,
#                                   CL = 25 fF -> ecrl_fast_sweep.csv  (where the
#                                   ECRL and 2LAL energy curves cross)
#
# Same deck and per-point checks as run_ecrl_slowramp_sweep.sh, with one
# difference: a point whose LOGIC fails (an output that does not reach
# the rail in time) is a result about the device, so it is written with
# status=logic_fail (or unsettled) instead of stopping the sweep.
# Everything that means the run itself is wrong still stops it, leaving
# that point's deck and log in $RUNS:
#   - a sed substitution did not land
#   - ngspice exited non-zero or its log has error/warning lines
#   - a .meas is missing or not a number
#   - the simulator used a different W or L on any of the 4 FETs
#     (read back with `show`) or a different TPHASE (chk_tphase)
#
# The fixed point W = 1.0 um, L = 0.15 um, CL = 25 fF is the anchor of
# the width sweep: both sweeps pass through it, and it must give the
# width sweep's value (checked at the end).
#
# E per operation = E per clock cycle = E per data transaction: the
# data alternates every cycle, so every cycle carries one transaction.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-}"
TEMPLATE="ecrl_slowramp.sp"
NFET=4                           # 2 cross-coupled pFETs + 2 nFETs
VDD=1.8
BAD='error|warning|timestep too small|singular|abort|interrupted|could not|undefined|unknown|failed'

W="1.0"
TPHASES=("1" "2" "5" "10" "20" "50" "100")
case "$MODE" in
  length) VALUES=("0.15" "0.18" "0.25" "0.35" "0.5" "0.75" "1.0" "1.5" "2.0"); CL="25" ;;
  cap)    VALUES=("5" "10" "25" "50" "100" "200");                             L="0.15" ;;
  fast)   VALUES=("25"); L="0.15"; TPHASES=("0.5" "0.6" "0.65" "0.7" "0.8" "0.9" "1") ;;
  *) echo "usage: $0 length|cap|fast" >&2; exit 2 ;;
esac
RESULTS="ecrl_${MODE}_sweep.csv"
RUNS="runs_ecrl_${MODE}"

fail() { echo "FAIL [$1]: $2   (see $RUNS/$1.*)" >&2; exit 1; }

# value of one .meas: must appear exactly once and be a number
meas() {
  awk -v n="$2" 'tolower($1)==n && $2=="=" {v=$3; c++}
    END {if (c!=1 || v !~ /^[-+]?[0-9.]+([eE][-+]?[0-9]+)?$/) exit 1; print v}' "$1"
}

rm -rf "$RUNS"; mkdir -p "$RUNS"
echo "W_um,L_um,CL_fF,Tphase_ns,Tclock_ns,f_tr_MHz,E_A_fJ,E_B_fJ,E_C_fJ,status" > "$RESULTS"

for V in "${VALUES[@]}"; do
  [ "$MODE" = length ] && L="$V" || CL="$V"
  for T in "${TPHASES[@]}"; do
    tag="L${L}_CL${CL}_T${T}"; deck="$RUNS/$tag.sp"; log="$RUNS/$tag.out"

    sed -e "s/l=0.15 w=1 m=1/l=${L} w=${W} m=1/g" \
        -e "s/^\.param CL=.*/.param CL=${CL}f/" \
        -e "s/^\.param TPHASE=.*/.param TPHASE=${T}n/" \
        "$TEMPLATE" > "$deck"
    [ "$(grep -c "l=${L} w=${W} m=1" "$deck")" -eq "$NFET" ] || fail "$tag" "W/L not substituted on all $NFET FETs"
    grep -q "^\.param CL=${CL}f$"     "$deck" || fail "$tag" "CL not substituted"
    grep -q "^\.param TPHASE=${T}n$"  "$deck" || fail "$tag" "TPHASE not substituted"

    ngspice -b -o "$log" "$deck" >/dev/null 2>&1 || fail "$tag" "ngspice exited non-zero"
    if grep -qiE "$BAD" "$log"; then
      grep -iE "$BAD" "$log" | head -5 >&2; fail "$tag" "log has error/warning lines"
    fi

    EA=$(meas "$log" e_a) || fail "$tag" "e_a missing or not a number"
    EB=$(meas "$log" e_b) || fail "$tag" "e_b missing or not a number"
    EC=$(meas "$log" e_c) || fail "$tag" "e_c missing or not a number"
    EA0=$(meas "$log" e_a0) || fail "$tag" "e_a0 missing or not a number"
    EB0=$(meas "$log" e_b0) || fail "$tag" "e_b0 missing or not a number"
    CT=$(meas "$log" chk_tphase) || fail "$tag" "chk_tphase missing"
    awk -v c="$CT" -v t="$T" 'BEGIN{e=1.5*t*1e-9; exit !((c-e)^2 < (1e-4*e)^2)}' \
      || fail "$tag" "simulator TPHASE: chk_tphase=$CT, expected $(awk -v t="$T" 'BEGIN{print 1.5*t}')n"
    OA=$(meas "$log" out_a)   || fail "$tag" "out_a missing or not a number"
    OBA=$(meas "$log" outb_a) || fail "$tag" "outb_a missing or not a number"
    OB=$(meas "$log" out_b)   || fail "$tag" "out_b missing or not a number"
    OBB=$(meas "$log" outb_b) || fail "$tag" "outb_b missing or not a number"

    # Read W and L back from the simulator itself: operating point + `show`.
    sed 's/^\.end$//' "$deck" > "$RUNS/$tag.w.sp"
    printf '.control\nop\nshow m : w l\nquit\n.endc\n.end\n' >> "$RUNS/$tag.w.sp"
    ngspice -b "$RUNS/$tag.w.sp" > "$RUNS/$tag.w.out" 2>&1 || fail "$tag" "W/L read-back run failed"
    awk -v w="$W" -v l="$L" -v n="$NFET" '$1=="device"{m=NF-1; for(i=2;i<=NF;i++) name[i]=$i}
      $1=="w"{for(i=2;i<=m+1;i++) wv[name[i]]=$i}
      $1=="l"{for(i=2;i<=m+1;i++) lv[name[i]]=$i}
      END{for(d in wv){k++; if((wv[d]-w*1e-6)^2>(1e-9*w*1e-6)^2 || (lv[d]-l*1e-6)^2>(1e-9*l*1e-6)^2) bad++}
          if (k!=n || bad) {printf "FETs=%d mismatched=%d\n", k, bad; exit 1}}' \
      "$RUNS/$tag.w.out" >&2 || fail "$tag" "simulator W/L differ from ${W}/${L} um (expected $NFET FETs)"

    # Logic (sampled mid-hold, IN=1 in cycle A, IN=0 in B), then settling
    # (the same two cycles two clock periods earlier).  Recorded, not fatal.
    status=ok
    awk -v v="$VDD" -v oa="$OA" -v oba="$OBA" -v ob="$OB" -v obb="$OBB" \
        'BEGIN{exit !(oa < 0.1*v && oba > 0.9*v && ob > 0.9*v && obb < 0.1*v)}' || status=logic_fail
    if [ "$status" = ok ]; then
      awk -v a="$EA" -v b="$EB" -v a0="$EA0" -v b0="$EB0" \
          'BEGIN{exit !((a0-a)^2 < (0.01*a)^2 && (b0-b)^2 < (0.01*b)^2)}' || status=unsettled
    fi

    awk -v w="$W" -v l="$L" -v cl="$CL" -v t="$T" -v a="$EA" -v b="$EB" -v c="$EC" -v s="$status" \
        'BEGIN{printf "%s,%s,%s,%s,%g,%g,%.6g,%.6g,%.6g,%s\n", w,l,cl,t,4*t,1000/t, a*1e15,b*1e15,c*1e15,s}' \
        | tee -a "$RESULTS"
  done
done

rows=$(( $(wc -l < "$RESULTS") - 1 ))
[ "$rows" -eq $(( ${#VALUES[@]} * ${#TPHASES[@]} )) ] || { echo "FAIL: $rows rows written" >&2; exit 1; }

# Anchor: W = 1.0, L = 0.15, CL = 25 fF must reproduce the width sweep at
# every TPHASE the width sweep also ran (the fast mode shares only 1 ns).
anchors=0
for T in "${TPHASES[@]}"; do
  a=$(awk -F, -v t="$T" '$1=="1.0" && $2=="0.15" && $3=="25" && $4==t {print $9}' "$RESULTS")
  b=$(awk -F, -v t="$T" '$1=="1.0" && $2==t {print $7}' ecrl_slowramp_sweep.csv)
  [ -z "$b" ] && continue
  anchors=$((anchors + 1))
  awk -v a="$a" -v b="$b" 'BEGIN{exit !(a!="" && b!="" && (a-b)^2 < (1e-4*b)^2)}' \
    || { echo "FAIL: anchor TPHASE=$T: $a fJ here, $b fJ in ecrl_slowramp_sweep.csv" >&2; exit 1; }
done
[ "$anchors" -ge 1 ] || { echo "FAIL: no TPHASE shared with the width sweep to anchor on" >&2; exit 1; }
nbad=$(awk -F, 'NR>1 && $10!="ok"' "$RESULTS" | wc -l)
echo "-> $RESULTS  ($rows points, $nbad not ok, anchor matches the width sweep; decks and logs in $RUNS/)"
