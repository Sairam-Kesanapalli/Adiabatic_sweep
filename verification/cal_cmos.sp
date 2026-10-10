* ==========================================================================
* CHECK 1a -- static CMOS inverter through the SAME energy meter as 2LAL.
* run_calibration.sh sweeps CL and TPER; check_calibration.py fits the line.
*
* Energy drawn from VDD per full output cycle (0->1->0) is
*     E_cyc = (CL + Cpar) * VDD^2 + E_sc
* so dE_cyc/dCL must equal VDD^2 = 3.24 fJ/fF whatever Cpar and the
* short-circuit energy are.  That slope is the calibration.
*
* Meter 1 is the 2LAL deck's B-source -> 1 F integrator, copied verbatim.
* Meter 2 is ngspice's own .meas INTEG of the same power, as a cross-check.
* ==========================================================================
.include "../models/sky130_01v8_tt_fast.spice"

.param VDD   = 1.8
.param WN    = 1.0
.param WP    = 1.0
.param L     = 0.15
.param CL    = 25f
.param TPER  = 40n
.param TEDGE = 100p
.param TSTEP = 'TPER/2000'

.options reltol=1e-4 abstol=1e-13 vntol=1e-7 chgtol=1e-16 gmin=1e-14
.options method=gear maxord=2

Vdd vdd 0 DC {VDD}
Vm  vdd vddm DC 0
Vin in 0 PULSE(0 {VDD} {TPER/4} {TEDGE} {TEDGE} {TPER/2-TEDGE} {TPER})

xP out in vddm vddm sky130_fd_pr__pfet_01v8 w={WP} l={L}
+ as='WP*L*1.77' ad='WP*L*1.77' ps='(WP+L)*2.4' pd='(WP+L)*2.4'
xN out in 0 0 sky130_fd_pr__nfet_01v8 w={WN} l={L}
+ as='WN*L*1.77' ad='WN*L*1.77' ps='(WN+L)*2.4' pd='(WN+L)*2.4'
CL out 0 {CL}

Be 0 e I = V(vddm)*I(Vm)
Ce e 0 1
Re e 0 1e15
.ic V(e)=0

.tran {TSTEP} {4*TPER} uic

* two settled cycles, periods 2 and 3
.meas tran e1 FIND V(e) AT={2*TPER}
.meas tran e2 FIND V(e) AT={4*TPER}
.meas tran E_CYC PARAM='(e2-e1)/2'
.meas tran E_INT INTEG par('V(vddm)*I(Vm)') FROM={2*TPER} TO={4*TPER}
.meas tran E_CYC2 PARAM='E_INT/2'
* functional: output high while input is low, and vice versa
.meas tran vout_hi FIND V(out) AT={3.1*TPER}
.meas tran vout_lo FIND V(out) AT={3.6*TPER}
.end
