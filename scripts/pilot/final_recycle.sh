#!/usr/bin/env bash
# FINAL run of the variant that passed the pre-registered dev rule: recycle, coevo, cap 12, 10 FRESH seeds (25-34), then ONE test scoring.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
mkdir -p results/pilot_recycle
cp -r results/pilot/test_events results/pilot_recycle/ 2>/dev/null
for s in 25 26 27 28 29 30 31 32 33 34; do echo $s; done | xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant recycle --out-dir results/pilot_recycle >> results/pilot_recycle/log_coevo.log 2>&1'
echo "$(date +%H:%M:%S) recycle final training done"
"$PY" scripts/pilot/eval_rules.py --score --out-dir results/pilot_recycle --md results/pilot_recycle/results.md --out results/pilot_recycle/results.json > results/pilot_recycle/score.log 2>&1
echo "$(date +%H:%M:%S) recycle final scored"
