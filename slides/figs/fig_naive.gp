set terminal pngcairo size 1050,720 font "Sans,12"
set output '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/fig_naive_vs_quadrail.png'
set title "Why a 2LAL inverter cannot be a wire crossing\nsky130 tt, W = 1.0 um, CL = 25 fF -- energy per operation, log scale" font "Sans,13"
set xlabel "Rail frequency  f_rail = 1/T_rail   (MHz)"
set ylabel "Energy per operation  (fJ)"
set logscale x
set logscale y
set grid
set key top right
set xrange [0.8:1300]
set yrange [3:2e5]
set format y "10^{%L}"
plot '/tmp/claude-1000/-home-madhav-Documents-Cutout-Adiabatic-sweep/900e4640-5aa3-4140-a2ef-dd7901ac4fc1/scratchpad/naive.dat' u 1:2 w linespoints lw 3 pt 7 ps 1.2 lc rgb "#c0242c" t 'Naive inverter: rails crossed  (NON-adiabatic, shorts the rails)', \
     '' u 1:3 w linespoints lw 3 pt 5 ps 1.2 lc rgb "#1a7f37" t 'Quad-rail inverter  (correct)', \
     '' u 1:4 w linespoints lw 3 pt 9 ps 1.3 lc rgb "#0969da" t '8-FET buffer cell  (reference)'
