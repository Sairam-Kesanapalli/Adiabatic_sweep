set terminal pngcairo size 1000,700 font "Sans,13"
set output '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/fig_measurement_bug.png'
set title "The measurement-window defect we found and fixed\nECRL inverter, W = 1.0 um, TPHASE = 100 ns (f_tr = 10 MHz) -- same netlist, same window length" font "Sans,13"
set ylabel "Energy per power-clock cycle  (fJ)"
set yrange [0:17]
set xrange [-0.75:1.75]
set style fill solid 0.85 border rgb "#444444"
set boxwidth 0.5
set grid ytics
unset key
set bmargin 6
set xtics font "Sans,13" offset 0,-0.3
set label 1 "5.36 fJ"  at 0,5.9  center font "Sans,17 Bold" tc rgb "#8a1c1c"
set label 2 "12.46 fJ" at 1,13.0 center font "Sans,17 Bold" tc rgb "#0b5a2a"
set label 3 "2.3x   (+132%)" at 0.5,15.4 center font "Sans,15 Bold" tc rgb "#333333"
set label 4 "input never changes\ninside the metered window" at 0,-2.4 center font "Sans,11" tc rgb "#555555"
set label 5 "exactly one real 0->1 transition\ninside the metered window" at 1,-2.4 center font "Sans,11" tc rgb "#555555"
set arrow 1 from 0.25,14.6 to 0.75,14.6 heads size screen 0.012,20 lw 2 lc rgb "#333333"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/bug.dat' using 1:3:xtic(2) with boxes lc rgb "#c2704a"
