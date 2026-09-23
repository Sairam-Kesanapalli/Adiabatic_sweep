* ==========================================================================
* 2LAL QUAD-RAIL INVERTER -- MULTI-TEST DECK
* sky130 / ngspice.  Companion to ecrl_exp1/ecrl_slowramp.sp.
* --------------------------------------------------------------------------
* Derived from 2LAL_inverter.sp, reduced to the INVERTER only (the buffer,
* the 4-FET cell and the naive rail-crossing chains are dropped) and
* re-parameterised so its axes line up 1:1 with the ECRL experiment:
*
*     2LAL                       ECRL
*     TPHASE = transition time = TPHASE
*     TRAIL  = 4*TPHASE        = Tclock = 4*TPHASE
*     f_tr   = 1/TPHASE        = 1/TPHASE
*     WN=WP, L=0.15 um         = WNMOS=WPMOS, L=0.15 um
*     CL per dual-rail node    = CL on OUT and OUTB
*
* WHAT AN 'OPERATION' IS HERE
*   A 2LAL inverter needs QUAD-RAIL data: two dual-rail chains, one
*   carrying A and one carrying NOT A, with the chains exchanged between
*   stages.  The exchange is the inverter and costs zero transistors.
*   One quad-rail COLUMN = the P-stage plus the N-stage at the same index
*   = 16 FETs, and delivers one inverted bit (with its complement) per
*   TRAIL.  Four columns are metered, so over N rail periods there are
*   4*N operations.  That is the denominator used below.
*
*   Activity is data-independent: for ANY bit value exactly one of the two
*   sub-chains carries a TRUE and therefore pulses, so a column always
*   switches exactly once per period -- just like an ECRL gate, whose
*   OUT or OUTB pulses every cycle.  TEST A vs TEST B below measures this
*   rather than assuming it: they should come out equal.
*
* SIGNAL ENCODING
*   A dual-rail pair (T,C) RESTS at FALSE = (0, VDD).  A TRUE is T pulsing
*   up on phi_t while C is pulled down by the antiphase rail phi_t+2.  A
*   FALSE is the absence of a pulse.  Encoding a 0 as a pulse on C instead
*   makes the pass gate's pFET conduct while phi_t is still high and every
*   stage latches a spurious 1 -- silently, because the 1s still look fine.
* ==========================================================================

.include "./sky130_01v8_tt_fast.spice"

