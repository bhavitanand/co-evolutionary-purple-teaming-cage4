"""Fair-baseline and robustness checks on the cached events (CPU only; run with the .venv-cyborg python).

1. Reference points: alert on everything, alert on nothing (shows how much of "precision" is just the attacker share of events).
2. Tuned static: the 10 hand-written rules, greedily pruned on TRAINING-seed events (seeds 0-9, same seeds the LLM runs trained on).
3. Learned baseline without an LLM: greedy rule induction (field = value conjunctions of up to two fields) on the same training events,
   at rule budgets 12 (the per-agent cap) and 60 (all five agents' caps), written in the same rule language and scored by the same executor.
4. All conditions again with the enriched fields blanked out (protocol, service_name, process_name, parent_process, privilege are
   invented by the telemetry bridge for most events): what is left when only truly native fields are visible.
5. Prevalence-adjusted precision (attackers are ~84% of native test events, so raw precision is flattered).
Outputs results/pilot_baselines/baselines.json and baselines.md.  Scoring: seen test episodes (40), native events.
"""
from __future__ import annotations

import copy
import gzip
import itertools
import json
import pathlib
import random
import statistics as st
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))
from src.loop.coevo import apply_rules, score  # noqa: E402
from src.rules.loader import load_rules  # noqa: E402
from src.rules.schema import Rule  # noqa: E402

OUT = ROOT / "results/pilot_baselines"
BLUE = [f"blue_agent_{i}" for i in range(5)]
SEEN = ["cage4_default", "aggressive", "stealthy", "deception_aware"]
FEATURES = ["dst_port", "is_decoy", "protocol", "service_name", "process_name", "parent_process", "privilege", "zone", "subnet"]
ENRICHED = ["protocol", "service_name", "process_name", "parent_process", "privilege"]


