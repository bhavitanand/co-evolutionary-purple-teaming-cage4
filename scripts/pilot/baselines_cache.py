"""Record labelled TRAINING-seed episodes (passive Blue, seeds 0-9 x the four seen Red strategies) so non-LLM baselines can be fitted on the
same seeds the LLM runs trained on. Output: results/pilot_baselines/train_events/<red>_s<seed>.json.gz  (run with .venv-cyborg python)."""
import gzip
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAGE = ROOT / "external" / "cage-challenge-4"
if CAGE.exists():
    sys.path.insert(0, str(CAGE))
from src.loop.coevo import EpisodePlayer  # noqa: E402

player = EpisodePlayer()
for red in ["cage4_default", "aggressive", "stealthy", "deception_aware"]:
    for s in range(10):
        path = ROOT / "results/pilot_baselines/train_events" / f"{red}_s{s}.json.gz"
        if path.exists():
            continue
        ep = player.play(red, s, steps=500)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump({"red": red, "seed": s, "last_step": ep["last_step"], "events": ep["events"]}, f)
        print("cached", red, s, len(ep["events"]), flush=True)
