"""Evasive Red: a scripted adversary that is rewarded for not being caught (pilot stronger-Red condition).

The LLM planner turned out to ignore its memory (plans followed the round number), so this Red adapts by construction.
It owns a small library of round plans. In the first rounds it tries each plan once (seeded random order); afterwards it
replays the plan whose most recent reward was highest. Reward = share of its own events that no rule alerted on, but 0
if the round produced no successful Impact (a Red that achieves nothing is not evading, it is idle).
It sees only what the planner sees (the caught share of the round, from training labels), never the rules themselves.
"""
from __future__ import annotations

import random
from typing import Any

from src.agents.red.plan import RedPlan

LIBRARY: dict[str, RedPlan] = {
    "stealth_probe": RedPlan("stealth_recon", "stealthy", 0.8, False, 0.3, 0.3, "quiet scans, probe for decoys, little pressure"),
    "stealth_push": RedPlan("balanced", "stealthy", 0.1, True, 0.7, 0.3, "quiet scans, go for servers and impact"),
    "loud_push": RedPlan("fast_impact", "aggressive", 0.0, True, 0.95, 0.5, "fast aggressive path to impact"),
    "mixed": RedPlan("balanced", "mixed", 0.3, False, 0.5, 0.5, "mixed scan style, moderate pressure"),
}


class EvasiveRed:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.order = list(LIBRARY)
        self.rng.shuffle(self.order)
        self.last_reward: dict[str, float] = {}
        self.current: str | None = None
        self.history: list[dict[str, Any]] = []

    def plan(self, round_ctx: dict[str, Any]) -> dict[str, Any]:
        rnd = round_ctx.get("round", 1)
        if rnd <= len(self.order):
            name, source = self.order[rnd - 1], "evasive_explore"
        else:
            best = max(self.last_reward.values())
            name = self.rng.choice([k for k, v in self.last_reward.items() if v == best])
            source = "evasive_exploit"
        self.current = name
        return {"plan": LIBRARY[name].to_dict(), "plan_name": name, "source": source, "errors": [], "llm_calls": 0,
                "tokens_out": 0, "llm_latency_s": 0.0}

    def update(self, entry: dict[str, Any]) -> None:
        out = entry["outcome"]
        reward = 0.0 if not out.get("impact_ok") else 1.0 - out.get("caught_pct", 100) / 100.0
        self.last_reward[self.current] = reward
        self.history.append({"round": entry["round"], "plan": self.current, "reward": round(reward, 3)})
