"""Pilot: train one condition of the co-evolution pilot on TRAINING seeds and save the final rule sets.

  llm_fixed_red      Blue = 5 LLM agents with feedback, Red = CAGE-4 default scripted Red (no self-play)
  coevo              Blue = 5 LLM agents with feedback, Red = LLM planner that adapts to being caught   (ours)
  coevo_nofeedback   as coevo, but Blue gets no performance feedback (ablation: is the feedback loop doing the work?)
  random_rules       Blue = random exemplar rules built from its own observed events (no LLM) + the same rule retirement;
                     Red = scripted default. Control for "any rule search with selection pressure".
Training seeds only (0-9). Final rules are scored frozen on test seeds by scripts/pilot/eval_rules.py.
Needs the CAGE-4 environment (.venv-cyborg) and, for LLM conditions, a running llama-server.
  python scripts/pilot/run_coevo.py --condition coevo --seeds 0 1 2 3 4 --rounds 8
"""
from __future__ import annotations

import argparse
import json
import os
import logging
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))

from src.agents.blue.agent import BlueLLMAgent  # noqa: E402
from src.agents.blue.llm_client import LlamaServerClient  # noqa: E402
from src.agents.red.evasive import EvasiveRed, ThompsonRed  # noqa: E402
from src.agents.red.llm_red import PlannedRed, RedMemory, RedPlanner  # noqa: E402
from src.loop.coevo import (BLUE_AGENTS, BlueTeam, EpisodePlayer, RetryClient, apply_rules, feedback_for, feedback_rich, observed_lines,  # noqa: E402
                            retire_weak_rules, rule_stats, score)
from src.loop.real_episode import derive_env_seed  # noqa: E402
from src.rules.schema import Rule  # noqa: E402
from src.rules.validator import validate_rule_dict  # noqa: E402

log = logging.getLogger("pilot")
CONDITIONS = ("llm_fixed_red", "coevo", "coevo_nofeedback", "random_rules", "coevo_aware", "coevo_evasive", "evasive_nofeedback")
TRAIN_SEEDS = range(0, 10)


class _NoLLM:
    def generate(self, prompt, schema=None):
        raise RuntimeError("random_rules never calls an LLM")


def random_rules(agent: str, events: list[dict], rng: random.Random, rnd: int, n: int = 5) -> list[Rule]:
    """Exemplar rules: pick observed events of this zone and match their category plus 1-2 of their other visible values."""
    pool = [e for e in events if e.get("category")]
    out: list[Rule] = []
    for i in range(n):
        if not pool:
            break
        ev = rng.choice(pool)
        fields = [f for f in ("dst_port", "process_name", "parent_process", "privilege", "service_name", "is_decoy") if ev.get(f) not in (None, "")]
        pick = rng.sample(fields, k=min(len(fields), rng.choice((1, 2)))) if fields else []
        sel = {f: ev[f] for f in pick}
        det = {"sel": sel or {"category": ev["category"]}, "condition": "sel"}
        d = {"rule_id": f"{agent}_r{rnd}_{i}", "round": rnd, "agent_id": agent.replace("blue_agent_", "blue_"), "title": f"exemplar {ev['category']} {sorted(sel)}",
             "level": "medium", "logsource": {"category": ev["category"]}, "detection": det, "confidence": 0.3,
             "rationale": "random exemplar of an observed event"}
        if validate_rule_dict(d).valid:
            out.append(Rule.from_dict(d))
    return out


