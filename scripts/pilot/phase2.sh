#!/usr/bin/env bash
# Phase 2 (after seeds 5-9 finish): train coevo_aware (Red also sees which of its actions were caught) on seeds 0-9, then score everything.
cd "$(dirname "$0")/../.."
until [ "$(ls results/pilot/rules/coevo_seed*.json 2>/dev/null | wc -l)" -ge 10 ] && [ "$(ls results/pilot/rules/coevo_nofeedback_seed*.json 2>/dev/null | wc -l)" -ge 10 ] && [ "$(ls results/pilot/rules/llm_fixed_red_seed*.json 2>/dev/null | wc -l)" -ge 10 ]; do sleep 120; done
echo "$(date +%H:%M:%S) phase1 done, starting coevo_aware"
for part in "0 1 2 3 4" "5 6 7 8 9"; do
  ../.venv-cyborg/Scripts/python.exe scripts/pilot/run_coevo.py --condition coevo_aware --seeds $part --rounds 8 --hint > results/pilot/run3_aware_${part// /}.log 2>&1 &
done
wait
echo "$(date +%H:%M:%S) coevo_aware done"
../.venv-cyborg/Scripts/python.exe scripts/pilot/eval_rules.py --score --md results/pilot/results_final.md --out results/pilot/results_final.json > results/pilot/score_final.log 2>&1
echo "$(date +%H:%M:%S) scored final"
