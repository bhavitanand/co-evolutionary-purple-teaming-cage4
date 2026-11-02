#!/usr/bin/env bash
# Helper for the cap-20 queue: stop once coevo + llm_fixed_red (20 runs) are done.
cd "$(dirname "$0")/../.."
PY=../.venv-cyborg/Scripts/python.exe
n() { ls results/pilot_cap20/rules 2>/dev/null | grep -cE '^(coevo|llm_fixed_red)_seed'; }
until [ "$(n)" -ge 20 ]; do sleep 20; done
for p in $(ps -W | grep -iE 'bash|python' | awk '{print $4}'); do :; done
powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'final_cap20|pilot_cap20' -and \$_.CommandLine -notmatch 'cap20_short' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
rm -f results/pilot_cap20/rules/coevo_nofeedback_seed*.json
echo "$(date +%H:%M:%S) cap20 queue cut at 20 runs"
$PY scripts/pilot/eval_rules.py --score --out-dir results/pilot_cap20 --md results/pilot_cap20/results.md --out results/pilot_cap20/results.json > results/pilot_cap20/score.log 2>&1
echo "$(date +%H:%M:%S) cap20 short scored"
