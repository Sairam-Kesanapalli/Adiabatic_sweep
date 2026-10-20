* ==========================================================================
* LENGTH-SWEEP helper -- threshold voltage of the sky130 1.8 V nFET and pFET.
*
* Constant-current definition: the gate voltage at which the drain current
* reaches 100 nA * W/L, at |Vds| = 0.1 V, W = 1 um, bulk tied to source.
* This deck only dumps the two I-V curves; check_lc_scaling.py applies the
* 100 nA * W/L criterion and reports how Vth moves with channel length:
* ECRL's threshold loss follows the pull-up pFET's |Vth|, and the 2LAL
* transmission gate's resistance follows both.
* run_calibration.sh substitutes L.
* ==========================================================================
.include "../models/sky130_01v8_tt_fast.spice"

.param L = 0.15

Vgn gn 0 DC 0
Vdn dn 0 DC 0.1
xN dn gn 0 0 sky130_fd_pr__nfet_01v8 w=1 l={L}

Vsp sp 0 DC 1.8
Vgp gp 0 DC 1.8
Vdp dp 0 DC 1.7
xP dp gp sp sp sky130_fd_pr__pfet_01v8 w=1 l={L}

.control
dc Vgn 0 1.8 0.001
wrdata OUTFILE.n i(Vdn)
dc Vgp 1.8 0 -0.001
wrdata OUTFILE.p i(Vsp)
quit
.endc
.end
