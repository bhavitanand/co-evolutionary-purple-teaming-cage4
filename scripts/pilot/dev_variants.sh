#!/usr/bin/env bash
# DEV runs (protocol: tune on dev seeds only). 3 Blue-side variants x dev seeds 10-14, condition coevo, 4B, 4 parallel runs.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
run() { v=$1; seed=$2; shift 2
  [ "$v" = coverage ] && export BLUE_COVERAGE_HINT=1
  $PY scripts/pilot/run_coevo.py --condition coevo --seeds $seed --rounds 8 --hint --dev "$@" --out-dir results/pilot_dev/$v >> results/pilot_dev/log_$v.log 2>&1; }
export -f run; export PY
mkdir -p results/pilot_dev
for seed in 10 11 12 13 14; do
  for v in base cap20 coverage; do echo "$v $seed"; done
done | xargs -P 4 -L 1 bash -c 'v=$0; s=$1; extra=""; [ "$v" = cap20 ] && extra="--max-active 20"; run $v $s $extra'
echo "$(date +%H:%M:%S) dev variants done"
