#!/usr/bin/env bash
# Port-hopping Red (pre-registered in results/PREREG_porthop.md): coevo + variant porthop, seeds 35-44, then score on the test seeds.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
echo "$(date +%H:%M:%S) porthop start" >> results/porthop.log
for s in 35 36 37 38 39 40 41 42 43 44; do echo $s; done | PY=$PY xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant porthop --out-dir results/pilot_porthop >> results/pilot_porthop/log.log 2>&1'
echo "$(date +%H:%M:%S) porthop training done" >> results/porthop.log
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_porthop --md results/pilot_porthop/results.md --out results/pilot_porthop/results.json > results/pilot_porthop/score.log 2>&1
echo "$(date +%H:%M:%S) porthop done" >> results/porthop.log
