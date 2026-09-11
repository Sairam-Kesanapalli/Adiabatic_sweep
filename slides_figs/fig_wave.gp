set terminal pngcairo size 1700,680 font "Sans,13"
set output '/home/madhav/Documents/Cutout/Adiabatic_sweep/slides_figs/fig_ecrl_waveform.png'
set multiplot layout 4,1 margins 0.065,0.985,0.115,0.90 spacing 0,0.012
set xrange [0:200]
set yrange [-0.25:2.15]
set ytics ("0" 0, "1.8" 1.8) font "Sans,10"
set grid xtics ytics
set key top right font "Sans,11" samplen 1.5
set object 1 rect from 120,-0.25 to 160,2.15 fc rgb "#dde8f7" fs solid noborder behind
set object 2 rect from 160,-0.25 to 200,2.15 fc rgb "#f7e6dd" fs solid noborder behind
unset xlabel
set format x ""
set title "ECRL inverter, sky130 tt, W = 1.0 um, TPHASE = 10 ns   |   shaded = the two metered clock cycles (0->1 and 1->0)" font "Sans,13"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/ecrl_wave.dat' u ($1*1e9):2 w l lw 2.5 lc rgb "#8B008B" t 'PHI  (power clock)'
unset title
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/ecrl_wave.dat' u ($3*1e9):4 w l lw 2.5 lc rgb "#B8860B" t 'IN  (slow ramp, in PHI wait window)'
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/ecrl_wave.dat' u ($5*1e9):6 w l lw 2.5 lc rgb "#1a7f37" t 'OUT'
set format x "%g"
set xlabel "time  (ns)"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/ecrl_wave.dat' u ($7*1e9):8 w l lw 2.5 lc rgb "#0969da" t 'OUTB'
unset multiplot
