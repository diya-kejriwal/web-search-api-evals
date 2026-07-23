#!/usr/bin/env python3
"""Upload dataset/full_provider_benchmark.json to Braintrust."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from braintrust import flush, init_dataset
from dotenv import load_dotenv

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT))
sys.path.insert(0, str(PKG_ROOT / "eval"))

from lib.config import BRAINTRUST_DATASET, DATASET_JSON
from lib.dataset_loader import load_local_dataset

load_dotenv(PKG_ROOT / ".env")


def parse_args():
    p = argparse.ArgumentParser(description="Upload people-search benchmark to Braintrust")
    p.add_argument("--project", default=os.environ.get("BRAINTRUST_PROJECT", "people-data-provider-evals"))
    p.add_argument("--dataset", default=BRAINTRUST_DATASET)
    p.add_argument("--file", default=str(DATASET_JSON))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    path = Path(args.file)
    if not path.is_absolute():
        path = PKG_ROOT / path
    if not path.exists():
        raise SystemExit(f"Missing {path}")

    rows = load_local_dataset(path)
    print(f"Loaded {len(rows)} rows from {path.name}")
    print(f"Target: {args.project}/{args.dataset}")

    if args.dry_run:
        return

    if not os.environ.get("BRAINTRUST_API_KEY"):
        raise SystemExit("Set BRAINTRUST_API_KEY in .env")

    dataset = init_dataset(project=args.project, name=args.dataset)
    for i, row in enumerate(rows, start=1):
        dataset.insert(
            id=row["id"],
            input=row["input"],
            metadata=row.get("metadata"),
        )
        if i % 50 == 0 or i == len(rows):
            print(f"  upserted {i}/{len(rows)}")

    flush()
    print(f"Done — {args.project}/{args.dataset}")


if __name__ == "__main__":
    main()