def load_eps(folder, reds, seeds):
    out = []
    for red in reds:
        for s in seeds:
            with gzip.open(folder / f"{red}_s{s}.json.gz", "rt", encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def strip(eps):
    """Copy of the episodes with every enriched field set to None (the executor treats None as 'not present')."""
    out = []
    for ep in eps:
        ep2 = dict(ep)
        evs = []
        for e in ep["events"]:
            e2 = dict(e)
            for f in e.get("enriched_fields") or []:
                e2[f] = None
            evs.append(e2)
        ep2["events"] = evs
        out.append(ep2)
    return out


def run_of(path):
    d = json.loads(path.read_text(encoding="utf-8-sig"))["rules"]
    return {a: [Rule.from_dict(r) for r in rs] for a, rs in d.items()}


def load_runs(cond, folders=("results/pilot",)):
    runs = []
    for d in folders:
        for f in sorted((ROOT / d / "rules").glob(f"{cond}_seed*.json")):
            runs.append(run_of(f))
    return runs


def uniform(rules):
    return {a: [Rule.from_dict({**r.to_dict(), "agent_id": a.replace("blue_agent_", "blue_")}) for r in rules] for a in BLUE}


def evaluate(run, eps):
    acc = {"precision": [], "recall": [], "fpr": []}
    for ep in eps:
        sc = score(ep["events"], apply_rules(ep["events"], run), ep["last_step"])["native"]
        for m in acc:
            if sc[m] is not None:
                acc[m].append(sc[m])
    r = {m: (st.mean(v) if v else float("nan")) for m, v in acc.items()}
    r["bal_acc"] = (r["recall"] + 1 - r["fpr"]) / 2
    for pi in (0.05, 0.01):
        d = r["recall"] * pi + r["fpr"] * (1 - pi)
        r[f"prec_at_{int(pi * 100)}pct"] = r["recall"] * pi / d if d > 0 else float("nan")
    return r


def boot(vals, n=4000, seed=0):
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return st.mean(vals), ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def n_rules(run):
    return st.mean(len(rs) for rs in run.values())


# ---------------------------------------------------------------- non-LLM baselines (fit on training events only)
def all_events(eps):
    return [e for ep in eps for e in ep["events"]]


def learn_rules(train_eps, budget, lam=5.0, min_prec=0.9, min_support=15):
    """Greedy set cover over conjunctions of up to two field=value conditions inside one event category."""
    evs = all_events(train_eps)
    y = np.array([e["label_red"] for e in evs], dtype=bool)
    cands = []  # (category, ((field, value), ...), mask)
    for cat in sorted({e["category"] for e in evs}):
        idx = np.array([e["category"] == cat for e in evs])
        singles = []
        for f in FEATURES:
            vals = {}
            for i in np.flatnonzero(idx):
                v = evs[i].get(f)
                if v is not None:
                    vals.setdefault(v, []).append(i)
            for v, ii in vals.items():
                if len(ii) >= min_support:
                    m = np.zeros(len(evs), dtype=bool)
                    m[ii] = True
                    singles.append(((f, v), m))
        for (c, m) in singles:
            cands.append((cat, (c,), m))
        for (c1, m1), (c2, m2) in itertools.combinations(singles, 2):
            if c1[0] != c2[0]:
                m = m1 & m2
                if m.sum() >= min_support:
                    cands.append((cat, (c1, c2), m))
    covered = np.zeros(len(evs), dtype=bool)
    chosen = []
    for _ in range(budget):
        best, best_gain = None, 0.0
        for cat, conds, m in cands:
            hits = m.sum()
            if hits == 0 or (m & y).sum() / hits < min_prec:
                continue
            gain = (m & y & ~covered).sum() - lam * (m & ~y & ~covered).sum()
            if gain > best_gain:
                best, best_gain = (cat, conds, m), gain
        if best is None:
            break
        chosen.append(best)
        covered |= best[2]
    rules = []
    for k, (cat, conds, m) in enumerate(chosen):
        sel = {f: v for f, v in conds}
        rules.append(Rule.from_dict({
            "rule_id": f"learn_{k:02d}", "round": 0, "agent_id": "blue_agent_0", "title": f"Learned: {cat} " + " & ".join(f"{f}={v}" for f, v in conds),
            "level": "medium", "logsource": {"category": cat}, "detection": {"sel": sel, "condition": "sel"},
            "confidence": 0.5, "rationale": f"Greedy rule induction on training events ({int(m.sum())} training hits)."}))
    return rules


def tune_static(train_eps, rules):
    """Forward selection over the hand-written rules on training events, objective recall minus FPR (native)."""
    chosen, best = [], -1.0
    pool = list(rules)
    while pool:
        cand = None
        for r in pool:
            j = evaluate(uniform(chosen + [r]), train_eps)
            v = j["recall"] - j["fpr"]
            if v > best + 1e-9 and (cand is None or v > cand[1]):
                cand = (r, v)
        if cand is None:
            break
        chosen.append(cand[0])
        pool.remove(cand[0])
        best = cand[1]
    return chosen


def alert_all_rules():
    cats = ["network_connection", "process_creation"]
    return [Rule.from_dict({"rule_id": f"all_{c}", "round": 0, "agent_id": "blue_agent_0", "title": "alert on all " + c, "level": "low",
                            "logsource": {"category": c}, "detection": {"s": {"is_decoy": [True, False]}, "condition": "s"},
                            "confidence": 0.1, "rationale": "reference"}) for c in cats]


def main():
    test = load_eps(ROOT / "results/pilot/test_events", SEEN, range(100, 110))
    test_s = strip(test)
    unseen = load_eps(ROOT / "results/pilot/test_events", ["hit_and_run"], range(100, 110))
    train = load_eps(OUT / "train_events", SEEN, range(10))
    train_s = strip(train)
    base = [e for ep in test for e in ep["events"] if e["provenance"] != "synthetic"]
    prev = st.mean(e["label_red"] for e in base)
    print(f"attacker share of native test events: {prev:.3f}", flush=True)

    static = load_rules(str(ROOT / "configs" / "static_blue_rules.json"))
    res = {"attacker_share_native_test": prev}
    sets = {}  # name -> (label, run on full events, run fitted on stripped events or None)
    sets["alert_all"] = ("Alert on every event (reference)", uniform(alert_all_rules()), None)
    sets["static"] = ("Static, 10 hand-written rules", uniform(static), None)
    tuned = tune_static(train, static)
    sets["static_tuned"] = (f"Static, pruned on training seeds ({len(tuned)} of 10 kept)", uniform(tuned), None)
    tuned_s = tune_static(train_s, static)
    for b in (12, 60):
        full = learn_rules(train, b)
        strp = learn_rules(train_s, b)
        sets[f"learned{b}"] = (f"Learned rules (no LLM), budget {b} ({len(full)} found)", uniform(full), uniform(strp))
        (OUT / f"learned{b}.json").write_text(json.dumps([r.to_dict() for r in full], indent=1), encoding="utf-8")
    sets["static_tuned"] = (sets["static_tuned"][0], sets["static_tuned"][1], uniform(tuned_s))
    sets["static"] = (sets["static"][0], sets["static"][1], sets["static"][1])
    sets["alert_all"] = (sets["alert_all"][0], sets["alert_all"][1], None)

    rows = []

    def add(name, label, run, run_for_stripped):
        full = evaluate(run, test)
        un = evaluate(run, unseen)
        stripped = evaluate(run_for_stripped, test_s) if run_for_stripped is not None else None
        rows.append((name, label, n_rules(run), full, un, stripped))
        print(label, f"rules/agent {n_rules(run):.1f}", {k: round(v, 3) for k, v in full.items()}, flush=True)

    for name, (label, run, run_s) in sets.items():
        add(name, label, run, run_s if run_s is not None else (run if name != "alert_all" else None))

    # LLM conditions: per-run results, mean and bootstrap over runs
    conds = {"random_rules": (("results/pilot",), "Random exemplar rules"), "llm_fixed_red": (("results/pilot",), "LLM vs fixed Red"),
             "coevo_nofeedback": (("results/pilot",), "LLM, no feedback"), "coevo": (("results/pilot",), "LLM, co-evolved")}
    llm = {}
    for cond, (folders, label) in conds.items():
        runs = load_runs(cond, folders)
        per = [(evaluate(r, test), evaluate(r, unseen), evaluate(r, test_s), n_rules(r)) for r in runs]
        llm[cond] = per
        mean = lambda i, m: st.mean(p[i][m] for p in per)
        rows.append((cond, f"{label}", st.mean(p[3] for p in per),
                     {m: mean(0, m) for m in per[0][0]}, {m: mean(1, m) for m in per[0][1]}, {m: mean(2, m) for m in per[0][2]}))
        print(label, "rules/agent %.1f" % rows[-1][2], {k: round(v, 3) for k, v in rows[-1][3].items()}, "stripped", {k: round(v, 3) for k, v in rows[-1][5].items()}, flush=True)

    # best-of comparisons: is a single LLM run better than the learned baseline at the same budget? (per-run recall at matched FPR)
    res["rows"] = [dict(name=n, label=l, rules_per_agent=r, full=f, unseen=u, stripped=s) for n, l, r, f, u, s in rows]
    res["llm_runs"] = {c: [dict(full=p[0], unseen=p[1], stripped=p[2], rules=p[3]) for p in per] for c, per in llm.items()}
    res["ci"] = {c: {m: boot([p[0][m] for p in per]) for m in ("recall", "fpr", "precision")} for c, per in llm.items()}
    (OUT / "baselines.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    def f(x):
        return "n/a" if x is None else f"{x:.3f}"

    L = ["# Fair baselines and robustness checks", "",
         f"Attacker events are {prev:.1%} of native test events, so raw precision is flattered. `Prec@1%` is precision if attackers were 1% of events (computed from recall and FPR).",
         "Scored on the 40 seen test episodes, native events; LLM rows are means over runs; `unseen` is hit_and_run (10 episodes).", "",
         "| System | rules/agent | recall | FPR | precision | balanced acc | Prec@1% | recall (unseen) | FPR (unseen) | recall, no enriched fields | FPR, no enriched fields |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, l, r, fl, un, sp in rows:
        L.append(f"| {l} | {r:.1f} | {f(fl['recall'])} | {f(fl['fpr'])} | {f(fl['precision'])} | {f(fl['bal_acc'])} | {f(fl['prec_at_1pct'])} | {f(un['recall'])} | {f(un['fpr'])} | "
                 f"{f(sp['recall']) if sp else 'n/a'} | {f(sp['fpr']) if sp else 'n/a'} |")
    L += ["", "95% bootstrap intervals over the ten training runs (full-field scoring): ", ""]
    for c, ci in res["ci"].items():
        L.append(f"- {c}: " + "; ".join(f"{m} {v[0]:.3f} [{v[1]:.3f}, {v[2]:.3f}]" for m, v in ci.items()))
    L += ["", "Pruned static rules kept: " + ", ".join(r.rule_id for r in tuned), "Learned (budget 12): " + "; ".join(r.title for r in learn_rules(train, 12))]
    (OUT / "baselines.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
