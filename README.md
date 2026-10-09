# Adiabatic logic in SKY130: ECRL vs 2LAL inverter

ngspice simulations of two adiabatic logic families in the SkyWater SKY130
PDK (tt corner, 1.8 V): an **ECRL** inverter and a **2LAL** quad-rail
inverter.  Both are swept over the same device widths and clock speeds, and
energy per operation is compared under matched conditions (same load
25 fF, L = 0.15 um, same TPHASE, alternating data).

## Layout

```
models/          sky130 model include shared by every deck, PDK link script
ecrl/            ECRL deck in use, its sweep script and results CSV
  baseline/      the original ECRL deck, width sweep and ngspice plot decks
2lal/            2LAL 8-stage ring deck, its generator, sweep script and results CSV
  superseded/    the earlier open-chain 2LAL decks (energy bug, kept for reference)
plots/           make_plots.py and the energy-vs-frequency plots it draws
verification/    waveform-level checks: decoder, mutation test, reports, figures
slides/          make_slides.py, the progress-review deck, and its figures
CHECKS.md        how to re-derive every number and run every check
```

| file | role |
|---|---|
| `ecrl/ecrl_slowramp.sp` | ECRL inverter, slow-ramp input, data alternating every cycle |
| `ecrl/run_ecrl_slowramp_sweep.sh` | 6 widths x 7 TPHASEs -> `ecrl/ecrl_slowramp_sweep.csv` |
| `2lal/make_2lal_ring.py` | generates `2lal/2LAL_inverter_ring.sp` (edit this, not the deck) |
| `2lal/run_2lal_sweep.sh` | same grid -> `2lal/2lal_inverter_sweep.csv` |
| `plots/make_plots.py` | CSVs -> PNG plots and ngspice `.cir` plot decks |
| `verification/verify_all.sh` | waveform dump + decode + mutation test |
| `slides/make_slides.py` | builds `slides/ECRL_2LAL_Progress_Review.pptx` |

## Quick start

Linux or WSL with `ngspice`, `python3` and `gnuplot`, plus a sky130A PDK
install (`link_pdk.sh` defaults to `~/.volare/sky130A`; pass another path if
yours lives elsewhere):

    models/link_pdk.sh                     # once: point models/ at ~/.volare/sky130A
    ecrl/run_ecrl_slowramp_sweep.sh        # ~3 min
    2lal/run_2lal_sweep.sh                 # ~5 min
    python3 plots/make_plots.py
    verification/verify_all.sh            # ~3 min

Every sweep point is checked (logic correct, circuit settled, simulator used
the requested W and TPHASE) before its CSV row is written; a failure stops the
sweep.  `CHECKS.md` explains every check and how far each one can be trusted.

## Current results (W = 1 um, energy per operation, fJ)

| TPHASE | f_tr | ECRL | 2LAL |
|---|---|---|---|
| 1 ns | 1000 MHz | 54.69 | 46.10 |
| 2 ns | 500 MHz | 39.82 | 26.49 |
| 5 ns | 200 MHz | 27.32 | 11.93 |
| 10 ns | 100 MHz | 21.66 | 6.29 |
| 20 ns | 50 MHz | 17.83 | 3.27 |
| 50 ns | 20 MHz | 14.37 | 1.44 |
| 100 ns | 10 MHz | 12.46 | 0.93 |

From `ecrl/ecrl_slowramp_sweep.csv` and `2lal/2lal_inverter_sweep.csv`.
ECRL carries one gate (4 FETs); 2LAL one quad-rail column (16 FETs) inside a
metered 8-stage ring.  Plots: `plots/ecrl_vs_2lal_W1.0.png`.

## Known issue

`slides/` predates the 2LAL ring fix.  The slides that report 2LAL energy
(2LAL vs frequency, the head-to-head plot, the numbers table, and the
provenance example `2.16179e-14 J` on the verification slide) still quote
the open-chain values (e.g. 44.05 fJ at 10 MHz, "ECRL wins 3.5x at low
frequency"), and `slides/figs/2lal_energy_vs_ftr.png` and
`slides/figs/ecrl_vs_2lal_W1.0*.png` are the old plots.  The CSVs and
`plots/` above are current.  The waveform slides (ECRL, and 2LAL slide 19)
are current.

The gnuplot scripts in `slides/figs/*.gp` point at the original author's
scratch files (`/home/madhav/...`, `/tmp/...`), so they record how those
figures were drawn but do not rerun as-is.  The waveform figures are
reproducible with `verification/verify_all.sh`.

## License

Apache 2.0, see `LICENSE`.
