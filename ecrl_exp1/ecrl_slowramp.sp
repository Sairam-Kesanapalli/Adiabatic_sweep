* ============================================================
* ECRL INVERTER - SKY130 - v2, ADIABATIC (SLOW-RAMP) INPUT
* ============================================================
* Same circuit as ecrl_baseline.sp.  Two things changed:
*
* 1. THE INPUT NO LONGER STEPS.
*    Baseline used TIN=100p regardless of TPHASE, so at TPHASE=100ns
*    the input edge was 1000x faster than the power clock -- the gate
*    saw a hard step, which is exactly what adiabatic operation is
*    supposed to avoid.  Here the input ramps over a FULL phase and
*    does so only while PHI sits in its wait window, so the gate never
*    sees a moving input during evaluate, at any TPHASE.
*
* 2. THE DATA ALTERNATES 1,0,1,0 EVERY CLOCK CYCLE,
*    and energy is measured separately for the 0->1 cycle and the
*    1->0 cycle so the switching activity can be matched against 2LAL
*    instead of assumed.
*
* PHI:  wait -> rise -> hold -> fall, TPHASE each.  Tclock = 4*TPHASE.
* Cycle k spans [4k*TPHASE, 4(k+1)*TPHASE].
*
* Timeline (units of TPHASE):
*   cycle 0  [ 0, 4]  settle, IN=0
*   cycle 1  [ 4, 8]  IN ramps 0->1 in the wait window [4,5]
*   cycle 2  [ 8,12]  IN ramps 1->0 in the wait window [8,9]
*   cycle 3  [12,16]  IN ramps 0->1   <- TEST A measured here
*   cycle 4  [16,20]  IN ramps 1->0   <- TEST B measured here
* ============================================================

.include "./sky130_01v8_tt_fast.spice"

* ------------------------------------------------------------
* PARAMETERS
* ------------------------------------------------------------
.param VDD=1.8
.param CL=25f
.param TPHASE=10n

* ------------------------------------------------------------
* POWER CLOCK
* ------------------------------------------------------------
VPHI PHI 0 PULSE(0 {VDD} {TPHASE} {TPHASE} {TPHASE} {TPHASE} {4*TPHASE})

* Instantaneous power delivered by the power clock.
* ngspice source current is defined into the positive terminal,
* so power delivered to the circuit is -V*I.
BPCPOWER PCLK 0 V={-V(PHI)*I(VPHI)}

* ------------------------------------------------------------
* INPUT - ramps over one full phase, inside PHI's wait window
* ------------------------------------------------------------
VIN IN 0 PULSE(0 {VDD} {4*TPHASE} {TPHASE} {TPHASE} {3*TPHASE} {8*TPHASE})
B_INB INB 0 V={VDD-V(IN)}

* ------------------------------------------------------------
* ECRL INVERTER
* ------------------------------------------------------------
XMP1 OUTB OUT  PHI PHI sky130_fd_pr__pfet_01v8 l=0.15 w=1 m=1
XMP2 OUT  OUTB PHI PHI sky130_fd_pr__pfet_01v8 l=0.15 w=1 m=1

XMN1 OUTB INB 0 0 sky130_fd_pr__nfet_01v8 l=0.15 w=1 m=1
XMN2 OUT IN 0 0 sky130_fd_pr__nfet_01v8 l=0.15 w=1 m=1

CLOAD_OUT  OUT  0 {CL}
CLOAD_OUTB OUTB 0 {CL}

* ============================================================
* TRANSIENT ANALYSIS
* ============================================================
.tran 10p {20*TPHASE}

* -------- energy per operation ------------------------------
* TEST A: the clock cycle in which the data went 0 -> 1
.meas tran E_A INTEG V(PCLK) FROM={12*TPHASE} TO={16*TPHASE}
* TEST B: the clock cycle in which the data went 1 -> 0
.meas tran E_B INTEG V(PCLK) FROM={16*TPHASE} TO={20*TPHASE}
* TEST C: average over the alternating pattern
.meas tran E_C PARAM='(E_A+E_B)/2'

* -------- settling check ------------------------------------
* Same two cycles, two clock periods earlier.  If the circuit has
* settled these match E_A / E_B.
.meas tran E_A0 INTEG V(PCLK) FROM={4*TPHASE} TO={8*TPHASE}
.meas tran E_B0 INTEG V(PCLK) FROM={8*TPHASE} TO={12*TPHASE}

* -------- functional check ----------------------------------
* Sampled mid-hold.  IN=1 -> OUT clamped low, OUTB pulses high.
.meas tran OUT_A  FIND V(OUT)  AT={14.5*TPHASE}
.meas tran OUTB_A FIND V(OUTB) AT={14.5*TPHASE}
.meas tran OUT_B  FIND V(OUT)  AT={18.5*TPHASE}
.meas tran OUTB_B FIND V(OUTB) AT={18.5*TPHASE}

.end
