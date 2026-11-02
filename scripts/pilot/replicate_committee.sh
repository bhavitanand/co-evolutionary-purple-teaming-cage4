#!/usr/bin/env bash
# Replication batch for the committee analysis: coevo and llm_fixed_red, NEW seeds 15-24 (standard cap 12, same flags as the main runs), 4B.
# Dev-range seeds (run_coevo.py --dev allows 10-29); seeds 10-14 were used for the variant screen, 15-24 never used. Output: results/pilot_rep.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
mkdir -p results/pilot_rep
for s in 15 16 17 18 19 20 21 22 23 24; do echo "coevo $s"; echo "llm_fixed_red $s"; done | \
  xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition $0 --seeds $1 --rounds 8 --hint --dev --out-dir results/pilot_rep >> results/pilot_rep/log_$0.log 2>&1'
echo "$(date +%H:%M:%S) replication training done"