def run_seed(args, cond: str, seed: int, out_dir: pathlib.Path, player: EpisodePlayer) -> None:
    rules_path = out_dir / "rules" / f"{cond}_seed{seed}.json"
    if rules_path.exists():
        log.info("%s seed %d already done, skipping", cond, seed)
        return
    use_llm_blue = cond != "random_rules"
    scripted_red = cond in ("coevo_evasive", "evasive_nofeedback")  # stronger Red: scripted, rewarded for evading
    adaptive_red = scripted_red or cond in ("coevo", "coevo_nofeedback", "coevo_aware")
    use_feedback = cond in ("llm_fixed_red", "coevo", "coevo_aware", "coevo_evasive")
    base = 100000 + 1000 * seed
    agents = {a: BlueLLMAgent(a.replace("blue_agent_", "blue_"), RetryClient(LlamaServerClient(args.url, model=args.model, temperature=args.temperature, seed=base + i,
                                                              max_tokens=1000)) if use_llm_blue else _NoLLM(),
                              max_rules=5, max_repairs=1, max_active=args.max_active, nested_schema=True, prompt_hint=args.hint)
              for i, a in enumerate(BLUE_AGENTS)}
    team = BlueTeam(agents)
    red_client = RetryClient(LlamaServerClient(args.url, model=args.model, temperature=0.7, seed=base, max_tokens=400)) if adaptive_red and not scripted_red else None
    variants = set(args.variant.split("+"))
    planner = ((ThompsonRed(seed) if 'thompson' in variants else EvasiveRed(seed)) if scripted_red else RedPlanner(red_client, RedMemory(), coupled=True, react="promptred" in variants)) if adaptive_red else None
    silent: dict[str, int] = {}  # variant 'recycle': consecutive rounds each rule stayed silent
    fb_fn = feedback_rich if "richfb" in variants else feedback_for
    rng = random.Random(seed)
    feedback: dict[str, list[str]] = {}
    last_alerts: dict[str, list[dict]] = {}
    last_events: dict[str, list[dict]] = {}
    log_file = out_dir / "train_log.jsonl"
    # Warm-up: one episode against CAGE-4's default Red so round 1 can already see the zone's telemetry (no labels used).
    warm = player.play("cage4_default", derive_env_seed(seed, 0, 0), steps=args.steps)
    for e in warm["events"]:
        last_events.setdefault(e["blue_agent"], []).append(e)
    feedback = {a: observed_lines(last_events.get(a, [])) for a in BLUE_AGENTS}

    prev_caught = 0.0  # variant 'porthop': share of Red activity caught last round
    for rnd in range(1, args.rounds + 1):
        t0 = time.perf_counter()
        # ---- Blue phase: propose rules from last round's feedback
        if use_llm_blue:
            blue_meta = team.propose(rnd, feedback, last_alerts if use_feedback else {})
            if "recycle" in variants and use_feedback:  # drop NEW rules that were mostly benign on last round's training events
                pre = 0
                for a, ag in agents.items():
                    fresh = [r for r in ag.active_rules if r.round == rnd]
                    prev = last_events.get(a, [])
                    if fresh and prev:
                        st_ = rule_stats(prev, apply_rules(prev, {a: fresh}))
                        bad = {rid for rid, s_ in st_.items() if s_["fires"] >= 3 and s_["red"] / s_["fires"] < 0.3}
                        if bad:
                            ag.active_rules = [r for r in ag.active_rules if r.rule_id not in bad]
                            pre += len(bad)
                blue_meta["prefiltered"] = pre
        else:
            added = 0
            for a, ag in agents.items():
                new = random_rules(a, last_events.get(a, []), rng, rnd)
                ag.active_rules = (ag.active_rules + new)[-args.max_active:]
                added += len(new)
            blue_meta = {"new_rules": added, "llm_calls": 0}
        # ---- Red phase
        plan_info = {"red": "cage4_default"}
        if adaptive_red:
            if red_client is not None:
                red_client.seed = base + rnd
            decision = planner.plan({"round": rnd})
            plan_info = {"red": "evasive" if scripted_red else "llm_planner", "plan_name": decision.get("plan_name"), "source": decision["source"], "plan": decision["plan"],
                         "red_llm_s": decision["llm_latency_s"]}
            ep = player.play(PlannedRed, derive_env_seed(seed, rnd, 0), steps=args.steps, plan=decision["plan"])
        else:
            ep = player.play("cage4_default", derive_env_seed(seed, rnd, 0), steps=args.steps)
        hopped = False
        if "porthop" in variants and rnd >= 2 and prev_caught >= 0.3:  # variant 'porthop': Red evades by moving its network events to other ports
            hop_rng = random.Random(derive_env_seed(seed, rnd, 1))
            for e in ep["events"]:
                if e["provenance"] == "native" and e["label_red"] in (1, "1") and e.get("dst_port") is not None:
                    e["dst_port"] = hop_rng.randint(1024, 65535)
            hopped = True
        plan_info["hopped"] = hopped
        # ---- score the CURRENT rules on this round's episode
        rules_by_agent = team.rules()
        alerts = apply_rules(ep["events"], rules_by_agent)
        sc = score(ep["events"], alerts, ep["last_step"])
        prev_caught = sc["all"]["recall"] or 0.0
        # ---- feedback for the next round + rule retirement (training labels, training seeds only)
        dropped: list[str] = []
        by_agent_alerts: dict[str, list] = {a: [] for a in BLUE_AGENTS}
        by_agent_events: dict[str, list] = {a: [] for a in BLUE_AGENTS}
        owner = {e["event_id"]: e["blue_agent"] for e in ep["events"]}
        for e in ep["events"]:
            by_agent_events[e["blue_agent"]].append(e)
        for al in alerts:
            by_agent_alerts[owner[al.event_id]].append(al)
        for a in BLUE_AGENTS:
            feedback[a] = observed_lines(by_agent_events[a]) + (
                fb_fn(by_agent_events[a], by_agent_alerts[a], rules_by_agent[a]) if use_feedback else [])
            last_alerts[a] = [{"rule_id": x.rule_id, "host_id": x.host_id, "step": x.step, "level": x.level} for x in by_agent_alerts[a][:30]]
            st_a = rule_stats(by_agent_events[a], by_agent_alerts[a])
            dropped += retire_weak_rules(agents[a], st_a)
            if "recycle" in variants:  # retire rules that stayed silent two rounds in a row, which frees their slots
                gone = []
                for r in agents[a].active_rules:
                    silent[r.rule_id] = 0 if r.rule_id in st_a else silent.get(r.rule_id, 0) + 1
                    if silent[r.rule_id] >= 2:
                        gone.append(r.rule_id)
                if gone:
                    agents[a].active_rules = [r for r in agents[a].active_rules if r.rule_id not in gone]
                    dropped += gone
        last_events = by_agent_events
        # ---- Red learns how much of its activity was caught
        if adaptive_red and decision["plan"]:
            outcome = dict(ep["red_outcome"])
            red_events = sc["all"]["tp"] + sc["all"]["fn"]
            outcome["caught_pct"] = round(100 * sc["all"]["tp"] / red_events) if red_events else 0
            if cond == "coevo_aware":  # Red also learns WHICH of its actions were caught (counts only, from training labels)
                alerted_ids = {a_.event_id for a_ in alerts}
                tot: dict[str, int] = {}
                hit: dict[str, int] = {}
                for e in ep["events"]:
                    if e["label_red"] == 1:
                        tot[e["source_action"]] = tot.get(e["source_action"], 0) + 1
                        hit[e["source_action"]] = hit.get(e["source_action"], 0) + (e["event_id"] in alerted_ids)
                outcome["caught_by_action"] = {k: round(100 * hit[k] / tot[k]) for k in sorted(tot)}
            planner.update({"round": rnd, "plan": decision["plan"], "outcome": outcome})
        rec = {"condition": cond, "seed": seed, "round": rnd, "blue": blue_meta, "active_rules": sum(len(v) for v in rules_by_agent.values()),
               "retired": dropped, "scores": sc, "red_actions": dict(ep["red_actions"]), "red_success": dict(ep["red_success"]),
               "red_forced_sleep": ep.get("red_forced_sleep", 0), "seconds": round(time.perf_counter() - t0, 1), **plan_info}
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        a = sc["all"]
        log.info("%s seed %d round %d: rules %d, P %s R %s FPR %s | native R %s | %.0fs", cond, seed, rnd, rec["active_rules"],
                 None if a["precision"] is None else round(a["precision"], 2), None if a["recall"] is None else round(a["recall"], 2),
                 None if a["fpr"] is None else round(a["fpr"], 2),
                 None if sc["native"]["recall"] is None else round(sc["native"]["recall"], 2), rec["seconds"])

    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps({"condition": cond, "seed": seed, "rounds": args.rounds, "model": args.model,
                                      "rules": {a: [r.to_dict() for r in ag.active_rules] for a, ag in agents.items()}}, indent=1),
                          encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--condition", required=True, choices=CONDITIONS)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="qwen3-4b-instruct-2507-q4_k_m")
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--hint", action="store_true", help="add the 'limits of the rule language' paragraph to the Blue prompt")
    ap.add_argument("--max-active", type=int, default=12, help="active rules kept per Blue agent")
    ap.add_argument("--out-dir", default="results/pilot")
    ap.add_argument("--variant", default="base", help="base, or one or more of recycle, richfb, promptred, agg joined by +")
    ap.add_argument("--dev", action="store_true", help="allow DEV seeds 10-19 (design iterations); test seeds 100-109 stay blocked")
    args = ap.parse_args()
    allowed = set(TRAIN_SEEDS) | (set(range(10, 50)) if args.dev else set())
    bad = [s for s in args.seeds if s not in allowed]
    if bad:
        raise SystemExit(f"seeds {bad} are not training seeds (0-9); test seeds 100-109 are for scripts/pilot/eval_rules.py")
    if "broad" in args.variant.split("+"):  # variant 'broad': prompt guidance toward simple, broad rules
        os.environ["BLUE_BROAD"] = "1"
    if "agg" in args.variant.split("+"):  # variant 'agg' (item 8): rules may use count-within-window aggregates
        os.environ["BLUE_AGG"] = "1"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    player = EpisodePlayer()
    try:
        for seed in args.seeds:
            run_seed(args, args.condition, seed, out_dir, player)
    finally:
        player.close()


if __name__ == "__main__":
    main()
