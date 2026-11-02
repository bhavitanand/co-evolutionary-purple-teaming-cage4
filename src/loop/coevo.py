"""pilot co-evolution loop, detection layer (pilot study, Nov 2026).

What this is: the smallest honest version of Algorithm 1 that runs end to end on real CAGE-4 episodes.
  * Red: a scripted strategy, or the LLM planner of T20 (once per round) + its cheap FSM executor.
  * Blue: five LLM agents (one per CAGE-4 Blue agent), each writing Sigma-style rules once per round (Decision D1, mode B).
    The rules act as DETECTORS on the telemetry bridge's events; Blue's response playbook is NOT wired into CybORG here, so
    Blue does not change what Red can do. Red therefore adapts to *being caught*, not to being blocked.
  * Training signal: after each round, Blue is told (in words) how its rules did against ground truth (per-rule precision,
    attacker events no rule matched, benign events that fired); Red is told how much of its activity was caught. This uses
    labels, so it only ever happens on TRAINING episodes (tuning seeds). Final rule sets are evaluated frozen, with no
    feedback, on separate test seeds and Red strategies (src/loop/coevo_eval.py).
  * Rule retirement: after each round a rule that fired at least 3 times with under 30% of its alerts on attacker activity is
    dropped from the active set. This is part of the method (selection pressure on rules) and is logged.
Everything here is a pilot-scale design choice, documented in docs/pilot-method.md.
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Iterable

from CybORG import CybORG
from CybORG.Agents import EnterpriseGreenAgent, SleepAgent
from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator

from src.agents.blue.agent import BlueLLMAgent
from src.agents.red.llm_red import PlannedRed, outcome_from_stats
from src.agents.red.plan import RedPlan
from src.agents.red.scripted import ALL as RED_STRATEGIES
from src.bridge import SYNTHETIC_ACTIONS, GroundTruthLabeler, TelemetryBridge
from src.eval.metrics import evaluate_episode
from src.rules.executor import RuleExecutor
from src.rules.schema import VISIBLE_FIELDS, Rule

log = logging.getLogger(__name__)

BLUE_AGENTS = [f"blue_agent_{i}" for i in range(5)]
_NOT_A_RED_DECISION = {"Sleep", "RedSessionCheck"}
PATTERN_FIELDS = ("category", "dst_port", "service_name", "process_name", "parent_process", "privilege", "is_decoy", "zone")


class RetryClient:
    """Wraps an LLM client: llama-server sometimes answers HTTP 500 (grammar-constrained sampling) or times out under load.
    Retry with a different sampling seed; after the last attempt return an empty answer so the agent falls back to its old rules."""

    def __init__(self, inner: Any, attempts: int = 4):
        object.__setattr__(self, "inner", inner)
        object.__setattr__(self, "attempts", attempts)
        object.__setattr__(self, "failures", 0)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self.inner, name, value)

    def generate(self, prompt: str, schema: dict | None = None) -> tuple[str, dict[str, Any]]:
        import time
        base = self.inner.seed
        for k in range(self.attempts):
            try:
                self.inner.seed = base + 7919 * k
                return self.inner.generate(prompt, schema)
            except Exception as exc:  # noqa: BLE001
                object.__setattr__(self, "failures", self.failures + 1)
                log.warning("LLM call failed (attempt %d/%d): %s", k + 1, self.attempts, exc)
                time.sleep(3 * (k + 1))
            finally:
                self.inner.seed = base
        return "", {"latency_s": 0.0, "error": "all attempts failed"}


# --------------------------------------------------------------------------- episodes
class EpisodePlayer:
    """Plays full CAGE-4 episodes with a passive Blue and returns the bridge's labelled events (to_log dicts).
    One per process: the labeler patches CybORG for the whole process and PlannedRed keeps class-level state."""

    def __init__(self) -> None:
        self.labeler = GroundTruthLabeler()

    def close(self) -> None:
        self.labeler.uninstall()

    def play(self, red: str | type, env_seed: int, steps: int = 500, plan: dict[str, Any] | None = None,
             synthetic: bool = True) -> dict[str, Any]:
        """red: key of scripted.ALL, or the PlannedRed class (then `plan` is its round plan, None = scripted default)."""
        labeler = self.labeler.install()
        if red is PlannedRed:
            PlannedRed.reset_stats()
            PlannedRed.set_plan(RedPlan(**plan) if plan else None)
            red_cls = PlannedRed
        else:
            red_cls = RED_STRATEGIES[red]
        sg = EnterpriseScenarioGenerator(blue_agent_class=SleepAgent, green_agent_class=EnterpriseGreenAgent,
                                         red_agent_class=red_cls, steps=steps)
        env = CybORG(sg, "sim", seed=env_seed)
        env.reset()
        labeler.reset()
        bridge = TelemetryBridge(env_seed, labeler=labeler, synthetic=SYNTHETIC_ACTIONS if synthetic else ())
        blue = [a for a in env.agents if a.startswith("blue")]
        events: list[dict[str, Any]] = []
        log_pos, last_step = 0, 0
        for step in range(steps):
            env.step()
            obs = {}
            for a in blue:
                body = {k: v for k, v in env.get_observation(a).items() if k not in ("success", "action")}
                if body:
                    obs[a] = body
            new = labeler.action_log[log_pos:]
            log_pos = len(labeler.action_log)
            evs = bridge.step_events(step, obs, red_actions=new)
            if any(e.label_red is None for e in evs):
                raise RuntimeError(f"unlabelled event at env_seed {env_seed} step {step}")
            events += [e.to_log() for e in evs]
            last_step = step
            if env.environment_controller.determine_done():
                break
        actions = [r for r in labeler.action_log if r["action"] not in _NOT_A_RED_DECISION]
        out = {"events": events, "last_step": last_step, "red_actions": Counter(r["action"] for r in actions),
               "red_success": Counter(r["action"] for r in actions if str(r.get("success")).upper() == "TRUE")}
        if red is PlannedRed:
            out["red_outcome"] = outcome_from_stats(PlannedRed.stats)
            out["red_forced_sleep"] = PlannedRed.stats["forced_sleep"]
        return out


# --------------------------------------------------------------------------- scoring
def visible(ev: dict[str, Any]) -> dict[str, Any]:
    return {k: ev.get(k) for k in VISIBLE_FIELDS}


def apply_rules(events: list[dict[str, Any]], rules_by_agent: dict[str, list[Rule]]) -> list[Any]:
    """Run each Blue agent's rules on that agent's own events. Returns Alert objects (rule_id, event_id, ...)."""
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        by_agent[ev["blue_agent"]].append(ev)
    alerts: list[Any] = []
    for agent, evs in by_agent.items():
        rules = rules_by_agent.get(agent) or []
        if rules:
            alerts += RuleExecutor(rules).run(visible(e) for e in evs)
    return alerts


def score(events: list[dict[str, Any]], alerts: Iterable[Any], last_step: int) -> dict[str, Any]:
    """Episode metrics overall and split by provenance (the synthetic events are easy by construction: never pool them)."""
    alerted = sorted({a.event_id for a in alerts})
    slim = [{"event_id": e["event_id"], "step": e["step"], "label_red": e["label_red"], "provenance": e["provenance"]} for e in events]

    def one(subset: list[dict[str, Any]]) -> dict[str, Any]:
        ids = {e["event_id"] for e in subset}
        m = evaluate_episode(subset, [i for i in alerted if i in ids], last_step=last_step)
        return {"n_events": m.n_events, "tp": m.tp, "fp": m.fp, "fn": m.fn, "tn": m.tn, "precision": m.precision,
                "recall": m.recall, "fpr": m.fpr, "time_to_detect": m.time_to_detect}

    return {"all": one(slim), "native": one([e for e in slim if e["provenance"] != "synthetic"]),
            "synthetic": one([e for e in slim if e["provenance"] == "synthetic"])}


# --------------------------------------------------------------------------- feedback (training only)
def _pattern(ev: dict[str, Any]) -> str:
    return json.dumps({k: ev[k] for k in PATTERN_FIELDS if ev.get(k) not in (None, "")}, sort_keys=True)


def observed_lines(agent_events: list[dict[str, Any]], top: int = 6) -> list[str]:
    """What a SOC engineer can see without labels: the most common event patterns in the zone last round."""
    if not agent_events:
        return []
    counts = Counter(_pattern(e) for e in agent_events)
    lines = [f"{len(agent_events)} events were seen in your zone; the most common patterns (unlabelled) were:"]
    lines += [f"{n}x {pat}" for pat, n in counts.most_common(top)]
    return lines


def rule_stats(events: list[dict[str, Any]], alerts: list[Any]) -> dict[str, dict[str, int]]:
    label = {e["event_id"]: e["label_red"] for e in events}
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"fires": 0, "red": 0})
    for a in alerts:
        s = out[a.rule_id]
        s["fires"] += 1
        s["red"] += int(label.get(a.event_id) == 1)
    return dict(out)


def feedback_for(agent_events: list[dict[str, Any]], alerts: list[Any], rules: list[Rule]) -> list[str]:
    """Plain-language training feedback for one Blue agent. Uses ground truth, so training episodes only."""
    if not agent_events:
        return ["no events were seen in your zone last round"]
    stats = rule_stats(agent_events, alerts)
    alerted = {a.event_id for a in alerts}
    red = [e for e in agent_events if e["label_red"] == 1]
    benign = [e for e in agent_events if e["label_red"] == 0]
    caught = sum(e["event_id"] in alerted for e in red)
    false = sum(e["event_id"] in alerted for e in benign)
    lines = [f"your rules matched {caught} of {len(red)} attacker events and {false} of {len(benign)} benign events in your zone"]
    titles = {r.rule_id: r.title for r in rules}
    for rid, s in sorted(stats.items(), key=lambda kv: -kv[1]["fires"])[:4]:
        lines.append(f"rule '{titles.get(rid, rid)}' fired {s['fires']} times, {100 * s['red'] // max(s['fires'], 1)}% on attacker activity")
    missed = Counter(_pattern(e) for e in red if e["event_id"] not in alerted)
    for pat, n in missed.most_common(3):
        lines.append(f"{n} attacker events matched NO rule, e.g. {pat}")
    noisy = Counter(_pattern(e) for e in benign if e["event_id"] in alerted)
    for pat, n in noisy.most_common(2):
        lines.append(f"{n} benign events wrongly fired alerts, e.g. {pat}")
    return lines


def feedback_rich(agent_events: list[dict[str, Any]], alerts: list[Any], rules: list[Rule]) -> list[str]:
    """Variant 'richfb': the standard feedback plus coverage by event category and up to six exact missed attacker patterns, each with an
    explicit instruction. Uses ground truth, so training episodes only."""
    lines = feedback_for(agent_events, alerts, rules)
    if not agent_events:
        return lines
    alerted = {a.event_id for a in alerts}
    red = [e for e in agent_events if e["label_red"] == 1]
    cats: dict[str, list[int]] = {}
    for e in red:
        c = cats.setdefault(e.get("category") or "?", [0, 0])
        c[1] += 1
        c[0] += int(e["event_id"] in alerted)
    if cats:
        lines.append("attacker events caught by category: " + "; ".join(f"{k} {v[0]} of {v[1]}" for k, v in sorted(cats.items())))
    missed = Counter(_pattern(e) for e in red if e["event_id"] not in alerted)
    for pat, n in missed.most_common(6)[3:]:
        lines.append(f"{n} attacker events matched NO rule, e.g. {pat}")
    if missed:
        lines.append("Write one new rule per missed attacker pattern above, matching exactly those field values, and avoid rules that only restate rules you already have.")
    return lines


def retire_weak_rules(agent: BlueLLMAgent, stats: dict[str, dict[str, int]], min_fires: int = 3, min_precision: float = 0.3) -> list[str]:
    """Selection pressure: drop active rules that fire often but almost never on attacker activity."""
    dropped = [r.rule_id for r in agent.active_rules
               if stats.get(r.rule_id, {}).get("fires", 0) >= min_fires
               and stats[r.rule_id]["red"] / stats[r.rule_id]["fires"] < min_precision]
    if dropped:
        agent.active_rules = [r for r in agent.active_rules if r.rule_id not in dropped]
        agent.executor = RuleExecutor(agent.active_rules)
    return dropped


# --------------------------------------------------------------------------- Blue team
@dataclass
class BlueTeam:
    agents: dict[str, BlueLLMAgent]
    pool: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=4))

    def rules(self) -> dict[str, list[Rule]]:
        return {a: list(ag.active_rules) for a, ag in self.agents.items()}

    def propose(self, round_number: int, feedback: dict[str, list[str]], last_alerts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        def go(item: tuple[str, BlueLLMAgent]) -> tuple[str, list[Rule]]:
            name, agent = item
            ctx = {"round": round_number, "agent_id": agent.agent_id, "feedback": feedback.get(name, []),
                   "last_alerts": last_alerts.get(name, [])}
            return name, agent.propose_rules(ctx)

        new = dict(self.pool.map(go, self.agents.items()))
        hist = [ag.history[-1] for ag in self.agents.values()]
        return {"new_rules": sum(len(v) for v in new.values()), "llm_calls": sum(h.llm_calls for h in hist),
                "valid_final": sum(h.valid_final for h in hist), "objects_found": sum(h.objects_found for h in hist),
                "valid_raw": sum(h.valid_raw for h in hist), "fallbacks": sum(h.fallback for h in hist),
                "latency_s": round(sum(h.latency_s for h in hist), 1)}
