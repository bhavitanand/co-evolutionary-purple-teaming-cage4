#!/usr/bin/env bash
# Long-horizon learned-Red test (pre-registered in results/PREREG_long_horizon.md): 4B server -> dev screen (seeds 10-14, 16 rounds, fixed Red vs
# Thompson Red) -> rule -> if pass, final seeds 35-44 for both conditions and scoring on the test seeds.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
L=results/overnight2.log
echo "$(date +%H:%M:%S) start 4B server" >> $L
powershell -NoProfile -File scripts/pilot/start_4b.ps1 >> $L 2>&1
mkdir -p results/pilot_dev results/pilot_long
{ for s in 10 11 12 13 14; do echo "llm_fixed_red $s long_fixed base"; echo "coevo_evasive $s long_thompson thompson"; done; } | \
  PY=$PY xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition $0 --seeds $1 --rounds 16 --hint --dev --variant $3 --out-dir results/pilot_dev/$2 >> results/pilot_dev/log_long.log 2>&1' 
echo "$(date +%H:%M:%S) dev long done" >> $L
if $PY scripts/pilot/long_rule.py >> $L 2>&1; then
  echo "$(date +%H:%M:%S) start final long" >> $L
  { for s in 35 36 37 38 39 40 41 42 43 44; do echo "llm_fixed_red $s base"; echo "coevo_evasive $s thompson"; done; } | \
    PY=$PY xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition $0 --seeds $1 --rounds 16 --hint --dev --variant $2 --out-dir results/pilot_long >> results/pilot_long/log.log 2>&1'
  $PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_long --md results/pilot_long/results.md --out results/pilot_long/results.json > results/pilot_long/score.log 2>&1
  echo "$(date +%H:%M:%S) final long scored" >> $L
fi
echo "$(date +%H:%M:%S) overnight2 done" >> $L
