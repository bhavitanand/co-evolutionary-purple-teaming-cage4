# LLM-Written Detection Rules Are Precise but Incomplete: A Pilot in CAGE-4 with Negative Results on Co-Evolutionary Purple Teaming

Code, frozen rule sets, cached test episodes and result files for the pilot study of LLM Blue agents that write Sigma-style detection
rules against an adaptive LLM Red agent in CybORG / CAGE Challenge 4. The paper is in [paper/paper.pdf](paper/paper.pdf)
(source: `paper/paper.md`). Authors: Bhavit Anand, Krish Anand, Prateek Tanwar (MAIT, GGSIPU, Delhi). Runs use a local `llama.cpp`
server (Qwen3-4B-Instruct-2507, Q4_K_M; GLM-4.7-Flash for the larger-model check) on one consumer GPU.

## Reproducing the paper

Every number in the paper is read from files under `results/`. Scoring is deterministic, so **re-scoring the released frozen rule sets
regenerates every table exactly**; retraining calls a language model and will not reproduce the same rules.

1. Environment: see [docs/setup.md](docs/setup.md) (Docker image, or a pinned Python 3.12 venv; CAGE-4 is pinned to a commit). Training needs
   the CAGE-4 environment plus `llama-server` with the GGUF model:
   `llama-server -m Qwen3-4B-Instruct-2507-Q4_K_M.gguf -ngl 99 -c 16384 --port 8080 --host 127.0.0.1`.
2. Re-score the released rule sets on the released test episodes (no LLM, no GPU):
   `python scripts/pilot/eval_rules.py --score --md results/pilot/results_final.md --out results/pilot/results_final.json`
   (other result folders: `results/pilot_rep`, `pilot_cap20`, `pilot_glm`, `pilot_recycle`; test episodes are cached in `results/*/test_events`).
3. Check the paper's tables against the result files: `python scripts/pilot/check_paper_numbers.py` (71 numbers).
4. Extra analyses: `scripts/pilot/analyze.py`, `rule_stats.py`, `per_rule.py`, `ttd.py`, `committee.py`, `committee_rep.py`, `baselines.py`.
5. Retrain a condition (hours; one 500-step episode per round, eight rounds per run):
   `python scripts/pilot/run_coevo.py --condition coevo --seeds 0 1 2 3 4 --rounds 8 --hint`
   (conditions: `llm_fixed_red`, `coevo_nofeedback`, `coevo`, `coevo_aware`, `coevo_evasive`, `evasive_nofeedback`). Training seeds are 0 to 9; test seeds 100 to 109 are only used for scoring.
6. Rebuild the PDF: `python scripts/pilot/build_paper.py` (needs `reportlab`).

Design variants that were screened on development seeds but are not in the paper (`recycle`, `richfb`, `promptred`, `agg`) are in
`results/pilot_dev` and `results/pilot_recycle`.

## Layout


| Path | Contents | Owner |
|---|---|---|
| `src/agents/` | `blue/`, `red/`, `baselines/`; mock agents (`random_blue`, `random_red`) | Krish |
| `src/rules/` | Rule dataclass, validator, executor, response playbook | Bhavit |
| `src/bridge/` | Telemetry bridge (CAGE-4 state -> synthetic events) and ground-truth labeler | Bhavit / Krish |
| `src/loop/` | Co-evolution loop, reward functions, checkpoints | Prateek |
| `src/eval/` | Metrics, bootstrap CIs, plots | Krish |
| `configs/` | YAML experiment configs | |
| `docs/` | Setup notes, cheat sheet, tuning log | |
| `scripts/` | Helper scripts | |
| `tests/` | pytest | |
| `results/` | Raw logs are gitignored; commit summaries under `results/summaries/` | |

The shapes of rules, events, agent APIs, logs and configs are defined in the
Interface Contract tab of the execution plan (frozen in T03).

## Conventions

- Python with type hints; `ruff` + `black` (config in `pyproject.toml`, CI runs `ruff check .`); `pytest` for every module; `logging`, not `print()`.
- Times in seconds. Seeds: tuning 0-9, test 100-109; never tune on test seeds.
- Branches: `feat/T##-short-name`. Every PR needs one review from another author.
- Every module must run against mock agents / mock events.

## Setup

One pinned environment (Python 3.12, CPU): `docker build -t purple-team . && docker run --rm purple-team` runs the tests in a container,
or `pip install -r requirements.txt -c constraints-py312.txt` natively. Details, what is pinned and why, and how to update the pins:
[docs/setup.md](docs/setup.md). CI (GitHub Actions) lints and tests every push.

## Documentation

- [docs/README.md](docs/README.md): index of the Blue-side docs (rules, Blue LLM agent, CAGE-4 telemetry findings, rating protocol) and how to reproduce the measurements.
- [docs/references.md](docs/references.md): papers and links used by the project.
