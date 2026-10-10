* ==========================================================================
* CHECK 2 helper -- on-resistance of the 2LAL transmission gate.
*
* Gates fully on (n gate at VDD, p gate at 0), 10 mV across the gate,
* common mode swept 0 .. 1.79 V.  For a node ramped adiabatically through
* this gate, the loss per ramp is C^2*V^2*mean(R)/T with the mean taken
* uniformly over voltage, so check_calibration.py averages R over the sweep.
* Same device geometry and diffusion parasitics as the TG subckt in
* ../2lal/2LAL_inverter_ring.sp.  run_calibration.sh substitutes W.
* ==========================================================================
.include "../models/sky130_01v8_tt_fast.spice"

.param W = 1.0
.param L = 0.15

Vs  s   0 DC 0
Vd  d   s DC 0.01
Vgn gn  0 DC 1.8
Vgp gp  0 DC 0
Vpb vpb 0 DC 1.8

xN d gn s 0 sky130_fd_pr__nfet_01v8 w={W} l={L}
+ as='W*L*1.77' ad='W*L*1.77' ps='(W+L)*2.4' pd='(W+L)*2.4'
xP d gp s vpb sky130_fd_pr__pfet_01v8 w={W} l={L}
+ as='W*L*1.77' ad='W*L*1.77' ps='(W+L)*2.4' pd='(W+L)*2.4'

.control
dc Vs 0 1.79 0.01
wrdata OUTFILE i(Vd)
quit
.endc
.end
