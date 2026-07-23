"""Shared helpers for Nyne / PDL / Exa Braintrust eval scripts."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from braintrust import current_span, traced

from lib.people_preview import scorer_output_fields
from lib.routing import record_for_exa, record_from_row

# data/people-search-eval/
REPO_ROOT = Path(__file__).resolve().parents[2]


def _people_search_eval_src_candidates() -> list[Path]:
    env = os.environ.get("PEOPLE_SEARCH_EVAL_SRC")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env).expanduser())
    # Common local layouts: sibling checkout next to web-search-api-evals
    candidates.append(REPO_ROOT.parents[2] / "people-search-eval" / "src")
    candidates.append(REPO_ROOT.parent.parent / "people-search-eval" / "src")
    return candidates


def ensure_people_search_eval_importable() -> None:
    try:
        import people_search_eval  # noqa: F401

        return
    except ImportError:
        pass

    for candidate in _people_search_eval_src_candidates():
        src = str(candidate)
        if candidate.is_dir() and src not in sys.path:
            sys.path.insert(0, src)
            try:
                import people_search_eval  # noqa: F401

                return
            except ImportError:
                continue
    raise SystemExit(
        "people_search_eval package not found. Install it (pip install -e ../people-search-eval) "
        "or set PEOPLE_SEARCH_EVAL_SRC to that package's src/ directory."
    )


def _people_from_result(result: dict) -> tuple[list, int | None]:
    summary = result.get("nyne_summary") or result.get("summary") or {}
    people = summary.get("people") or []
    if summary.get("person") and not people:
        people = [summary["person"]]
    person_count = summary.get("person_count")
    if person_count is None:
        person_count = len(people)
    return people, person_count


@traced
def nyne_task(input, hooks):
    ensure_people_search_eval_importable()
    from people_search_eval.execute_query import execute_query

    meta = hooks.metadata if hooks else {}
    record = record_from_row({"input": input, "metadata": meta, "id": meta.get("benchmark_id")})
    t0 = time.time()
    result = execute_query(record)
    elapsed = round(time.time() - t0, 2)

    people, person_count = _people_from_result(result)
    output = {
        "people": people,
        "person_count": person_count,
        "endpoint": result.get("nyne_endpoint"),
        "error": result.get("error"),
        **scorer_output_fields(people, meta, provider="nyne"),
    }

    latency_ms = round((result.get("latency_seconds") or elapsed) * 1000, 2)
    span = current_span()
    if span:
        span.log(
            metrics={"latency_ms": latency_ms, "person_count": person_count or 0},
            metadata={
                "benchmark_id": record.get("id"),
                "provider": "nyne",
                "persona": meta.get("persona"),
                "query_type": meta.get("query_type"),
            },
        )
    return output


@traced
def exa_task(input, hooks):
    ensure_people_search_eval_importable()
    from people_search_eval.execute_exa_query import execute_exa_query

    meta = hooks.metadata if hooks else {}
    record = record_for_exa({"input": input, "metadata": meta, "id": meta.get("benchmark_id")})
    t0 = time.time()
    result = execute_exa_query(record)
    elapsed = round(time.time() - t0, 2)

    people, person_count = _people_from_result(result)
    category = result.get("exa_category")
    search_type = result.get("exa_type")
    endpoint = f"exa/search:{category or 'people'}:{search_type or 'auto'}"

    output = {
        "people": people,
        "person_count": person_count,
        "endpoint": endpoint,
        "error": result.get("error"),
        **scorer_output_fields(people, meta, provider="exa"),
    }

    latency_ms = round((result.get("latency_seconds") or elapsed) * 1000, 2)
    span = current_span()
    if span:
        span.log(
            metrics={"latency_ms": latency_ms, "person_count": person_count or 0},
            metadata={
                "benchmark_id": record.get("id"),
                "provider": "exa",
                "exa_category": category,
                "exa_type": search_type,
                "category_group": record.get("category_group"),
                "persona": meta.get("persona"),
                "query_type": meta.get("query_type"),
            },
        )
    return output


@traced
def pdl_task(input, hooks):
    ensure_people_search_eval_importable()
    from people_search_eval.execute_pdl_query import execute_pdl_query

    meta = hooks.metadata if hooks else {}
    record = record_from_row({"input": input, "metadata": meta, "id": meta.get("benchmark_id")})
    t0 = time.time()
    result = execute_pdl_query(record)
    elapsed = round(time.time() - t0, 2)

    people, person_count = _people_from_result(result)
    endpoint = result.get("pdl_endpoint") or "person/search"
    pdl_label = f"pdl/{endpoint}"

    output = {
        "people": people,
        "person_count": person_count,
        "endpoint": pdl_label,
        "error": result.get("error"),
        **scorer_output_fields(people, meta, provider="pdl"),
    }

    latency_ms = round((result.get("latency_seconds") or elapsed) * 1000, 2)
    span = current_span()
    if span:
        span.log(
            metrics={"latency_ms": latency_ms, "person_count": person_count or 0},
            metadata={
                "benchmark_id": record.get("id"),
                "provider": "pdl",
                "persona": meta.get("persona"),
                "query_type": meta.get("query_type"),
            },
        )
    return output