* ---------------------------------------------------------------- parameters
.param VDD    = 1.8
.param WN     = 1.0         ; nFET width, MICRONS   ; SWEEPVAR
.param WP     = 1.0         ; pFET width, MICRONS   ; SWEEPVAR
.param L      = 0.15        ; channel length, MICRONS
.param CL     = 25f         ; load per dual-rail node (matches ECRL's CL)

.param TPHASE = 10n                                 ; SWEEPVAR
.param TRAIL  = '4*TPHASE'  ; one full trapezoid    (== ECRL Tclock)
.param TSTEP  = 'TPHASE/500'
.param TSTOP  = '8*TRAIL'

* measurement windows, in rail periods:
*   period 4 carries data bit 0 -> TEST B (1->0)
*   period 5 carries data bit 1 -> TEST A (0->1)
.param TM0 = '4*TRAIL'
.param TM1 = '5*TRAIL'
.param TM2 = '6*TRAIL'

.options reltol=1e-4 abstol=1e-13 vntol=1e-7 chgtol=1e-16 gmin=1e-14
.options method=gear maxord=2

Vnb vnb 0 DC 0
Vpb vpb 0 DC {VDD}

* ---------------------------------------------------------------- power clocks
* rise / flat-high / fall / flat-low of one TPHASE each: 50% duty at the
* midpoint, 25% transition time -- Fig. 1 of the 2LAL paper.
Vp0 p0 0 PULSE(0 {VDD} 0            {TPHASE} {TPHASE} {TPHASE} {TRAIL})
Vp1 p1 0 PULSE(0 {VDD} {TPHASE}     {TPHASE} {TPHASE} {TPHASE} {TRAIL})
Vp2 p2 0 PULSE(0 {VDD} {2*TPHASE}   {TPHASE} {TPHASE} {TPHASE} {TRAIL})
Vp3 p3 0 PULSE(0 {VDD} {3*TPHASE}   {TPHASE} {TPHASE} {TPHASE} {TRAIL})

* ---------------------------------------------------------------- input drive
* Quad-rail source: (aT0,aC0) carries A, (nT0,nC0) carries NOT A.
* TRUE = (phi0, phi2) ; FALSE = (0, VDD) held.  Data alternates 1,0 every
* rail period; dctl toggles 3.5 TPHASE in, inside phi0's dead window, so the
* encoded rails never change while a pulse is live.
Vdctl dctl 0 PULSE(0 {VDD} {3.5*TPHASE} 1p 1p {TRAIL} {2*TRAIL})
BaT aT0 0 V = (V(dctl) > {VDD/2}) ? V(p0) : 0
BaC aC0 0 V = (V(dctl) > {VDD/2}) ? V(p2) : {VDD}
BnT nT0 0 V = (V(dctl) > {VDD/2}) ? 0     : V(p0)
BnC nC0 0 V = (V(dctl) > {VDD/2}) ? {VDD} : V(p2)

* ==========================================================================
* CELLS
* ==========================================================================
* Transmission gate: conducts s->d when the dual-rail control (gn,gp) is TRUE.
.subckt TG d gn gp s vnb vpb
xN d gn s vnb sky130_fd_pr__nfet_01v8 w={WN} l={L}
+ as='WN*L*1.77' ad='WN*L*1.77' ps='(WN+L)*2.4' pd='(WN+L)*2.4'
xP d gp s vpb sky130_fd_pr__pfet_01v8 w={WP} l={L}
+ as='WP*L*1.77' ad='WP*L*1.77' ps='(WP+L)*2.4' pd='(WP+L)*2.4'
.ends TG

* The 2LAL delay element (Fig 2c / 4lc PHAS2), 8 FETs:
*   forward pair drives the output from phi_t and its antiphase phi_t+2;
*   reverse pair restores the PREVIOUS stage's node from phi_t-1 / phi_t+1
*   once this stage's output is valid.  The reverse pair is what recovers
*   the charge the forward pair cannot, and is why 2LAL is adiabatic.
.subckt BUF8P inT inC outT outC L0 L1 L2 L3 vnb vpb
XF1 outT inT inC L1 vnb vpb TG          ; TRUE -> outT pulses on phi_t
XF2 outC inT inC L3 vnb vpb TG          ; TRUE -> outC pulled down by phi_t+2
XR1 inT  outT outC L0 vnb vpb TG        ; restore inT via phi_t-1
XR2 inC  outT outC L2 vnb vpb TG        ; restore inC via phi_t+1
.ends BUF8P

* ==========================================================================
* QUAD-RAIL INVERTER CHAIN
* ==========================================================================
* Stage n is clocked by phi_n (one tick advance per stage).
* Sub-chain A nodes are aT<m>/aC<m>, sub-chain NOT-A nodes are nT<m>/nC<m>.
* EVERY stage takes its input from the OPPOSITE sub-chain -- that crossing
* is the inversion.  So aT1 = NOT A, aT2 = A, aT3 = NOT A, aT4 = A.
* Stage 0 drives and stage 5 loads; stages 1..4 are metered.

* -------- rail ammeters (0 V sources used as current probes) ---------------
Vm0 p0 r0 DC 0
Vm1 p1 r1 DC 0
Vm2 p2 r2 DC 0
Vm3 p3 r3 DC 0

* stage 0  (phi1)  driver
XP0 nT0   nC0   aT1   aC1   p0  p1  p2  p3  vnb vpb BUF8P
XN0 aT0   aC0   nT1   nC1   p0  p1  p2  p3  vnb vpb BUF8P
* stage 1  (phi2)  metered
XP1 nT1   nC1   aT2   aC2   r1  r2  r3  r0  vnb vpb BUF8P
XN1 aT1   aC1   nT2   nC2   r1  r2  r3  r0  vnb vpb BUF8P
* stage 2  (phi3)  metered
XP2 nT2   nC2   aT3   aC3   r2  r3  r0  r1  vnb vpb BUF8P
XN2 aT2   aC2   nT3   nC3   r2  r3  r0  r1  vnb vpb BUF8P
* stage 3  (phi0)  metered
XP3 nT3   nC3   aT4   aC4   r3  r0  r1  r2  vnb vpb BUF8P
XN3 aT3   aC3   nT4   nC4   r3  r0  r1  r2  vnb vpb BUF8P
* stage 4  (phi1)  metered
XP4 nT4   nC4   aT5   aC5   r0  r1  r2  r3  vnb vpb BUF8P
XN4 aT4   aC4   nT5   nC5   r0  r1  r2  r3  vnb vpb BUF8P
* stage 5  (phi2)  load
XP5 nT5   nC5   aT6   aC6   p1  p2  p3  p0  vnb vpb BUF8P
XN5 aT5   aC5   nT6   nC6   p1  p2  p3  p0  vnb vpb BUF8P

* ---------------------------------------------------------------- node loads
CaT1 aT1 0 {CL}
CaC1 aC1 0 {CL}
CnT1 nT1 0 {CL}
CnC1 nC1 0 {CL}
CaT2 aT2 0 {CL}
CaC2 aC2 0 {CL}
CnT2 nT2 0 {CL}
CnC2 nC2 0 {CL}
CaT3 aT3 0 {CL}
CaC3 aC3 0 {CL}
CnT3 nT3 0 {CL}
CnC3 nC3 0 {CL}
CaT4 aT4 0 {CL}
CaC4 aC4 0 {CL}
CnT4 nT4 0 {CL}
CnC4 nC4 0 {CL}
CaT5 aT5 0 {CL}
CaC5 aC5 0 {CL}
CnT5 nT5 0 {CL}
CnC5 nC5 0 {CL}

* ==========================================================================
* ENERGY INTEGRATOR
* ==========================================================================
* A behavioural current source pushing P(t) into a 1 F capacitor makes V(e)
* the running integral of power, so the node reads directly in JOULES.
Be 0 e I = V(r0)*I(Vm0) + V(r1)*I(Vm1) + V(r2)*I(Vm2) + V(r3)*I(Vm3)
Ce e 0 1
Re e 0 1e15

* ---------------------------------------------------------------- rest state
* Every dual-rail node starts at FALSE = (0, VDD).  Starting them all at 0
* instead injects a spurious first bit.
.ic V(e)=0
.ic V(aT1)=0 V(aC1)={VDD} V(nT1)=0 V(nC1)={VDD}
.ic V(aT2)=0 V(aC2)={VDD} V(nT2)=0 V(nC2)={VDD}
.ic V(aT3)=0 V(aC3)={VDD} V(nT3)=0 V(nC3)={VDD}
.ic V(aT4)=0 V(aC4)={VDD} V(nT4)=0 V(nC4)={VDD}
.ic V(aT5)=0 V(aC5)={VDD} V(nT5)=0 V(nC5)={VDD}
.ic V(aT6)=0 V(aC6)={VDD} V(nT6)=0 V(nC6)={VDD}

.tran {TSTEP} {TSTOP} uic

* ==========================================================================
* FUNCTIONAL CHECKS
* ==========================================================================
* Node m rides phi_m, so it plateaus during tick m+1: sample (m+1.5)*TPHASE
* into the rail period.  Nodes 3 and 4 therefore sample into the FOLLOWING
* period -- that is correct, the bit has simply advanced that far.
* Expected, for input bit b:  aT1=NOT b, aT2=b, aT3=NOT b, aT4=b
*   TRUE -> (T,C) = (1.8, 0)        FALSE -> (T,C) = (0, 1.8)
.param tb0_n1 = '4*TRAIL + 2.5*TPHASE'
.param tb0_n2 = '4*TRAIL + 3.5*TPHASE'
.param tb0_n3 = '4*TRAIL + 4.5*TPHASE'
.param tb0_n4 = '4*TRAIL + 5.5*TPHASE'
.param tb1_n1 = '5*TRAIL + 2.5*TPHASE'
.param tb1_n2 = '5*TRAIL + 3.5*TPHASE'
.param tb1_n3 = '5*TRAIL + 4.5*TPHASE'
.param tb1_n4 = '5*TRAIL + 5.5*TPHASE'

.meas tran a1_b0_T FIND V(aT1) AT={tb0_n1}
.meas tran a1_b0_C FIND V(aC1) AT={tb0_n1}
.meas tran a2_b0_T FIND V(aT2) AT={tb0_n2}
.meas tran a2_b0_C FIND V(aC2) AT={tb0_n2}
.meas tran a3_b0_T FIND V(aT3) AT={tb0_n3}
.meas tran a3_b0_C FIND V(aC3) AT={tb0_n3}
.meas tran a4_b0_T FIND V(aT4) AT={tb0_n4}
.meas tran a4_b0_C FIND V(aC4) AT={tb0_n4}
.meas tran a1_b1_T FIND V(aT1) AT={tb1_n1}
.meas tran a1_b1_C FIND V(aC1) AT={tb1_n1}
.meas tran a2_b1_T FIND V(aT2) AT={tb1_n2}
.meas tran a2_b1_C FIND V(aC2) AT={tb1_n2}
.meas tran a3_b1_T FIND V(aT3) AT={tb1_n3}
.meas tran a3_b1_C FIND V(aC3) AT={tb1_n3}
.meas tran a4_b1_T FIND V(aT4) AT={tb1_n4}
.meas tran a4_b1_C FIND V(aC4) AT={tb1_n4}
.meas tran n1_b0_T FIND V(nT1) AT={tb0_n1}
.meas tran n1_b0_C FIND V(nC1) AT={tb0_n1}
.meas tran n2_b0_T FIND V(nT2) AT={tb0_n2}
.meas tran n2_b0_C FIND V(nC2) AT={tb0_n2}
.meas tran n1_b1_T FIND V(nT1) AT={tb1_n1}
.meas tran n1_b1_C FIND V(nC1) AT={tb1_n1}
.meas tran n2_b1_T FIND V(nT2) AT={tb1_n2}
.meas tran n2_b1_C FIND V(nC2) AT={tb1_n2}

* ==========================================================================
* ENERGY -- 4 metered quad-rail columns, one operation each per rail period
* ==========================================================================
.meas tran e0 FIND V(e) AT={TM0}
.meas tran e1 FIND V(e) AT={TM1}
.meas tran e2 FIND V(e) AT={TM2}
* TEST B: the rail period carrying data bit 0   (4 operations)
.meas tran E_B PARAM='(e1-e0)/4'
* TEST A: the rail period carrying data bit 1   (4 operations)
.meas tran E_A PARAM='(e2-e1)/4'
* TEST C: average over the alternating pattern  (8 operations)
.meas tran E_C PARAM='(e2-e0)/8'

* -------- run check -----------------------------------------------------
* p1 starts rising at TPHASE and takes TPHASE to reach VDD, so it crosses
* VDD/2 at exactly 1.5*TPHASE.  run_2lal_sweep.sh reads this back to prove
* the simulator used the TPHASE the sweep asked for.
.meas tran chk_tphase WHEN V(p1)='VDD/2' RISE=1

.end
