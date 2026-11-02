#!/usr/bin/env bash
# FINAL run of the variant chosen on dev seeds (cap20 = --max-active 20): seeds 0-9, three conditions, then ONE test scoring.
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
for c in coevo llm_fixed_red coevo_nofeedback; do for s in 0 1 2 3 4 5 6 7 8 9; do echo "$c $s"; done; done | \
  xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition $0 --seeds $1 --rounds 8 --hint --max-active 20 --out-dir results/pilot_cap20 >> results/pilot_cap20/log_$0.log 2>&1'
echo "$(date +%H:%M:%S) cap20 training done"
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_cap20 --md results/pilot_cap20/results.md --out results/pilot_cap20/results.json > results/pilot_cap20/score.log 2>&1
echo "$(date +%H:%M:%S) cap20 scored"
