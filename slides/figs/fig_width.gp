set terminal pngcairo size 1050,720 font "Sans,12"
set output '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/fig_width_sweep.png'
set title "Transistor sizing helps only where the loss is resistive\nECRL inverter, sky130 tt, VDD 1.8 V, L = 0.15 um, CL = 25 fF" font "Sans,13"
set xlabel "Transistor width W  (um)   -- nFET and pFET sized together"
set ylabel "Energy per operation  (fJ)"
set grid
set key top right
set xrange [0.7:3.3]
set yrange [0:66]
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/width.dat' u 1:2 w linespoints lw 3 pt 7 ps 1.3 lc rgb "#a4237a" t 'f_tr = 1000 MHz   (-39% across the sweep)', \
     '' u 1:3 w linespoints lw 3 pt 5 ps 1.2 lc rgb "#1a7f37" t 'f_tr = 100 MHz     (-20%)', \
     '' u 1:4 w linespoints lw 3 pt 9 ps 1.4 lc rgb "#0969da" t 'f_tr = 10 MHz       (-8%, essentially flat)'
