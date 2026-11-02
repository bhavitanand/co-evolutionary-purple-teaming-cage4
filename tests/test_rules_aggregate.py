"""Optional rule aggregate: alert only once N matching events from one group occur within W steps."""
from src.rules.executor import RuleExecutor
from src.rules.schema import Rule
from src.rules.validator import validate_rule_dict


def _rule(**agg):
    return {"rule_id": "blue_0_t", "round": 1, "agent_id": "blue_0", "title": "burst", "level": "medium",
            "logsource": {"category": "network_connection"}, "detection": {"s": {"dst_port": 22}, "condition": "s"},
            "confidence": 0.7, "rationale": "x", "aggregate": {"count": 3, "window": 10, "group_by": "host_id", **agg}}


def _events(steps, host="h1"):
    return [{"event_id": i, "step": s, "host_id": host, "category": "network_connection", "dst_port": 22} for i, s in enumerate(steps)]


def test_valid_and_invalid_aggregate():
    assert validate_rule_dict(_rule()).valid
    assert not validate_rule_dict(_rule(count=1)).valid
    assert not validate_rule_dict(_rule(window=500)).valid
    assert not validate_rule_dict(_rule(group_by="label_red")).valid


def test_alerts_only_when_count_reached_in_window():
    ex = RuleExecutor([Rule.from_dict(_rule())])
    assert [a.step for a in ex.run(_events([1, 3, 5, 40, 41, 60]))] == [5]


def test_groups_are_independent():
    ex = RuleExecutor([Rule.from_dict(_rule())])
    ev = _events([1, 2], "h1") + _events([3], "h2")
    assert ex.run(ev) == []


def test_rule_without_aggregate_unchanged():
    d = _rule()
    del d["aggregate"]
    assert len(RuleExecutor([Rule.from_dict(d)]).run(_events([1, 2]))) == 2
