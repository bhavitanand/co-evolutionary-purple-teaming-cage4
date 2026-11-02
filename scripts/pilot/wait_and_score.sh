#!/usr/bin/env bash
# Wait until every condition has finished all 5 training seeds, then score the frozen rules on the test episodes.
cd "$(dirname "$0")/../.."
n_expected=${1:-5}
for c in random_rules llm_fixed_red coevo_nofeedback coevo; do
  until [ "$(ls results/pilot/rules/${c}_seed*.json 2>/dev/null | wc -l)" -ge "$n_expected" ]; do sleep 60; done
  echo "$(date +%H:%M:%S) $c finished"
done
../.venv-cyborg/Scripts/python.exe scripts/pilot/eval_rules.py --score --md results/pilot/${2:-results.md} --out results/pilot/${3:-results.json} > results/pilot/score.log 2>&1
echo "$(date +%H:%M:%S) scored"
