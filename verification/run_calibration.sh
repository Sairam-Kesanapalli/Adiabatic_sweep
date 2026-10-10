#!/bin/bash
# ============================================================
# Run the simulations behind check_calibration.py (~3 min):
#
#   1a  cal_cmos.sp     static CMOS through the 2LAL energy meter,
#                       CL = 0/10/25/50/100 fF at TPER = 40 and 400 ns
#   1b  convergence     the 2LAL ring and the ECRL deck at TPHASE =
#                       1/10/100 ns: as shipped, max step / 4 (ECRL
#                       10 ps -> 4 ps), and that plus reltol 1e-6
#   1c  cal_rc.sp       ideal 10 kohm / 25 fF on the rail trapezoid,
#                       TPHASE = 1/10/100 ns
#   2   ECRL split      ecrl_slowramp.sp with 0 V probes on every FET,
#                       energy per device per clock phase, TPHASE =
#                       1/10/100 ns
#       cal_tg_ron.sp   TG on-resistance at the 6 sweep widths
#       cal_pfet_rise.sp  ECRL pull-up pFET DC table
#
# Decks and logs go to data/calibration/ (not in git).  Stops at the
# first run that fails: ngspice exits non-zero, the log has an
# error/warning line, or a substitution did not land.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

DATA="data/calibration"
ECRL="../ecrl/ecrl_slowramp.sp"
LAL="../2lal/2LAL_inverter_ring.sp"
BAD='error|warning|timestep too small|singular|abort|interrupted|could not|undefined|unknown|failed'

fail() { echo "FAIL [$1]: $2   (see $DATA/$1.*)" >&2; exit 1; }
[ -e ../models/sky130-ngspice-models ] || { echo "FAIL: no PDK link -- run models/link_pdk.sh" >&2; exit 1; }
rm -rf "$DATA"; mkdir -p "$DATA"

# run TAG < deck  ->  $DATA/TAG.sp, .out   (OUTFILE in the deck -> $DATA/TAG.dat)
run() {
  local tag=$1
  sed "s|OUTFILE|$DATA/$tag.dat|" > "$DATA/$tag.sp"
  ngspice -b -o "$DATA/$tag.out" "$DATA/$tag.sp" >/dev/null 2>&1 || fail "$tag" "ngspice exited non-zero"
  if grep -qiE "$BAD" "$DATA/$tag.out"; then
    grep -iE "$BAD" "$DATA/$tag.out" | head -5 >&2; fail "$tag" "log has error/warning lines"
  fi
  echo "  $tag"
}
# require PATTERN in the deck just written, so a missed sed cannot pass silently
landed() { grep -q -- "$2" "$DATA/$1.sp" || fail "$1" "substitution did not land: $2"; }

echo "1a: static CMOS"
for T in 40n 400n; do
  for C in 0 10f 25f 50f 100f; do
    tag="cmos_CL${C}_T${T}"
    sed -e "s/^\.param CL    = .*/.param CL    = ${C}/" \
        -e "s/^\.param TPER  = .*/.param TPER  = ${T}/" cal_cmos.sp | run "$tag"
    landed "$tag" "^\.param CL    = ${C}$"; landed "$tag" "^\.param TPER  = ${T}$"
  done
done

echo "1c: ideal RC"
for T in 1n 10n 100n; do
  sed "s/^\.param TPHASE = .*/.param TPHASE = ${T}/" cal_rc.sp | run "rc_T$T"
  landed "rc_T$T" "^\.param TPHASE = ${T}$"
done

