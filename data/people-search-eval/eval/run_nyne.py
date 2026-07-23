#!/usr/bin/env python3
"""
Braintrust eval — people-search benchmark × Nyne.

  python eval/run_nyne.py --low-credits
  python eval/run_nyne.py --routing-audit
  python eval/run_nyne.py --local-dataset --limit 3 --no-send-logs --low-credits
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
from lib.dataset_loader import load_cloud_dataset, load_local_dataset
from lib.eval_runner import bootstrap_env, run_eval
from lib.eval_tasks import nyne_task
from lib.routing import audit_nyne_routing, record_from_row


def _apply_low_credits_env() -> None:
    """Nyne credit savers — insights off is the biggest win on search rows."""
    os.environ.setdefault("NYNE_INSIGHTS", "0")
    os.environ.setdefault("NYNE_PROFILE_SCORING", "0")
    os.environ.setdefault("NYNE_PROBABILITY_SCORE", "0")
    os.environ.setdefault("NYNE_SEARCH_LIMIT", "5")


def parse_args():
    p = argparse.ArgumentParser(description="Nyne eval for people-search benchmark")
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
    p.add_argument("--concurrency", type=int, default=int(os.environ.get("NYNE_EVAL_CONCURRENCY", "1")))
    p.add_argument("--no-send-logs", action="store_true")
    p.add_argument("--overall-judge", default=OVERALL_JUDGE_SLUG)
    p.add_argument("--persona-judge", default=PERSONA_JUDGE_SLUG)
    p.add_argument(
        "--no-llm-judges",
        action="store_true",
        help="Skip Braintrust LLM judges (saves judge credits, not Nyne credits)",
    )
    p.add_argument(
        "--low-credits",
        action="store_true",
        help="Set NYNE_INSIGHTS=0, NYNE_PROFILE_SCORING=0, NYNE_PROBABILITY_SCORE=0, NYNE_SEARCH_LIMIT=5",
    )
    p.add_argument(
        "--routing-audit",
        action="store_true",
        help="Print enrichment vs search routing summary and exit (no API calls)",
    )
    return p.parse_args()


def _load_rows(args) -> list[dict]:
    if args.dataset:
        from braintrust import init_dataset

        return load_cloud_dataset(
            init_dataset(project=args.project, name=args.dataset),
            args.limit,
        )
    if args.local_dataset is not None:
        path = Path(args.local_dataset)
        if not path.is_absolute():
            path = PKG_ROOT / path
        return load_local_dataset(path, args.limit)
    return load_local_dataset(DATASET_JSON, args.limit)


def _print_routing_audit(rows: list[dict]) -> None:
    counts = audit_nyne_routing(rows)
    print(f"Rows audited: {len(rows)}")
    print("Nyne routing:")
    for endpoint, count in sorted(counts.items()):
        print(f"  {endpoint}: {count}")
    print()
    print("Routing rules:")
    print("  metadata.query_type=enrichment + person_name → person/enrichment")
    print("  metadata.query_type=search (or enrichment w/o person_name) → person/search")
    print("  verify* queries on enrichment → +verification_claims, probability_score if enabled")
    print()
    shown = 0
    for row in rows:
        rec = record_from_row(row)
        meta = row.get("metadata") or {}
        print(
            f"  {rec['id']}: {rec.get('nyne_endpoint')} "
            f"({meta.get('query_type')}, person={meta.get('person_name') or '-'})"
        )
        shown += 1
        if shown >= 5:
            break
    if len(rows) > shown:
        print(f"  ... and {len(rows) - shown} more")


def main():
    args = parse_args()

    if args.low_credits:
        _apply_low_credits_env()

    bootstrap_env()
    from people_search_eval import config as nyne_config

    if args.routing_audit:
        if not args.dataset and args.local_dataset is None:
            args.local_dataset = str(DATASET_JSON)
        rows = _load_rows(args)
        if not isinstance(rows, list):
            rows = list(rows)
        _print_routing_audit(rows)
        return

    if not nyne_config.NYNE_API_KEY or not nyne_config.NYNE_API_SECRET:
        raise SystemExit("Set NYNE_API_KEY and NYNE_API_SECRET in .env")

    if args.no_llm_judges:
        args.overall_judge = None
        args.persona_judge = None

    if not args.dataset and args.local_dataset is None:
        args.dataset = BRAINTRUST_DATASET

    print("Nyne credits config:")
    print(f"  insights:          {nyne_config.NYNE_INCLUDE_INSIGHTS}")
    print(f"  profile_scoring:   {nyne_config.NYNE_INCLUDE_PROFILE_SCORING}")
    print(f"  probability_score: {nyne_config.NYNE_PROBABILITY_SCORE}")
    print(f"  search_limit:      {nyne_config.NYNE_SEARCH_LIMIT}")
    print(f"  low_credits mode:  {args.low_credits}")
    print()

    run_eval(provider="nyne", task=nyne_task, args=args)


if __name__ == "__main__":
    main()
