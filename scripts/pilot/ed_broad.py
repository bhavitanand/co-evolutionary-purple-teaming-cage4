"""One-off: opt-in variant 'broad' (prompt guidance toward simple, broad rules; tests the paper's narrow-rules explanation). Baseline unchanged."""
import os


def edit(path, pairs):
    s = open(path, encoding="utf-8", newline=None).read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:70], s.count(a))
        s = s.replace(a, b)
    open(path + ".tmp", "w", encoding="utf-8", newline="\n").write(s)
    os.replace(path + ".tmp", path)


edit("src/agents/blue/prompt.py", [
    ("LIMITS_HINT_AGG = [",
     "# Variant 'broad' (env BLUE_BROAD=1): guidance toward simple, broad rules. Written from the visible field vocabulary, no labels.\n"
     "BROAD_HINT = [\n"
     '    "STYLE: prefer simple rules with one or two fields. A rule that matches on a single strong field, for example only the destination port, "\n'
     '    "is allowed and is often better than a long list of conditions. Do not add zone, address, privilege or parent_process conditions "\n'
     '    "unless the feedback shows the simple rule raised false alarms.",\n'
     "]\n\n\nLIMITS_HINT_AGG = ["),
    ("        *(COVERAGE_HINT if os.environ.get(\"BLUE_COVERAGE_HINT\") else []),",
     "        *(COVERAGE_HINT if os.environ.get(\"BLUE_COVERAGE_HINT\") else []),\n        *(BROAD_HINT if os.environ.get(\"BLUE_BROAD\") else []),"),
])
edit("scripts/pilot/run_coevo.py", [
    ('    if "agg" in args.variant.split("+"):',
     '    if "broad" in args.variant.split("+"):  # variant \'broad\': prompt guidance toward simple, broad rules\n        os.environ["BLUE_BROAD"] = "1"\n    if "agg" in args.variant.split("+"):'),
])
edit("scripts/pilot/dev_summary.py", [('"promptred", "agg")', '"promptred", "agg", "broad")')])
print("ok")
