"""Reproducible execution harness for development and later authorized cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

from .devdata import make_plans, make_questions, make_scenarios
from .model_client import MockClient, ModelConfig, HostedModelClient, RetryingClient, prompt_hash
from .schema import ExecutionTrace, Question, Scenario
from .systems.direct import run_direct
from .systems.program import run_program
from .systems.sandbox import MockSandbox
from .systems.d2.workflow import run_d2


def tuple_id(experiment_id: str, cohort: str, question_id: str, arm: str, repeat: int) -> str:
    material = f"{experiment_id}|{cohort}|{question_id}|{arm}|{repeat}".encode()
    return hashlib.sha256(material).hexdigest()[:24]


def schedule(questions: list[Question], arms: list[str], cohort: str, seed: int, experiment_id: str, repeat: int = 1) -> list[dict[str, object]]:
    rows = [
        {"tuple_id": tuple_id(experiment_id, cohort, question.question_id, arm, repeat), "question_id": question.question_id, "arm": arm, "cohort": cohort, "repeat": repeat}
        for question in questions for arm in arms
    ]
    random.Random(seed).shuffle(rows)
    return rows


def select_repeat_subset(questions: list[Question], *, seed: int = 20261125) -> list[str]:
    """Select one question per scenario using metadata only.

    The held-out question metadata is supplied by the later freeze step; this helper
    does not construct or materialize any held-out scenario here.
    """
    grouped: dict[str, list[Question]] = {}
    for question in questions:
        grouped.setdefault(question.scenario_id, []).append(question)
    rng = random.Random(seed)
    selected: list[str] = []
    for scenario_id in sorted(grouped):
        candidates = sorted(grouped[scenario_id], key=lambda item: (item.question_class.value, item.difficulty, item.question_id))
        selected.append(rng.choice(candidates).question_id)
    return selected


def _client(live: bool):
    if live:
        config = ModelConfig(model_id=os.environ.get("AUD_SUD_MODEL_ID", ""), allow_live=True, provider=os.environ.get("AUD_SUD_PROVIDER", "openai"), api_base=os.environ.get("AUD_SUD_API_BASE"))
        return RetryingClient(HostedModelClient(config, cli_live=True))
    return RetryingClient(MockClient())


def run_development(*, arms: list[str] | None = None, seed: int = 20261125, experiment_id: str = "development", live: bool = False) -> Path:
    if live and (os.environ.get("AUD_SUD_ALLOW_LIVE_API", "false").lower() != "true"):
        raise RuntimeError("live development execution requires AUD_SUD_ALLOW_LIVE_API=true")
    arms = arms or ["A", "C", "B"]
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    by_scenario = {scenario.scenario_id: scenario for scenario in scenarios}
    by_question = {question.question_id: question for question in questions}
    plans = make_plans(scenarios, questions)
    client = _client(live)
    run_root = Path("runs") / experiment_id
    for subdir in ("manifest", "raw", "delivered", "traces", "usage"):
        (run_root / subdir).mkdir(parents=True, exist_ok=True)
    manifest = {"experiment_id": experiment_id, "cohort": "development", "seed": seed, "arms": arms, "questions": [question.question_id for question in questions], "gold_isolation": True, "live": live}
    (run_root / "manifest" / "execution.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = schedule(questions, arms, "development", seed, experiment_id)
    (run_root / "manifest" / "schedule.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completed = {line.split("\t", 1)[0] for line in (run_root / "manifest" / "completed.tsv").read_text().splitlines()} if (run_root / "manifest" / "completed.tsv").exists() else set()
    with (run_root / "manifest" / "completed.tsv").open("a", encoding="utf-8") as done:
        for row in rows:
            if row["tuple_id"] in completed:
                continue
            started = time.perf_counter()
            question = by_question[str(row["question_id"])]
            scenario = by_scenario[question.scenario_id]
            arm = str(row["arm"])
            failure = None
            try:
                if arm == "A":
                    answer, detail = run_direct(client, question, scenario)
                elif arm == "C":
                    answer, detail = run_program(client, question, scenario, sandbox=MockSandbox())
                elif arm == "B":
                    answer, detail = run_d2(client, question, scenario, development_plan=plans[question.question_id])
                else:
                    raise ValueError(f"unknown arm {arm}")
            except Exception as exc:  # retain attempted denominator and diagnostics
                answer = None
                detail = {"error": str(exc)}
                failure = "execution_failure"
            raw = answer.model_dump(mode="json") if answer is not None else None
            (run_root / "raw" / f"{row['tuple_id']}.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (run_root / "delivered" / f"{row['tuple_id']}.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            trace = ExecutionTrace(question_id=question.question_id, scenario_id=question.scenario_id, arm=arm, cohort="development", tuple_id=str(row["tuple_id"]), prompt_hashes={"question": prompt_hash({"question": question.text})}, model_id=getattr(client, "model_id", "hosted"), calls=int(detail.get("calls", 0)), plan=detail.get("plan"), code=detail.get("code"), tool_trace=detail.get("tool_trace", []), raw_answer=raw, delivered_answer=raw, failure_class=failure or detail.get("failure"), latency_ms=(time.perf_counter() - started) * 1000)
            (run_root / "traces" / f"{row['tuple_id']}.json").write_text(json.dumps(trace.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            done.write(f"{row['tuple_id']}\t{arm}\t{question.question_id}\n")
    return run_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Run only the authorized development cohort by default")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--arms", default="A,C,B")
    parser.add_argument("--seed", type=int, default=20261125)
    parser.add_argument("--run", default="development")
    parser.add_argument("--mock", action="store_true", help="use the local mock client")
    parser.add_argument("--live", action="store_true", help="explicitly authorize hosted-model requests")
    args = parser.parse_args()
    if args.split != "dev":
        raise SystemExit("held-out benchmark execution is intentionally not implemented in the development repository")
    if not args.mock and not args.live:
        raise SystemExit("choose --mock or explicitly choose --live with the required environment flag")
    root = run_development(arms=[item for item in args.arms.split(",") if item], seed=args.seed, experiment_id=args.run, live=args.live)
    print(root)


if __name__ == "__main__":
    main()

