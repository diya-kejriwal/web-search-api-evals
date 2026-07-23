#!/usr/bin/env python3
"""
Braintrust eval — full-provider benchmark × Exa Search.

  # Full run on uploaded Braintrust dataset (default)
  python eval_exa_braintrust.py

  # Explicit cloud dataset
  python eval_exa_braintrust.py --project people-data-provider-evals --dataset full_provider_benchmark

  # Local file instead of cloud
  python eval_exa_braintrust.py --local-dataset --limit 3 --no-send-logs
  python eval_exa_braintrust.py --local-dataset --no-llm-judges
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from full_provider_eval.config import (
    BRAINTRUST_DATASET,
    DATASET_JSON,
    OVERALL_JUDGE_SLUG,
    PERSONA_JUDGE_SLUG,
)
from full_provider_eval.eval_runner import bootstrap_env, run_eval
from full_provider_eval.eval_tasks import exa_task


def parse_args():
    p = argparse.ArgumentParser(description="Exa eval for full-provider benchmark")
    p.add_argument("--project", default=os.environ.get("BRAINTRUST_PROJECT", "people-data-provider-evals"))
    p.add_argument("--dataset", default=None, help=f"Braintrust dataset (default: {BRAINTRUST_DATASET})")
    p.add_argument(
        "--local-dataset",
        nargs="?",
        const=str(DATASET_JSON),
        default=None,
        help="Load local JSON instead of cloud dataset",
    )
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--concurrency", type=int, default=int(os.environ.get("EXA_EVAL_CONCURRENCY", "1")))
    p.add_argument("--no-send-logs", action="store_true")
    p.add_argument("--overall-judge", default=OVERALL_JUDGE_SLUG)
    p.add_argument("--persona-judge", default=PERSONA_JUDGE_SLUG)
    p.add_argument(
        "--no-llm-judges",
        action="store_true",
        help="Skip Braintrust LLM judges (deterministic scorers only)",
    )
    return p.parse_args()


def main():
    bootstrap_env()
    from people_search_eval import config as exa_config

    args = parse_args()
    if not exa_config.EXA_API_KEY:
        raise SystemExit("Set EXA_API_KEY in .env")

    if args.no_llm_judges:
        args.overall_judge = None
        args.persona_judge = None

    if not args.dataset and args.local_dataset is None:
        args.dataset = BRAINTRUST_DATASET

    print(f"Exa type:   {exa_config.EXA_SEARCH_TYPE}")
    print(f"Exa results:{exa_config.EXA_NUM_RESULTS}")
    print(f"Exa query:  {exa_config.EXA_QUERY_FIELD}")
    run_eval(provider="exa", task=exa_task, args=args)


if __name__ == "__main__":
    main()
