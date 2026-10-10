* ==========================================================================
* CHECK 2 helper -- DC table of the ECRL pull-up pFET in its clock-rise bias.
*
* While PHI rises, the output that is about to go high has its pFET's
* source and bulk on PHI and its gate on the opposite output, which the
* nFET clamps at 0 V.  Its drain is the output node Vn.  This table of
* I(PHI, Vn) lets check_calibration.py integrate C*dVn/dt = I(PHI(t), Vn)
* and predict the clock-rise loss without any transient simulation.
* Device as in ../ecrl/ecrl_slowramp.sp (w=1 l=0.15, no diffusion params).
* ==========================================================================
.include "../models/sky130_01v8_tt_fast.spice"

Vphi phi 0 DC 0
Vn   n   0 DC 0
Vm   phi s DC 0
xP n 0 s phi sky130_fd_pr__pfet_01v8 w=1 l=0.15

.control
dc Vphi 0 1.8 0.01 Vn 0 1.8 0.01
wrdata OUTFILE i(Vm)
quit
.endc
.end
