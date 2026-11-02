#!/usr/bin/env bash
# Overnight chain (3-Nov): (1) DEV screen of variant 'broad' on dev seeds 10-14 (4B); (2) if it passes the pre-set rule (recall >= base + 0.05 and FPR <= base + 0.01)
# run it FINAL on fresh seeds 35-44 and score once; (3) swap the server to GLM-4.7-Flash and extend the larger-model check to 10 runs per condition, rescore.
# Resumable: rerun to continue (finished seeds are skipped). Log: results/overnight.log
cd "$(dirname "$0")/../.."
export PY=../.venv-cyborg/Scripts/python.exe
log() { echo "$(date +%H:%M:%S) $*" >> results/overnight.log; }
mkdir -p results/pilot_dev results/pilot_broad
log "start dev broad"
for seed in 10 11 12 13 14; do echo $seed; done | xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant broad --out-dir results/pilot_dev/broad >> results/pilot_dev/log_broad.log 2>&1'
log "dev broad done"
../.venv/Scripts/python.exe scripts/pilot/dev_summary.py > /dev/null 2>&1
PASS=$(../.venv/Scripts/python.exe - <<'P'
import json, statistics as st
def m(v):
    per = {}
    for x in open(f"results/pilot_dev/{v}/train_log.jsonl", encoding="utf-8-sig"):
        r = json.loads(x)
        if r["round"] >= 7:
            n = r["scores"]["native"]; per.setdefault(r["seed"], []).append((n["recall"], n["fpr"] or 0.0))
    return st.mean(st.mean(a for a, _ in x) for x in per.values()), st.mean(st.mean(b for _, b in x) for x in per.values())
br, bf = m("base"); vr, vf = m("broad")
print("pass" if vr >= br + 0.05 and vf <= bf + 0.01 else "fail", f"broad {vr:.3f}/{vf:.3f} base {br:.3f}/{bf:.3f}")
P
)
log "dev rule: $PASS"
if [[ "$PASS" == pass* ]]; then
  cp -r results/pilot/test_events results/pilot_broad/ 2>/dev/null
  for s in 35 36 37 38 39 40 41 42 43 44; do echo $s; done | xargs -P 4 -L 1 bash -c '"$PY" scripts/pilot/run_coevo.py --condition coevo --seeds $0 --rounds 8 --hint --dev --variant broad --out-dir results/pilot_broad >> results/pilot_broad/log_coevo.log 2>&1'
  log "broad final training done"
  "$PY" scripts/pilot/eval_rules.py --score --out-dir results/pilot_broad --md results/pilot_broad/results.md --out results/pilot_broad/results.json > results/pilot_broad/score.log 2>&1
  log "broad final scored"
fi
log "start GLM swap"
powershell -NoProfile -File scripts/pilot/start_glm.ps1 >> results/overnight.log 2>&1
bash scripts/pilot/glm_ext.sh >> results/overnight.log 2>&1
log "overnight done"
