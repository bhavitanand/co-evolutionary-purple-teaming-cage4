#!/usr/bin/env bash
# Wait for the GLM confirmatory runs (3 conditions x 3 seeds), then score them on the cached test episodes.
cd "$(dirname "$0")/../.."
until [ "$(ls results/pilot_glm/rules/*_seed*.json 2>/dev/null | wc -l)" -ge 9 ]; do sleep 120; done
echo "$(date +%H:%M:%S) glm training done"
../.venv-cyborg/Scripts/python.exe scripts/pilot/eval_rules.py --score --out-dir results/pilot_glm --md results/pilot_glm/results.md --out results/pilot_glm/results.json > results/pilot_glm/score.log 2>&1
echo "$(date +%H:%M:%S) glm scored"
