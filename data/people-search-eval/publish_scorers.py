#!/usr/bin/env python3
"""Publish all full-provider Braintrust LLM judges."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from braintrust.framework2 import projects
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "scorers" / "prompts"

CHOICE_SCORES = {
    "High Value": 1.0,
    "Useful": 0.7,
    "Low Value": 0.3,
    "Failed": 0.0,
}

SCORERS = [
    ("overall.md", "people-judge-overall", "people-judge-overall"),
    ("persona.md", "people-judge-persona", "people-judge-persona"),
]


def _load_prompt(path: Path) -> str:
    text = path.read_text()
    parts = text.split("---", 2)
    prompt = parts[2].strip() if len(parts) >= 3 else text.strip()
    if not prompt:
        raise SystemExit(f"No prompt body in {path}")
    return prompt


def parse_args():
    p = argparse.ArgumentParser(description="Publish full-provider Braintrust judges")
    p.add_argument("--project", default=os.environ.get("BRAINTRUST_PROJECT", "people-data-provider-evals"))
    p.add_argument("--model", default=os.environ.get("SCORER_MODEL", "claude-opus-4-6"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", nargs="*", help="Publish subset by slug suffix (e.g. persona)")
    return p.parse_args()


def main():
    load_dotenv(ROOT / ".env")
    args = parse_args()

    if not args.dry_run and not os.environ.get("BRAINTRUST_API_KEY"):
        raise SystemExit("Set BRAINTRUST_API_KEY in .env")

    project = None if args.dry_run else projects.create(args.project)

    for filename, slug, name in SCORERS:
        if args.only and not any(slug == f"people-judge-{x}" for x in args.only):
            continue
        prompt = _load_prompt(PROMPTS_DIR / filename)
        print(f"{slug}: {len(prompt)} chars, model={args.model}")
        if args.dry_run:
            continue
        project.scorers.create(
            name=name,
            slug=slug,
            description=f"Full-provider people-search judge ({name})",
            messages=[{"role": "user", "content": prompt}],
            model=args.model,
            use_cot=True,
            choice_scores=CHOICE_SCORES,
            if_exists="replace",
        )

    if not args.dry_run:
        project.publish()
        print(f"\nPublished to {args.project}")


if __name__ == "__main__":
    main()
