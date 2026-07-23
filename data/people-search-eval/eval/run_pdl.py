#!/usr/bin/env python3
"""
Braintrust eval — people-search benchmark × People Data Labs.

  python eval/run_pdl.py --project people-data-provider-evals --dataset full_provider_benchmark
  python eval/run_pdl.py --local-dataset --limit 3 --no-send-logs
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))
sys.path.insert(0, str(PKG_ROOT / "eval"))

from lib.config import (
    BRAINTRUST_DATASET,
    DATASET_JSON,
    OVERALL_JUDGE_SLUG,
    PERSONA_JUDGE_SLUG,
)
from lib.eval_runner import bootstrap_env, run_eval
from lib.eval_tasks import pdl_task


def parse_args():
    p = argparse.ArgumentParser(description="PDL eval for people-search benchmark")
    p.add_argument("--project", default=os.environ.get("BRAINTRUST_PROJECT", "people-data-provider-evals"))
    p.add_argument("--dataset", default=None)
    p.add_argument(
        "--local-dataset",
        nargs="?",
        const=str(DATASET_JSON),
        default=None,
    )
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--concurrency", type=int, default=int(os.environ.get("PDL_EVAL_CONCURRENCY", "2")))
    p.add_argument("--no-send-logs", action="store_true")
    p.add_argument("--overall-judge", default=OVERALL_JUDGE_SLUG)
    p.add_argument("--persona-judge", default=PERSONA_JUDGE_SLUG)
    return p.parse_args()


def main():
    bootstrap_env()
    from people_search_eval import config as pdl_config

    args = parse_args()
    if not pdl_config.PDL_API_KEY:
        raise SystemExit("Set PDL_API_KEY in .env")

    if not args.dataset and args.local_dataset is None:
        args.dataset = BRAINTRUST_DATASET

    run_eval(provider="pdl", task=pdl_task, args=args)


if __name__ == "__main__":
    main()
