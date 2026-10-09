#!/bin/bash
# ============================================================
# All waveform-level verification in one go (~3 min):
#   1. run_waveforms.sh      dump ECRL / 2LAL waveforms        -> data/
#   2. check_waveforms.py    decode them, check inversion       -> waveform_report.txt, figures/
#   3. mutation_test_2lal.sh prove the deck's 96 checks can fail -> mutation_report.txt
# Stops at the first failure.  The sweeps have their own per-point
# checks (../ecrl/run_ecrl_slowramp_sweep.sh, ../2lal/run_2lal_sweep.sh).
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"
./run_waveforms.sh
python3 check_waveforms.py
./mutation_test_2lal.sh
echo "-> verification PASSED: see waveform_report.txt, mutation_report.txt, figures/"
