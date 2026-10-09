#!/bin/bash
# ============================================================
# Can the 96 functional checks in 2LAL_inverter_ring.sp actually fail?
#
# Each mutant is the ring deck with ONE deliberate defect.  A check that
# never fails proves nothing, so every logic defect below must make at
# least one chkhi_/chklo_ measurement fail, and the unmodified deck
# (M0) must fail none.  Run at the deck's default point (W = 1 um,
# TPHASE = 10 ns).
#
# M7 is the documented limit: a resistive leak wastes energy but leaves
# the logic intact, so the logic checks are EXPECTED to pass and only
# E_C moves.  Energy problems are caught elsewhere (settling check,
# chain-end/boundary checks in CHECKS.md), not by these 96.
#
# Writes mutation_report.txt; decks and logs go to data/mutants/.
# Exit 1 if any expectation is violated.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

DECK="../2lal/2LAL_inverter_ring.sp"
DIR="data/mutants"
REPORT="mutation_report.txt"
NCHK=96
[ -e ../models/sky130-ngspice-models ] || { echo "FAIL: no PDK link -- run models/link_pdk.sh" >&2; exit 1; }
mkdir -p "$DIR"

#         name                       expect  sed program (one defect)
MUTANTS=(
  "M0_unmodified                     pass    s/^NO-SUCH-LINE//"
  "M1_stage3_T_C_outputs_swapped     fail    s/^XP3 nT3 nC3 aT4 aC4 /XP3 nT3 nC3 aC4 aT4 /"
  "M2_restore_gate_XR1_removed       fail    /^XR1 inT  outT outC L0/d"
  "M3_stage3_does_not_invert         fail    s/^XP3 nT3 nC3 aT4/XP3 aT3 aC3 aT4/;s/^XN3 aT3 aC3 nT4/XN3 nT3 nC3 nT4/"
  "M4_stage3_clocked_one_phase_late  fail    s/^\(X[PN]3 .*\) r3 r0 r1 r2 /\1 r0 r1 r2 r3 /"
  "M5_forward_C_gate_XF2_removed     fail    /^XF2 outC inT inC L3/d"
  "M6_data_seed_not_alternating      fail    s/^\.ic V(aT6)=.*/.ic V(aT6)={VDD} V(aC6)=0 V(nT6)=0 V(nC6)={VDD}/;s/^\.ic V(aT7)=.*/.ic V(aT7)=0 V(aC7)={VDD} V(nT7)={VDD} V(nC7)=0/"
  "M7_1Mohm_leak_on_node_nT5         pass    s/^CnT5 nT5 0 {CL}/CnT5 nT5 0 {CL}\nRleak nT5 0 1meg/"
)

bad=0
{
  echo "Mutation test of the $NCHK functional checks in 2lal/2LAL_inverter_ring.sp"
  echo "(verification/mutation_test_2lal.sh, W = 1 um, TPHASE = 10 ns)"
  echo
  printf "%-34s %-7s %-12s %-10s %s\n" mutant "lines" "checks fail" "E_C (fJ)" "expected / result"
} | tee "$REPORT"

for row in "${MUTANTS[@]}"; do
  read -r name expect prog <<< "$row"
  deck="$DIR/$name.sp"; log="$DIR/$name.out"
  sed "$prog" "$DECK" > "$deck"
  nchg=$(diff "$DECK" "$deck" | grep -c '^[<>]' || true)
  if [ "$name" != "M0_unmodified" ] && [ "$nchg" -eq 0 ]; then
    echo "FAIL: $name: the sed program changed nothing -- the mutant is not a mutant" >&2; exit 1
  fi
  ngspice -b -o "$log" "$deck" >/dev/null 2>&1 || { echo "FAIL: $name: ngspice exited non-zero" >&2; exit 1; }
  read -r k f < <(awk '/^chkhi_/ {k++; if ($3+0 < 1.62) f++} /^chklo_/ {k++; if ($3+0 > 0.18) f++}
                       END {print k+0, f+0}' "$log")
  [ "$k" -eq "$NCHK" ] || { echo "FAIL: $name: found $k checks in the log, expected $NCHK" >&2; exit 1; }
  ec=$(awk 'tolower($1)=="e_c" && $2=="=" {printf "%.3f", $3*1e15}' "$log")
  if [ "$expect" = pass ]; then [ "$f" -eq 0 ] && verdict="ok" || verdict="UNEXPECTED"
  else                          [ "$f" -gt 0 ] && verdict="ok (caught)" || verdict="UNEXPECTED (missed)"; fi
  case "$verdict" in UNEXPECTED*) bad=$((bad + 1));; esac
  printf "%-34s %-7s %-12s %-10s %s / %s\n" "$name" "$nchg" "$f/$k" "${ec:-n/a}" "$expect" "$verdict" | tee -a "$REPORT"
done

{
  echo
  [ "$bad" -eq 0 ] && echo "OVERALL: PASS -- every logic defect tripped the checks; the clean deck passed all $NCHK" \
                   || echo "OVERALL: FAIL -- $bad mutant(s) behaved unexpectedly"
} | tee -a "$REPORT"
[ "$bad" -eq 0 ]
