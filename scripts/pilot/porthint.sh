#!/usr/bin/env bash
# Port-hopping Red + 'porthint' prompt note (pre-registered in results/PREREG_porthint.md), seeds 35-44, then score on the test seeds.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
mkdir -p results/pilot_porthint && cp -r results/pilot/test_events results/pilot_porthint/
echo "$(date +%H:%M:%S) porthint start" >> results/porthint.log
for s in 35 36 37 38 39 40 41 42 43 44; do echo $s; done | PY=$PY xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant porthop+porthint --out-dir results/pilot_porthint >> results/pilot_porthint/log.log 2>&1'
echo "$(date +%H:%M:%S) porthint training done" >> results/porthint.log
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_porthint --md results/pilot_porthint/results.md --out results/pilot_porthint/results.json > results/pilot_porthint/score.log 2>&1
echo "$(date +%H:%M:%S) porthint done" >> results/porthint.log
