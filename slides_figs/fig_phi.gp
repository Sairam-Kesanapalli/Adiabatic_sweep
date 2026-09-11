set terminal pngcairo size 1150,450 font "Sans,13"
set output '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/fig_phi_phases.png'
set title "ECRL power clock: four equal phases, T_clock = 4 x T_phase" font "Sans,14"
set xrange [0:8]
set yrange [-0.35:3.0]
set ytics ("0" 0, "VDD = 1.8 V" 1.8) font "Sans,11"
set xtics ("0" 0, "T_p" 1, "2T_p" 2, "3T_p" 3, "4T_p" 4, "5T_p" 5, "6T_p" 6, "7T_p" 7, "8T_p" 8)
set grid xtics
unset key
set label 1 "WAIT"  at 0.5,-0.22 center font "Sans,11 Bold" tc rgb "#555555"
set label 2 "RISE"  at 1.5,-0.22 center font "Sans,11 Bold" tc rgb "#a4237a"
set label 3 "HOLD"  at 2.5,-0.22 center font "Sans,11 Bold" tc rgb "#555555"
set label 4 "FALL"  at 3.5,-0.22 center font "Sans,11 Bold" tc rgb "#a4237a"
set label 5 "input may change here" at 0.5,2.05 center font "Sans,10" tc rgb "#666666" rotate by 0
set arrow 2 from 0.5,1.9 to 0.5,0.08 lw 1.2 lc rgb "#999999" size screen 0.008,20
set arrow 1 from 0,2.62 to 4,2.62 heads size screen 0.008,20 lw 1.5 lc rgb "#555555"
set label 7 "one T_clock = one operation = one data transaction" at 2.0,2.80 center font "Sans,11 Bold" tc rgb "#333333"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/phi1.dat' u 1:2 w l lw 3 lc rgb "#8B008B"
