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

.control

* ============================================================
* ECRL ENERGY vs POWER-CLOCK PHASE TIME
* WN = WP = 1 um
* LN = LP = 0.15 um
* ============================================================

set noaskquit

* Create result vectors
let tphase_vec = vector(7)
let energy_vec = vector(7)

* ------------------------------------------------------------
* TPHASE = 1 ns
* ------------------------------------------------------------

alterparam TPHASE=1n
reset
tran 10p 12n
meas tran E1 integ v(PCLK) from=4n to=8n

let tphase_vec[0] = 1
let energy_vec[0] = E1

* ------------------------------------------------------------
* TPHASE = 2 ns
* ------------------------------------------------------------

alterparam TPHASE=2n
reset
tran 10p 24n
meas tran E2 integ v(PCLK) from=8n to=16n

let tphase_vec[1] = 2
let energy_vec[1] = E2

* ------------------------------------------------------------
* TPHASE = 5 ns
* ------------------------------------------------------------

alterparam TPHASE=5n
reset
tran 10p 60n
meas tran E5 integ v(PCLK) from=20n to=40n

let tphase_vec[2] = 5
let energy_vec[2] = E5

* ------------------------------------------------------------
* TPHASE = 10 ns
* ------------------------------------------------------------

alterparam TPHASE=10n
reset
tran 10p 120n
meas tran E10 integ v(PCLK) from=40n to=80n

let tphase_vec[3] = 10
let energy_vec[3] = E10

* ------------------------------------------------------------
* TPHASE = 20 ns
* ------------------------------------------------------------

alterparam TPHASE=20n
reset
tran 10p 240n
meas tran E20 integ v(PCLK) from=80n to=160n

let tphase_vec[4] = 20
let energy_vec[4] = E20

* ------------------------------------------------------------
* TPHASE = 50 ns
* ------------------------------------------------------------

alterparam TPHASE=50n
reset
tran 10p 600n
meas tran E50 integ v(PCLK) from=200n to=400n

let tphase_vec[5] = 50
let energy_vec[5] = E50

* ------------------------------------------------------------
* TPHASE = 100 ns
* ------------------------------------------------------------

alterparam TPHASE=100n
reset
tran 10p 1.2u
meas tran E100 integ v(PCLK) from=400n to=800n

let tphase_vec[6] = 100
let energy_vec[6] = E100

* ------------------------------------------------------------
* Display results
* ------------------------------------------------------------

print tphase_vec energy_vec

* ------------------------------------------------------------
* Plot
* ------------------------------------------------------------

plot energy_vec vs tphase_vec

.endc
.end
