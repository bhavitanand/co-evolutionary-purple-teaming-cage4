#!/usr/bin/env bash
# DEV screen for item 8 (counts and time windows in the rule language): coevo, variant agg, dev seeds 10-14, runs after dev_variants2.sh finishes.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
until grep -q "dev variants2 done" results/pilot_dev_wait2.log 2>/dev/null; do sleep 60; done
mkdir -p results/pilot_dev
for seed in 10 11 12 13 14; do echo $seed; done | xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant agg --out-dir results/pilot_dev/agg >> results/pilot_dev/log_agg.log 2>&1'
echo "$(date +%H:%M:%S) dev agg done"
