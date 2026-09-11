set terminal pngcairo size 1150,560 font "Sans,12"
set output '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/fig_2lal_clocks.png'
set multiplot layout 4,1 margins 0.13,0.97,0.12,0.90 spacing 0,0.02
set xrange [0:8]
set yrange [-0.3:2.1]
set ytics ("0" 0, "VDD" 1.8) font "Sans,10"
set grid xtics
set key left top reverse Left samplen 0 font "Sans,13 Bold" width -2
set format x ""
unset xlabel
set title "2LAL four-phase rail set: each rail lags the previous by one T_phase; T_rail = 4 x T_phase = ECRL's T_clock" font "Sans,13"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/p0.dat' u 1:2 w l lw 3 lc rgb "#a4237a" t 'phi_0' ; unset title
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/p1.dat' u 1:2 w l lw 3 lc rgb "#12866B" t 'phi_1'
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/p2.dat' u 1:2 w l lw 3 lc rgb "#0969da" t 'phi_2'
set format x "%g"
set xlabel "time  (units of T_phase)"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/p3.dat' u 1:2 w l lw 3 lc rgb "#C2704A" t 'phi_3'
unset multiplot
