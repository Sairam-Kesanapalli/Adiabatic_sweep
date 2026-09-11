* ============================================================================
* 2LAL ADIABATIC INVERTER -- sky130 / ngspice
* ----------------------------------------------------------------------------
* Two-Level Adiabatic Logic (M. P. Frank).  Four trapezoidal power-clock rails
* at 0/90/180/270 deg, 50% duty, 25% transition time -- Fig. 1 of the MEMS-
* resonator paper, reproduced exactly by the PULSE sources below.
*
* SIGNAL ENCODING  (the part that is easy to get wrong)
*   A 2LAL signal is a dual-rail pair (T,C) that RESTS AT FALSE = (0, Vdd).
*   A TRUE is signalled by T pulsing up on phi_t while C is pulled down by the
*   180-deg antiphase rail phi_t+2; the pair then returns to (0, Vdd).
*   A FALSE is the ABSENCE of a pulse -- the pair simply stays at (0, Vdd).
*   (Fig. 2c caption: 'if in pulses before tick #t, out will pulse @t, else it
*    will stay at its initial level, arranged to be F'.  4lc.cir encodes the
*    same thing as .ic V(d0T)=gg V(d0C)=vv.)
*
*   Encoding C as a pulse instead of a held level makes the pFET conduct while
*   phi_t is still high, and every stage latches a spurious 1.  That is a
*   testbench bug, not a cell bug, and it is silent -- the 1s still look fine.
*
* WHY THE INVERTER IS NOT A WIRE CROSSING
*   The rest state (0, Vdd) is ASYMMETRIC between the two rails, so crossing T
*   and C turns rest into (Vdd, 0), which the next stage reads as a permanent
*   TRUE.  Chain C below demonstrates that failure.
*   Inversion in 2LAL therefore needs QUAD-RAIL encoding: carry A and NOT-A as
*   two independent dual-rail chains and swap the CHAINS, not the rails.  The
*   swap itself costs zero transistors -- but it doubles the datapath, and
*   that doubling is the real price of a 2LAL inverter.  Chain D does this.
*
* TIMING (Frank, '2LAL Cycle of Operation'), tick = 1/4 rail period:
*   tick n   : in rises (riding phi_n-1), phi_n rises
*   tick n+1 : out rises -- stage charges through its forward pass gate
*   tick n+2 : in retracts, phi_n falls
*   tick n+3 : out restored to rest by the next stage's reverse pass gates
*
* CHAINS
*   A  BUF4   buffer  -- 4 FETs/stage, the '2 nFET + 2 pFET' advice
*   B  BUF8P  buffer  -- 8 FETs/stage, 4lc PHAS2 / Fig 2c (correct 2LAL cell)
*   C  BUF8P  'NOT'   -- B with outT/outC crossed: naive inverter (BROKEN)
*   D  BUF8P  quad-rail inverter -- two BUF8P chains, swapped after stage 2
*
* Each chain is stage0 (driver, unmetered) -> stages 1..4 (METERED) -> stage5
* (load, unmetered), so every metered stage sees a real transistor source and
* a real transistor load rather than an ideal supply.
* ============================================================================

