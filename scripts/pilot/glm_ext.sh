#!/usr/bin/env bash
# Extend the GLM confirmatory check from 3 to 10 runs per condition (seeds 3-9), then rescore all 30 rule sets.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
for c in llm_fixed_red coevo_nofeedback coevo; do
  extra=""; [ "$c" != "llm_fixed_red" ] && extra=""
  $PY scripts/pilot/run_coevo.py --condition $c --seeds 3 4 5 6 7 8 9 --rounds 8 --hint --model glm-4.7-flash --out-dir results/pilot_glm >> results/pilot_glm/run_${c}_ext.log 2>&1 &
done
wait
echo "$(date +%H:%M:%S) glm ext training done"
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_glm --md results/pilot_glm/results_n10.md --out results/pilot_glm/results_n10.json > results/pilot_glm/score_n10.log 2>&1
echo "$(date +%H:%M:%S) glm ext scored"
