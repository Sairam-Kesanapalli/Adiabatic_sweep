* ============================================================
* ECRL INVERTER - SKY130 BASELINE
* ============================================================

* ------------------------------------------------------------
* SKY130 TT MODEL
* MUST COME BEFORE DEVICE INSTANCES
* ------------------------------------------------------------

.lib "./sky130-ngspice-models/libs.tech/ngspice/sky130.lib.spice" tt


* ------------------------------------------------------------
* PARAMETERS
* ------------------------------------------------------------

.param VDD=1.8

.param WNMOS=1u
.param WPMOS=1u

.param LNMOS=0.15u
.param LPMOS=0.15u

.param CL=25f

.param TPHASE=10n
.param TIN=100p


* ------------------------------------------------------------
* POWER CLOCK
*
* wait  -> rise -> hold -> fall
*
* equal timing:
* TWAIT = TRISE = THOLD = TFALL = TPHASE
*
* Tclock = 4*TPHASE
* ------------------------------------------------------------

VPHI PHI 0 PULSE(0 {VDD} {TPHASE} {TPHASE} {TPHASE} {TPHASE} {4*TPHASE})
* Instantaneous power delivered by the power clock
* Positive value = power delivered to circuit
BPCPOWER PCLK 0 V={-V(PHI)*I(VPHI)}

* ------------------------------------------------------------
* INPUT
* ------------------------------------------------------------

VIN IN 0 PULSE(0 {VDD} {TPHASE/2} {TIN} {TIN} {3*TPHASE} {8*TPHASE})

* Complementary input
B_INB INB 0 V={VDD-V(IN)}


* ------------------------------------------------------------
* ECRL INVERTER
*
* PMOS:
*
* MP1: D=OUTB G=OUT  S=PHI B=PHI
* MP2: D=OUT  G=OUTB S=PHI B=PHI
*
* NMOS:
*
* MN1: D=OUTB G=INB S=0 B=0
* MN2: D=OUT  G=IN  S=0 B=0
* ------------------------------------------------------------

XMP1 OUTB OUT  PHI PHI sky130_fd_pr__pfet_01v8 l=0.15 w=1 m=1
XMP2 OUT  OUTB PHI PHI sky130_fd_pr__pfet_01v8 l=0.15 w=1 m=1

XMN1 OUTB INB 0 0 sky130_fd_pr__nfet_01v8 l=0.15 w=1 m=1
XMN2 OUT IN 0 0 sky130_fd_pr__nfet_01v8 l=0.15 w=1 m=1

* ------------------------------------------------------------
* OUTPUT LOAD
* ------------------------------------------------------------

CLOAD_OUT  OUT  0 {CL}
CLOAD_OUTB OUTB 0 {CL}


* ============================================================
* TRANSIENT ANALYSIS
* ============================================================

.tran 10p {12*TPHASE}

.save V(PHI) V(IN) V(INB) V(OUT) V(OUTB) I(VPHI) V(PCLK)

.print tran V(PHI) V(IN) V(INB) V(OUT) V(OUTB) I(VPHI) V(PCLK)

.meas tran E_OP INTEG V(PCLK) FROM=40n TO=80n

.end
