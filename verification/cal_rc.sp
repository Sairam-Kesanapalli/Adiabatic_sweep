* ==========================================================================
* CHECK 1c -- ideal R-C driven by the SAME trapezoid as one 2LAL rail.
*
* Each rail period pushes ~C*VDD^2 = 81 fJ into the capacitor and takes
* almost all of it back; the meter has to recover the small residue from
* two large, nearly cancelling flows, which static CMOS never tests.
* check_calibration.py compares E_PER with the exact solution of the RC
* equation for this waveform (closed form when T >> tau:
*     E_ramp = C*V^2*(tau/T)*[1 - (tau/T)*(1 - exp(-T/tau))] ).
*
* Same .options, same TSTEP = TPHASE/500 and same 1 F integrator as
* ../2lal/2LAL_inverter_ring.sp.
* ==========================================================================
.param VDD    = 1.8
.param R      = 10k
.param C      = 25f
.param TPHASE = 10n
.param TRAIL  = '4*TPHASE'
.param TSTEP  = 'TPHASE/500'

.options reltol=1e-4 abstol=1e-13 vntol=1e-7 chgtol=1e-16 gmin=1e-14
.options method=gear maxord=2

Vp p 0 PULSE(0 {VDD} 0 {TPHASE} {TPHASE} {TPHASE} {TRAIL})
Vm p r DC 0
R1 r n {R}
C1 n 0 {C}

Be 0 e I = V(r)*I(Vm)
Ce e 0 1
Re e 0 1e15
.ic V(e)=0 V(n)=0

.tran {TSTEP} {4*TRAIL} uic

* rail period 2 (settled)
.meas tran e1 FIND V(e) AT={2*TRAIL}
.meas tran e2 FIND V(e) AT={3*TRAIL}
.meas tran E_PER PARAM='e2-e1'
.end
