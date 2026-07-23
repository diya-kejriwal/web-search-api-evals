"""Shared Braintrust eval runner for Nyne and PDL."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from braintrust import Eval, init_dataset, init_function
from dotenv import load_dotenv

from full_provider_eval.config import (
    BRAINTRUST_DATASET,
    BRAINTRUST_PROJECT,
    OVERALL_JUDGE_SLUG,
    PERSONA_JUDGE_SLUG,
)
from full_provider_eval.dataset_loader import load_cloud_dataset, load_local_dataset
from full_provider_eval.scorers.field_fill_scorer import field_fill_scorer
from full_provider_eval.scorers.persona_field_fill_scorer import persona_field_fill_scorer

ROOT = Path(__file__).resolve().parents[2]


def _people_search_eval_src() -> Path | None:
    env = os.environ.get("PEOPLE_SEARCH_EVAL_SRC")
    if env:
        return Path(env).expanduser()
    for candidate in (
        ROOT.parents[2] / "people-search-eval" / "src",
        ROOT.parent.parent / "people-search-eval" / "src",
    ):
        if candidate.is_dir():
            return candidate
    return None


def bootstrap_env() -> None:
    os.environ.setdefault("BRAINTRUST_LEGACY_IDS", "true")
    load_dotenv(ROOT / ".env")
    pse_src = _people_search_eval_src()
    if pse_src is not None:
        load_dotenv(pse_src.parent / ".env")
        if str(pse_src) not in sys.path:
            sys.path.insert(0, str(pse_src))
    from people_search_eval import config as pse

    pse.NYNE_API_KEY = os.environ.get("NYNE_API_KEY")
    pse.NYNE_API_SECRET = os.environ.get("NYNE_API_SECRET")
    pse.PDL_API_KEY = os.environ.get("PDL_API_KEY")
    pse.NYNE_INCLUDE_INSIGHTS = os.environ.get("NYNE_INSIGHTS", "1") == "1"
    pse.NYNE_INCLUDE_PROFILE_SCORING = os.environ.get("NYNE_PROFILE_SCORING", "0") == "1"
    pse.NYNE_PROBABILITY_SCORE = os.environ.get("NYNE_PROBABILITY_SCORE", "1") == "1"
    pse.NYNE_SEARCH_LIMIT = int(os.environ.get("NYNE_SEARCH_LIMIT", str(pse.NYNE_SEARCH_LIMIT)))
    pse.PDL_SEARCH_SIZE = int(os.environ.get("PDL_SEARCH_SIZE", str(pse.PDL_SEARCH_SIZE)))
    pse.EXA_API_KEY = os.environ.get("EXA_API_KEY")
    pse.EXA_NUM_RESULTS = int(os.environ.get("EXA_NUM_RESULTS", str(pse.EXA_NUM_RESULTS)))
    pse.EXA_SEARCH_TYPE = os.environ.get("EXA_SEARCH_TYPE", pse.EXA_SEARCH_TYPE)
    pse.EXA_QUERY_FIELD = os.environ.get("EXA_QUERY_FIELD", pse.EXA_QUERY_FIELD)
    pse.EXA_INCLUDE_HIGHLIGHTS = os.environ.get("EXA_INCLUDE_HIGHLIGHTS", "1") == "1"


def person_count_scorer(output, expected, input, metadata):
    from braintrust import Score

    if not isinstance(output, dict):
        return Score(name="has_people", score=0.0)
    count = output.get("person_count")
    if count is None:
        people = output.get("people") or []
        count = len(people)
    return Score(name="has_people", score=1.0 if count else 0.0, metadata={"person_count": count})


def build_scores(
    project: str,
    *,
    overall_judge: str | None,
    persona_judge: str | None,
) -> list:
    scores: list = [person_count_scorer, field_fill_scorer, persona_field_fill_scorer]

    if overall_judge:
        scores.append(init_function(project_name=project, slug=overall_judge))

    # One persona-switched judge: it reads metadata.persona / output.judge_persona
    # and applies the matching rubric inside a single prompt.
    if persona_judge:
        scores.append(init_function(project_name=project, slug=persona_judge))

    return scores


def run_eval(
    *,
    provider: str,
    task,
    args,
    default_dataset: str = BRAINTRUST_DATASET,
) -> None:
    bootstrap_env()

    if args.dataset:
        data = load_cloud_dataset(init_dataset(project=args.project, name=args.dataset), args.limit)
        dataset_label = args.dataset
        local_mode = False
        print("Mode:      cloud (Braintrust dataset)")
        print(f"Project:   {args.project}")
        print(f"Dataset:   {args.dataset}")
    elif args.local_dataset is not None:
        path = Path(args.local_dataset)
        if not path.is_absolute():
            path = ROOT / path
        data = load_local_dataset(path, args.limit)
        dataset_label = path.name
        local_mode = True
        print("Mode:      local file")
        print(f"Data file: {path.name}")
    else:
        raise SystemExit("Pass --dataset NAME or --local-dataset PATH")

    date_suffix = datetime.now(timezone.utc).strftime("%Y%m%d")
    if provider == "exa-calibration":
        experiment_name = f"exa-calibration-{date_suffix}"
    else:
        experiment_name = f"{provider}-full-provider-{dataset_label}-{date_suffix}"

    row_count = args.limit or (len(data) if isinstance(data, list) else "all")
    print(f"Provider:  {provider}")
    print(f"Experiment:{experiment_name}")
    print(f"Rows:      {row_count}")
    print(f"Upload:    {'no' if args.no_send_logs else 'yes'}")

    scores = build_scores(
        args.project,
        overall_judge=args.overall_judge,
        persona_judge=args.persona_judge,
    )
    print(f"Scorers:   has_people, field_fill, persona_field_fill", end="")
    if args.overall_judge:
        print(f", {args.overall_judge}", end="")
    if args.persona_judge:
        print(f", persona={args.persona_judge}", end="")
    print()

    Eval(
        args.project,
        data=data,
        task=task,
        scores=scores,
        max_concurrency=args.concurrency,
        experiment_name=experiment_name,
        no_send_logs=args.no_send_logs,
        metadata={
            "api": provider,
            "benchmark": "calibration" if provider == "exa-calibration" else "full_provider_people_search",
            "dataset": dataset_label,
            "local_mode": local_mode,
        },
    )
