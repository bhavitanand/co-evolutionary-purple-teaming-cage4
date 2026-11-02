#!/usr/bin/env bash
# Stronger Red (scripted EvasiveRed): train coevo_evasive and evasive_nofeedback (4B, seeds 0-9), cache plan-library test events, score.
# Resumable: re-run it; finished seeds are skipped. Needs the 4B llama-server on :8080.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
M=qwen3-4b-instruct-2507-q4_k_m
$PY scripts/pilot/eval_rules.py --cache --reds plan_stealth_probe plan_stealth_push plan_loud_push plan_mixed > results/pilot/cache_plans.log 2>&1 &
for c in coevo_evasive evasive_nofeedback; do
  $PY scripts/pilot/run_coevo.py --condition $c --seeds 0 1 2 3 4 --rounds 8 --hint --model $M >> results/pilot/run_${c}_a.log 2>&1 &
  $PY scripts/pilot/run_coevo.py --condition $c --seeds 5 6 7 8 9 --rounds 8 --hint --model $M >> results/pilot/run_${c}_b.log 2>&1 &
done
wait
echo "$(date +%H:%M:%S) phase3 training done"
$PY scripts/pilot/eval_rules.py --score --md results/pilot/results_evasive.md --out results/pilot/results_evasive.json > results/pilot/score_evasive.log 2>&1
echo "$(date +%H:%M:%S) phase3 scored"
