#!/bin/bash
# ============================================================
# Point models/sky130-ngspice-models at a sky130A PDK install.
#
# Every deck reaches the device models through this one link:
#   ../models/sky130_01v8_tt_fast.spice  -> ./sky130-ngspice-models/...
#   ../../models/sky130-ngspice-models/libs.tech/ngspice/sky130.lib.spice
# It is machine-specific, so it is not in git.  Run once per checkout:
#
#   models/link_pdk.sh                    # uses $PDK_ROOT/sky130A,
#                                         # default ~/.volare/sky130A
#   models/link_pdk.sh /path/to/sky130A   # or name it explicitly
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

PDK="${1:-${PDK_ROOT:-$HOME/.volare}/sky130A}"
NEED="libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice"

[ -f "$PDK/$NEED" ] || { echo "FAIL: $PDK/$NEED not found -- is $PDK a sky130A install?" >&2; exit 1; }
ln -sfn "$PDK" sky130-ngspice-models
echo "models/sky130-ngspice-models -> $PDK"