* Full sky130 PDK via the ngspice-flavoured library, same source and corner as
* ecrl_baseline.sp so the two families are directly comparable.
* `sky130-ngspice-models` is a symlink to ~/.volare/sky130A, whose internal
* layout is identical to the sky130-ngspice-models repo the ECRL deck expects.
*
* UNITS: this library takes W and L in MICRONS (w=0.5 means 0.5 um).  The
* trimmed 4lc/*.pm3.spice files this deck used previously take METRES
* (w=500e-9).  The two conventions are silently incompatible -- passing metres
* here fails with "could not find a valid modelname", and passing microns to
* the .pm3 files would ask for a half-metre device.  Do not mix them.
.lib "./sky130-ngspice-models/libs.tech/ngspice/sky130.lib.spice" tt

* ---------------------------------------------------------------- parameters
.param Vp    = 1.8          ; rail amplitude / supply
.param ww    = 0.5          ; nFET width, MICRONS
.param wp    = 0.5          ; pFET width, MICRONS (set 1 to match ecrl_baseline.sp)
.param ll    = 0.15         ; channel length, MICRONS
* The full library is binned across the whole W range, so W is now free --
* the previous 420..520nm / 2..3um restriction came from the trimmed vendored
* models, not from sky130.  T-gates need no P/N ratioing, so both devices are
* the same width by default.

* Frail is the RAIL period frequency: one full trapezoid per 1/Frail.
* (4lc.cir's `Hz` is its LOGIC frequency and its tank runs at 2*Hz; nothing
*  here derives from that, to stay clear of the factor-of-two trap.)
.param Frail = 10e6                                            ; SWEEPVAR
.param Trail = '1/Frail'
.param tick  = 'Trail/4'    ; = transition time = 25% of the period
.param tstep = 'tick/200'
.param tstop = '8*Trail'
.param tm0   = '4*Trail'    ; energy window = rail periods 4..6
.param tm1   = '6*Trail'    ; = one 0 bit and one 1 bit

.options reltol=1e-4 abstol=1e-13 vntol=1e-7 chgtol=1e-16 gmin=1e-14
.options method=gear maxord=2

Vnb vnb 0 DC 0
Vpb vpb 0 DC {Vp}

* ---------------------------------------------------------------- power clocks
* PULSE(V1 V2 TD TR TF PW PER), TR=TF=PW=tick, PER=4*tick gives rise/high/
* fall/low of one tick each: 50% duty at the midpoint, 25% transition time.
Vp0 p0 0 PULSE(0 {Vp} 0          {tick} {tick} {tick} {Trail})
Vp1 p1 0 PULSE(0 {Vp} {tick}     {tick} {tick} {tick} {Trail})
Vp2 p2 0 PULSE(0 {Vp} {2*tick}   {tick} {tick} {tick} {Trail})
Vp3 p3 0 PULSE(0 {Vp} {3*tick}   {tick} {tick} {tick} {Trail})

* ---------------------------------------------------------------- input drive
* Ideal dual-rail input riding phi0, alternating 1,0,1,0 every rail period.
* TRUE  = (phi0, phi2)  -- T pulses up, C pulled down by the antiphase rail
* FALSE = (0,   Vdd )   -- held at rest, no pulse at all
* dctl toggles 3.5 ticks in, inside phi0's dead window, so the encoded rails
* never change while a pulse is live.
Vdctl dctl 0 PULSE(0 {Vp} {3.5*tick} 1p 1p {Trail} {2*Trail})
* A = the data bit
BinT inT 0 V = (V(dctl) > {Vp/2}) ? V(p0) : 0
BinC inC 0 V = (V(dctl) > {Vp/2}) ? V(p2) : {Vp}
* NOT A = the second rail pair the quad-rail datapath needs
BnnT nnT 0 V = (V(dctl) > {Vp/2}) ? 0     : V(p0)
BnnC nnC 0 V = (V(dctl) > {Vp/2}) ? {Vp}  : V(p2)

* ============================================================================
* CELLS -- shared port list: inT inC outT outC L0 L1 L2 L3 vnb vpb
* ============================================================================
* L1 = phi_t (this stage's clock)   L3 = phi_t+2 (its antiphase)
* L0 = phi_t-1 (the input's clock)  L2 = phi_t+1

* Transmission gate: conducts s->d when the dual-rail control (gn,gp) is TRUE.
.subckt TG d gn gp s vnb vpb
xN d gn s vnb sky130_fd_pr__nfet_01v8 w={ww} l={ll}
+ as='ww*ll*1.77' ad='ww*ll*1.77' ps='(ww+ll)*2.4' pd='(ww+ll)*2.4'
xP d gp s vpb sky130_fd_pr__pfet_01v8 w={wp} l={ll}
+ as='wp*ll*1.77' ad='wp*ll*1.77' ps='(wp+ll)*2.4' pd='(wp+ll)*2.4'
.ends TG

* --- BUF4: 4 FETs, forward only ('2 nFET + 2 pFET per stage') ---------------
* Both pass gates share one control -- the input pair -- with one passing
* phi_t and the other its antiphase.  Propagates data, but cannot pull its own
* output back down: by the time phi_t falls the input has already retracted
* and the gate is off, so the charge is stranded and dumped non-adiabatically.
.subckt BUF4 inT inC outT outC L0 L1 L2 L3 vnb vpb
XF1 outT inT inC L1 vnb vpb TG          ; TRUE -> outT pulses on phi_t
XF2 outC inT inC L3 vnb vpb TG          ; TRUE -> outC pulled down by phi_t+2
.ends BUF4

* --- BUF8P: 4lc PHAS2 / Fig 2c, the real 2LAL cell --------------------------
* BUF4 plus a REVERSE pair that drives the previous stage's node from
* phi_t-1 / phi_t+1, gated by this stage's output.  That recovers the charge
* the forward pair cannot, and is the whole reason 2LAL is adiabatic.
.subckt BUF8P inT inC outT outC L0 L1 L2 L3 vnb vpb
XF1 outT inT inC L1 vnb vpb TG          ; TRUE -> outT pulses on phi_t
XF2 outC inT inC L3 vnb vpb TG          ; TRUE -> outC pulled down by phi_t+2
XR1 inT  outT outC L0 vnb vpb TG        ; restore inT via phi_t-1
XR2 inC  outT outC L2 vnb vpb TG        ; restore inC via phi_t+1
.ends BUF8P

* ============================================================================
* CHAINS -- stage n clocked by phi_n, one tick advance per stage
* ============================================================================

* -------- per-chain rail ammeters (0 V sources used as current probes) ------
VmA0 p0 rA0 DC 0
VmA1 p1 rA1 DC 0
VmA2 p2 rA2 DC 0
VmA3 p3 rA3 DC 0
VmB0 p0 rB0 DC 0
VmB1 p1 rB1 DC 0
VmB2 p2 rB2 DC 0
VmB3 p3 rB3 DC 0
VmC0 p0 rC0 DC 0
VmC1 p1 rC1 DC 0
VmC2 p2 rC2 DC 0
VmC3 p3 rC3 DC 0
VmD0 p0 rD0 DC 0
VmD1 p1 rD1 DC 0
VmD2 p2 rD2 DC 0
VmD3 p3 rD3 DC 0

* ---------------------------------------------------------------- CHAIN A
* BUF4 buffer -- the 4-FET '2 nFET + 2 pFET' cell
XA0 inT    inC    AT1    AC1    p0   p1   p2   p3   vnb vpb BUF4
XA1 AT1    AC1    AT2    AC2    rA1  rA2  rA3  rA0  vnb vpb BUF4
XA2 AT2    AC2    AT3    AC3    rA2  rA3  rA0  rA1  vnb vpb BUF4
XA3 AT3    AC3    AT4    AC4    rA3  rA0  rA1  rA2  vnb vpb BUF4
XA4 AT4    AC4    AT5    AC5    rA0  rA1  rA2  rA3  vnb vpb BUF4
XA5 AT5    AC5    AT6    AC6    p1   p2   p3   p0   vnb vpb BUF4

* ---------------------------------------------------------------- CHAIN B
* BUF8P buffer -- the correct 8-FET 2LAL cell (reference)
XB0 inT    inC    BT1    BC1    p0   p1   p2   p3   vnb vpb BUF8P
XB1 BT1    BC1    BT2    BC2    rB1  rB2  rB3  rB0  vnb vpb BUF8P
XB2 BT2    BC2    BT3    BC3    rB2  rB3  rB0  rB1  vnb vpb BUF8P
XB3 BT3    BC3    BT4    BC4    rB3  rB0  rB1  rB2  vnb vpb BUF8P
XB4 BT4    BC4    BT5    BC5    rB0  rB1  rB2  rB3  vnb vpb BUF8P
XB5 BT5    BC5    BT6    BC6    p1   p2   p3   p0   vnb vpb BUF8P

* ---------------------------------------------------------------- CHAIN C
* BUF8P with outT/outC CROSSED -- the naive inverter (expected to fail)
XC0 inT    inC    CC1    CT1    p0   p1   p2   p3   vnb vpb BUF8P
XC1 CT1    CC1    CC2    CT2    rC1  rC2  rC3  rC0  vnb vpb BUF8P
XC2 CT2    CC2    CC3    CT3    rC2  rC3  rC0  rC1  vnb vpb BUF8P
XC3 CT3    CC3    CC4    CT4    rC3  rC0  rC1  rC2  vnb vpb BUF8P
XC4 CT4    CC4    CC5    CT5    rC0  rC1  rC2  rC3  vnb vpb BUF8P
XC5 CT5    CC5    CC6    CT6    p1   p2   p3   p0   vnb vpb BUF8P

* ---------------------------------------------------------------- CHAIN D
* QUAD-RAIL inverter -- two BUF8P chains (DP carries A, DN carries NOT A)
*   with the two chains swapped going into stage 3.  The swap is pure
*   wiring: zero transistors.  DP after the swap carries NOT A.
XD0DP inT    inC    DPT1   DPC1   p0   p1   p2   p3   vnb vpb BUF8P
XD0DN nnT    nnC    DNT1   DNC1   p0   p1   p2   p3   vnb vpb BUF8P
XD1DP DPT1   DPC1   DPT2   DPC2   rD1  rD2  rD3  rD0  vnb vpb BUF8P
XD1DN DNT1   DNC1   DNT2   DNC2   rD1  rD2  rD3  rD0  vnb vpb BUF8P
XD2DP DPT2   DPC2   DPT3   DPC3   rD2  rD3  rD0  rD1  vnb vpb BUF8P
XD2DN DNT2   DNC2   DNT3   DNC3   rD2  rD3  rD0  rD1  vnb vpb BUF8P
XD3DP DNT3   DNC3   DPT4   DPC4   rD3  rD0  rD1  rD2  vnb vpb BUF8P
XD3DN DPT3   DPC3   DNT4   DNC4   rD3  rD0  rD1  rD2  vnb vpb BUF8P
XD4DP DPT4   DPC4   DPT5   DPC5   rD0  rD1  rD2  rD3  vnb vpb BUF8P
XD4DN DNT4   DNC4   DNT5   DNC5   rD0  rD1  rD2  rD3  vnb vpb BUF8P
XD5DP DPT5   DPC5   DPT6   DPC6   p1   p2   p3   p0   vnb vpb BUF8P
XD5DN DNT5   DNC5   DNT6   DNC6   p1   p2   p3   p0   vnb vpb BUF8P

* ---------------------------------------------------------------- wiring load
.param Cw = 1e-14           ; interconnect capacitance per dual-rail node
CAT1 AT1 0 {Cw}
CAC1 AC1 0 {Cw}
CAT2 AT2 0 {Cw}
CAC2 AC2 0 {Cw}
CAT3 AT3 0 {Cw}
CAC3 AC3 0 {Cw}
CAT4 AT4 0 {Cw}
CAC4 AC4 0 {Cw}
CAT5 AT5 0 {Cw}
CAC5 AC5 0 {Cw}
CBT1 BT1 0 {Cw}
CBC1 BC1 0 {Cw}
CBT2 BT2 0 {Cw}
CBC2 BC2 0 {Cw}
CBT3 BT3 0 {Cw}
CBC3 BC3 0 {Cw}
CBT4 BT4 0 {Cw}
CBC4 BC4 0 {Cw}
CBT5 BT5 0 {Cw}
CBC5 BC5 0 {Cw}
CCT1 CT1 0 {Cw}
CCC1 CC1 0 {Cw}
CCT2 CT2 0 {Cw}
CCC2 CC2 0 {Cw}
CCT3 CT3 0 {Cw}
CCC3 CC3 0 {Cw}
CCT4 CT4 0 {Cw}
CCC4 CC4 0 {Cw}
CCT5 CT5 0 {Cw}
CCC5 CC5 0 {Cw}
CDPT1 DPT1 0 {Cw}
CDPC1 DPC1 0 {Cw}
CDPT2 DPT2 0 {Cw}
CDPC2 DPC2 0 {Cw}
CDPT3 DPT3 0 {Cw}
CDPC3 DPC3 0 {Cw}
CDPT4 DPT4 0 {Cw}
CDPC4 DPC4 0 {Cw}
CDPT5 DPT5 0 {Cw}
CDPC5 DPC5 0 {Cw}
CDNT1 DNT1 0 {Cw}
CDNC1 DNC1 0 {Cw}
CDNT2 DNT2 0 {Cw}
CDNC2 DNC2 0 {Cw}
CDNT3 DNT3 0 {Cw}
CDNC3 DNC3 0 {Cw}
CDNT4 DNT4 0 {Cw}
CDNC4 DNC4 0 {Cw}
CDNT5 DNT5 0 {Cw}
CDNC5 DNC5 0 {Cw}

* ============================================================================
* ENERGY INTEGRATORS
* ============================================================================
* A behavioural current source pushing P(t) into a 1 F capacitor makes V(e*)
* the running integral of power, so the node reads directly in JOULES.
BeA 0 eA I = V(rA0)*I(VmA0) + V(rA1)*I(VmA1) + V(rA2)*I(VmA2) + V(rA3)*I(VmA3)
CeA eA 0 1
ReA eA 0 1e15
BeB 0 eB I = V(rB0)*I(VmB0) + V(rB1)*I(VmB1) + V(rB2)*I(VmB2) + V(rB3)*I(VmB3)
CeB eB 0 1
ReB eB 0 1e15
BeC 0 eC I = V(rC0)*I(VmC0) + V(rC1)*I(VmC1) + V(rC2)*I(VmC2) + V(rC3)*I(VmC3)
CeC eC 0 1
ReC eC 0 1e15
BeD 0 eD I = V(rD0)*I(VmD0) + V(rD1)*I(VmD1) + V(rD2)*I(VmD2) + V(rD3)*I(VmD3)
CeD eD 0 1
ReD eD 0 1e15

* ---------------------------------------------------------------- rest state
* Every dual-rail node starts at FALSE = (0, Vdd) -- 'arranged to be F'.
* Starting them all at 0 instead injects a spurious first bit.
.ic V(eA)=0 V(eB)=0 V(eC)=0 V(eD)=0
.ic V(AT1)=0 V(AC1)={Vp} V(AT2)=0 V(AC2)={Vp} V(AT3)=0 V(AC3)={Vp} V(AT4)=0 V(AC4)={Vp} V(AT5)=0 V(AC5)={Vp} V(AT6)=0 V(AC6)={Vp}
.ic V(BT1)=0 V(BC1)={Vp} V(BT2)=0 V(BC2)={Vp} V(BT3)=0 V(BC3)={Vp} V(BT4)=0 V(BC4)={Vp} V(BT5)=0 V(BC5)={Vp} V(BT6)=0 V(BC6)={Vp}
.ic V(CT1)=0 V(CC1)={Vp} V(CT2)=0 V(CC2)={Vp} V(CT3)=0 V(CC3)={Vp} V(CT4)=0 V(CC4)={Vp} V(CT5)=0 V(CC5)={Vp} V(CT6)=0 V(CC6)={Vp}
.ic V(DPT1)=0 V(DPC1)={Vp} V(DPT2)=0 V(DPC2)={Vp} V(DPT3)=0 V(DPC3)={Vp} V(DPT4)=0 V(DPC4)={Vp} V(DPT5)=0 V(DPC5)={Vp} V(DPT6)=0 V(DPC6)={Vp}
.ic V(DNT1)=0 V(DNC1)={Vp} V(DNT2)=0 V(DNC2)={Vp} V(DNT3)=0 V(DNC3)={Vp} V(DNT4)=0 V(DNC4)={Vp} V(DNT5)=0 V(DNC5)={Vp} V(DNT6)=0 V(DNC6)={Vp}

.tran {tstep} {tstop} uic

* ============================================================================
* FUNCTIONAL CHECKS
* ============================================================================
* Stage n's output plateaus during tick n+1, so sample (n+1.5) ticks in.
* Rail period 4 carries bit 0, period 5 carries bit 1.
* NOTE: stage 4's sample lands 1.5 ticks into the FOLLOWING rail period (the
* bit has advanced 4 ticks by then), so read stages 1-3 for the bit under test;
* stage 4 is shown to confirm the value keeps advancing, not to check polarity.
* PASS = T and C rail-to-rail and complementary:
*   TRUE -> T ~ 1.8, C ~ 0        FALSE -> T ~ 0, C ~ 1.8
.param tb0_s1 = '4*Trail + 2.5*tick'
.param tb0_s2 = '4*Trail + 3.5*tick'
.param tb0_s3 = '4*Trail + 4.5*tick'
.param tb0_s4 = '4*Trail + 5.5*tick'
.param tb1_s1 = '5*Trail + 2.5*tick'
.param tb1_s2 = '5*Trail + 3.5*tick'
.param tb1_s3 = '5*Trail + 4.5*tick'
.param tb1_s4 = '5*Trail + 5.5*tick'

.meas tran drv_b0_inT FIND V(inT) AT={tb0_s1}
.meas tran drv_b0_inC FIND V(inC) AT={tb0_s1}
.meas tran drv_b0_nnT FIND V(nnT) AT={tb0_s1}
.meas tran drv_b0_nnC FIND V(nnC) AT={tb0_s1}
.meas tran drv_b1_inT FIND V(inT) AT={tb1_s1}
.meas tran drv_b1_inC FIND V(inC) AT={tb1_s1}
.meas tran drv_b1_nnT FIND V(nnT) AT={tb1_s1}
.meas tran drv_b1_nnC FIND V(nnC) AT={tb1_s1}
* chain A
.meas tran A1_b0_T FIND V(AT1) AT={tb0_s1}
.meas tran A1_b0_C FIND V(AC1) AT={tb0_s1}
.meas tran A2_b0_T FIND V(AT2) AT={tb0_s2}
.meas tran A2_b0_C FIND V(AC2) AT={tb0_s2}
.meas tran A3_b0_T FIND V(AT3) AT={tb0_s3}
.meas tran A3_b0_C FIND V(AC3) AT={tb0_s3}
.meas tran A4_b0_T FIND V(AT4) AT={tb0_s4}
.meas tran A4_b0_C FIND V(AC4) AT={tb0_s4}
.meas tran A1_b1_T FIND V(AT1) AT={tb1_s1}
.meas tran A1_b1_C FIND V(AC1) AT={tb1_s1}
.meas tran A2_b1_T FIND V(AT2) AT={tb1_s2}
.meas tran A2_b1_C FIND V(AC2) AT={tb1_s2}
.meas tran A3_b1_T FIND V(AT3) AT={tb1_s3}
.meas tran A3_b1_C FIND V(AC3) AT={tb1_s3}
.meas tran A4_b1_T FIND V(AT4) AT={tb1_s4}
.meas tran A4_b1_C FIND V(AC4) AT={tb1_s4}
* chain B
.meas tran B1_b0_T FIND V(BT1) AT={tb0_s1}
.meas tran B1_b0_C FIND V(BC1) AT={tb0_s1}
.meas tran B2_b0_T FIND V(BT2) AT={tb0_s2}
.meas tran B2_b0_C FIND V(BC2) AT={tb0_s2}
.meas tran B3_b0_T FIND V(BT3) AT={tb0_s3}
.meas tran B3_b0_C FIND V(BC3) AT={tb0_s3}
.meas tran B4_b0_T FIND V(BT4) AT={tb0_s4}
.meas tran B4_b0_C FIND V(BC4) AT={tb0_s4}
.meas tran B1_b1_T FIND V(BT1) AT={tb1_s1}
.meas tran B1_b1_C FIND V(BC1) AT={tb1_s1}
.meas tran B2_b1_T FIND V(BT2) AT={tb1_s2}
.meas tran B2_b1_C FIND V(BC2) AT={tb1_s2}
.meas tran B3_b1_T FIND V(BT3) AT={tb1_s3}
.meas tran B3_b1_C FIND V(BC3) AT={tb1_s3}
.meas tran B4_b1_T FIND V(BT4) AT={tb1_s4}
.meas tran B4_b1_C FIND V(BC4) AT={tb1_s4}
* chain C
.meas tran C1_b0_T FIND V(CT1) AT={tb0_s1}
.meas tran C1_b0_C FIND V(CC1) AT={tb0_s1}
.meas tran C2_b0_T FIND V(CT2) AT={tb0_s2}
.meas tran C2_b0_C FIND V(CC2) AT={tb0_s2}
.meas tran C3_b0_T FIND V(CT3) AT={tb0_s3}
.meas tran C3_b0_C FIND V(CC3) AT={tb0_s3}
.meas tran C4_b0_T FIND V(CT4) AT={tb0_s4}
.meas tran C4_b0_C FIND V(CC4) AT={tb0_s4}
.meas tran C1_b1_T FIND V(CT1) AT={tb1_s1}
.meas tran C1_b1_C FIND V(CC1) AT={tb1_s1}
.meas tran C2_b1_T FIND V(CT2) AT={tb1_s2}
.meas tran C2_b1_C FIND V(CC2) AT={tb1_s2}
.meas tran C3_b1_T FIND V(CT3) AT={tb1_s3}
.meas tran C3_b1_C FIND V(CC3) AT={tb1_s3}
.meas tran C4_b1_T FIND V(CT4) AT={tb1_s4}
.meas tran C4_b1_C FIND V(CC4) AT={tb1_s4}
* chain D
.meas tran DP1_b0_T FIND V(DPT1) AT={tb0_s1}
.meas tran DP1_b0_C FIND V(DPC1) AT={tb0_s1}
.meas tran DP2_b0_T FIND V(DPT2) AT={tb0_s2}
.meas tran DP2_b0_C FIND V(DPC2) AT={tb0_s2}
.meas tran DP3_b0_T FIND V(DPT3) AT={tb0_s3}
.meas tran DP3_b0_C FIND V(DPC3) AT={tb0_s3}
.meas tran DP4_b0_T FIND V(DPT4) AT={tb0_s4}
.meas tran DP4_b0_C FIND V(DPC4) AT={tb0_s4}
.meas tran DP1_b1_T FIND V(DPT1) AT={tb1_s1}
.meas tran DP1_b1_C FIND V(DPC1) AT={tb1_s1}
.meas tran DP2_b1_T FIND V(DPT2) AT={tb1_s2}
.meas tran DP2_b1_C FIND V(DPC2) AT={tb1_s2}
.meas tran DP3_b1_T FIND V(DPT3) AT={tb1_s3}
.meas tran DP3_b1_C FIND V(DPC3) AT={tb1_s3}
.meas tran DP4_b1_T FIND V(DPT4) AT={tb1_s4}
.meas tran DP4_b1_C FIND V(DPC4) AT={tb1_s4}
.meas tran DN1_b0_T FIND V(DNT1) AT={tb0_s1}
.meas tran DN1_b0_C FIND V(DNC1) AT={tb0_s1}
.meas tran DN2_b0_T FIND V(DNT2) AT={tb0_s2}
.meas tran DN2_b0_C FIND V(DNC2) AT={tb0_s2}
.meas tran DN3_b0_T FIND V(DNT3) AT={tb0_s3}
.meas tran DN3_b0_C FIND V(DNC3) AT={tb0_s3}
.meas tran DN4_b0_T FIND V(DNT4) AT={tb0_s4}
.meas tran DN4_b0_C FIND V(DNC4) AT={tb0_s4}
.meas tran DN1_b1_T FIND V(DNT1) AT={tb1_s1}
.meas tran DN1_b1_C FIND V(DNC1) AT={tb1_s1}
.meas tran DN2_b1_T FIND V(DNT2) AT={tb1_s2}
.meas tran DN2_b1_C FIND V(DNC2) AT={tb1_s2}
.meas tran DN3_b1_T FIND V(DNT3) AT={tb1_s3}
.meas tran DN3_b1_C FIND V(DNC3) AT={tb1_s3}
.meas tran DN4_b1_T FIND V(DNT4) AT={tb1_s4}
.meas tran DN4_b1_C FIND V(DNC4) AT={tb1_s4}

* ============================================================================
* ENERGY -- periods 4..6 = 2 bits through 4 metered stages = 8 stage-ops
* ============================================================================
.meas tran eA_0 FIND V(eA) AT={tm0}
.meas tran eA_1 FIND V(eA) AT={tm1}
.meas tran eB_0 FIND V(eB) AT={tm0}
.meas tran eB_1 FIND V(eB) AT={tm1}
.meas tran eC_0 FIND V(eC) AT={tm0}
.meas tran eC_1 FIND V(eC) AT={tm1}
.meas tran eD_0 FIND V(eD) AT={tm0}
.meas tran eD_1 FIND V(eD) AT={tm1}
.meas tran E_BUF4 PARAM='(eA_1-eA_0)/8'
.meas tran E_BUF8P PARAM='(eB_1-eB_0)/8'
.meas tran E_NAIVE_NOT PARAM='(eC_1-eC_0)/8'
.meas tran E_QUADRAIL_NOT PARAM='(eD_1-eD_0)/8'

.end
