#!/usr/bin/env bash
# DEV screen 2 (items 3, 4, 7): coevo with variant recycle / richfb / promptred on DEV seeds 10-14, 4B, cap 12, 4 parallel runs.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
mkdir -p results/pilot_dev
for seed in 10 11 12 13 14; do
  for v in recycle richfb promptred; do echo "$v $seed"; done
done | xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $1 --rounds 8 --hint --dev --variant $0 --out-dir results/pilot_dev/$0 >> results/pilot_dev/log_$0.log 2>&1'
echo "$(date +%H:%M:%S) dev variants2 done"
