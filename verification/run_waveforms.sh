#!/bin/bash
# ============================================================
# Dump the inverter waveforms that check_waveforms.py decodes.
#
# Runs the two decks in use with a wrdata block appended, so every
# node can be read back.  Nothing else in the circuit changes.  Only
# TPHASE varies, plus two 2LAL stress runs:
#   ecrl_T{1,10,100}.dat    PHI, IN, OUT, OUTB
#   2lal_T{1,10,100}.dat    p0..p3 and aT/aC/nT/nC of all 8 ring nodes
#   2lal_const_T10.dat      constant data: wave 1 seeded with the same
#                           polarity as wave 0, so every node should HOLD
#                           its value instead of alternating
#   2lal_long_T100.dat      20 rail periods at TPHASE = 100 ns (slowest
#                           sweep point), to see whether the data
#                           leaks away; TSTEP relaxed to TPHASE/200
# Output, decks and logs go to data/ (not in git, ~100 MB).
#
# Stops at the first run that fails: ngspice exits non-zero, the log
# has an error/warning line, or no waveform is written.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

DATA="data"
ECRL="../ecrl/ecrl_slowramp.sp"
LAL="../2lal/2LAL_inverter_ring.sp"
BAD='error|warning|timestep too small|singular|abort|interrupted|could not|undefined|unknown|failed'

fail() { echo "FAIL [$1]: $2   (see $DATA/$1.*)" >&2; exit 1; }
[ -e ../models/sky130-ngspice-models ] || { echo "FAIL: no PDK link -- run models/link_pdk.sh" >&2; exit 1; }
mkdir -p "$DATA"

# run TAG VECTORS < deck  ->  $DATA/TAG.sp, .out, .dat
run() {
  local tag=$1 vecs=$2
  sed "s|^\.end\$|.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata $DATA/$tag.dat $vecs\nquit\n.endc\n.end|" \
    > "$DATA/$tag.sp"
  grep -q "^wrdata " "$DATA/$tag.sp" || fail "$tag" "could not append the wrdata block"
  rm -f "$DATA/$tag.dat"
  ngspice -b -o "$DATA/$tag.out" "$DATA/$tag.sp" >/dev/null 2>&1 || fail "$tag" "ngspice exited non-zero"
  if grep -qiE "$BAD" "$DATA/$tag.out"; then
    grep -iE "$BAD" "$DATA/$tag.out" | head -5 >&2; fail "$tag" "log has error/warning lines"
  fi
  [ -s "$DATA/$tag.dat" ] || fail "$tag" "no waveform written"
  echo "  $DATA/$tag.dat   $(( $(wc -l < "$DATA/$tag.dat") - 1 )) time points"
}

V2LAL="v(p0) v(p1) v(p2) v(p3)"
for m in 0 1 2 3 4 5 6 7; do V2LAL="$V2LAL v(aT$m) v(aC$m) v(nT$m) v(nC$m)"; done

for T in 1 10 100; do
  sed "s/^\.param TPHASE=.*/.param TPHASE=${T}n/" "$ECRL" | run "ecrl_T$T" "v(phi) v(in) v(out) v(outb)"
  sed "s/^\.param TPHASE = .*/.param TPHASE = ${T}n/" "$LAL" | run "2lal_T$T" "$V2LAL"
done

sed -e 's/^\.ic V(aT6)=.*/.ic V(aT6)={VDD} V(aC6)=0 V(nT6)=0 V(nC6)={VDD}   ; wave 1, TRUE on a (was n)/' \
    -e 's/^\.ic V(aT7)=.*/.ic V(aT7)=0 V(aC7)={VDD} V(nT7)={VDD} V(nC7)=0   ; wave 1, TRUE on n (was a)/' \
    "$LAL" | run "2lal_const_T10" "$V2LAL"

sed -e "s/^\.param TPHASE = .*/.param TPHASE = 100n/" \
    -e "s/^\.param TSTEP .*/.param TSTEP  = 'TPHASE\/200'/" \
    -e "s/^\.param TSTOP .*/.param TSTOP  = '20*TRAIL+TPHASE'/" \
    "$LAL" | run "2lal_long_T100" "$V2LAL"

echo "-> $DATA/  (now run: python3 check_waveforms.py)"