echo "1b: convergence"
for T in 1 10 100; do
  base="s/^\.param TPHASE = .*/.param TPHASE = ${T}n/"
  sed -e "$base" "$LAL" | run "conv_2lal_T${T}_base"
  sed -e "$base" -e "s|^\.param TSTEP  = .*|.param TSTEP  = 'TPHASE/2000'|" "$LAL" | run "conv_2lal_T${T}_step"
  sed -e "$base" -e "s|^\.param TSTEP  = .*|.param TSTEP  = 'TPHASE/2000'|" \
      -e "s/reltol=1e-4/reltol=1e-6/" "$LAL" | run "conv_2lal_T${T}_tight"
  landed "conv_2lal_T${T}_tight" "TPHASE/2000"; landed "conv_2lal_T${T}_tight" "reltol=1e-6"

  base="s/^\.param TPHASE=.*/.param TPHASE=${T}n/"
  sed -e "$base" "$ECRL" | run "conv_ecrl_T${T}_base"
  sed -e "$base" -e "s/^\.tran 10p /.tran 4p /" "$ECRL" | run "conv_ecrl_T${T}_step"
  sed -e "$base" -e "s/^\.tran 10p /.tran 4p /" -e "s/^\.end$/.options reltol=1e-6\n.end/" \
      "$ECRL" | run "conv_ecrl_T${T}_tight"
  landed "conv_ecrl_T${T}_tight" "^\.tran 4p "; landed "conv_ecrl_T${T}_tight" "reltol=1e-6"
done

echo "2: ECRL energy split by device and clock phase"
PSUB='(V(ps1)-V(OUTB))*I(Vsp1)+(V(ps2)-V(OUT))*I(Vsp2)'
for T in 1 10 100; do
  tag="ecrl_split_T$T"
  sed -e "s/^\.param TPHASE=.*/.param TPHASE=${T}n/" \
      -e "s/^XMP1 OUTB OUT  PHI PHI/XMP1 OUTB OUT  ps1 PHI/" \
      -e "s/^XMP2 OUT  OUTB PHI PHI/XMP2 OUT  OUTB ps2 PHI/" \
      -e "s/^XMN1 OUTB INB 0 0/XMN1 OUTB INB sn1 0/" \
      -e "s/^XMN2 OUT IN 0 0/XMN2 OUT IN sn2 0/" \
      -e 's/^\.end$//' "$ECRL" > "$DATA/$tag.tmp"
  cat >> "$DATA/$tag.tmp" <<EOF
* ---- 0 V probes on every FET; bulks stay on PHI / 0
Vsp1 PHI ps1 DC 0
Vsp2 PHI ps2 DC 0
Vsn1 sn1 0 DC 0
Vsn2 sn2 0 DC 0
* TEST A cycle [12,16]*TPHASE: wait / rise / hold / fall
.meas tran Ep_wait INTEG par('$PSUB') FROM={12*TPHASE} TO={13*TPHASE}
.meas tran Ep_rise INTEG par('$PSUB') FROM={13*TPHASE} TO={14*TPHASE}
.meas tran Ep_hold INTEG par('$PSUB') FROM={14*TPHASE} TO={15*TPHASE}
.meas tran Ep_fall INTEG par('$PSUB') FROM={15*TPHASE} TO={16*TPHASE}
.meas tran En_cyc  INTEG par('V(OUTB)*I(Vsn1)+V(OUT)*I(Vsn2)') FROM={12*TPHASE} TO={16*TPHASE}
.meas tran Ewell   INTEG par('V(PHI)*(-I(VPHI)) - V(PHI)*(I(Vsp1)+I(Vsp2))') FROM={12*TPHASE} TO={16*TPHASE}
.meas tran vres    FIND V(OUTB) AT={16*TPHASE}
.end
EOF
  run "$tag" < "$DATA/$tag.tmp"; rm -f "$DATA/$tag.tmp"
  for p in "XMP1 OUTB OUT  ps1" "XMP2 OUT  OUTB ps2" "XMN1 OUTB INB sn1" "XMN2 OUT IN sn2"; do landed "$tag" "^$p"; done
done

echo "2: DC tables"
for W in 0.84 1.0 1.2 1.5 2.0 3.0; do
  sed "s/^\.param W = .*/.param W = ${W}/" cal_tg_ron.sp | run "tg_W$W"
  landed "tg_W$W" "^\.param W = ${W}$"
done
run pfet_rise < cal_pfet_rise.sp

echo "-> $DATA/  (now run: python3 check_calibration.py)"
