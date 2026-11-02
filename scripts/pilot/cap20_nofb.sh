#!/usr/bin/env bash
# Completes the cap-20 comparison: coevo_nofeedback, --max-active 20, seeds 0-9 (same settings as the other cap-20 conditions), then rescore the cap20 dir once.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
for s in 0 1 2 3 4 5 6 7 8 9; do echo $s; done | \
  xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo_nofeedback --seeds $0 --rounds 8 --hint --max-active 20 --out-dir results/pilot_cap20 >> results/pilot_cap20/log_coevo_nofeedback.log 2>&1'
echo "$(date +%H:%M:%S) cap20 nofeedback training done"
cp results/pilot_cap20/results.md results/pilot_cap20/results_2cond.md; cp results/pilot_cap20/results.json results/pilot_cap20/results_2cond.json
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_cap20 --md results/pilot_cap20/results.md --out results/pilot_cap20/results.json > results/pilot_cap20/score3.log 2>&1
echo "$(date +%H:%M:%S) cap20 nofeedback scored"
