"""Map people-search CSV rows to Nyne / PDL / Exa execution records."""

from __future__ import annotations

import re

from evals.processing.people_search.constants import (
    PERSONA_SLUGS,
    PERSONA_TO_EXA_CATEGORY_GROUP,
)

_VERIFY_RE = re.compile(r"\bverify\b", re.I)


def persona_slug(persona: str | None, persona_slug_value: str | None = None) -> str:
    if persona_slug_value:
        return str(persona_slug_value).strip().lower()
    label = persona or ""
    return PERSONA_SLUGS.get(
        label, label.strip().lower().replace(" ", "_") or "unknown"
    )


def build_execution_record(
    query: str,
    metadata: dict | None = None,
    *,
    for_exa: bool = False,
) -> dict:
    """Build an execution record compatible with people-search-eval clients."""
    meta = metadata or {}
    query_text = (meta.get("query_text") or query or "").strip()
    query_type = meta.get("query_type") or "search"
    person_name = (meta.get("person_name") or "").strip()
    company = (meta.get("company") or "").strip()
    slug = persona_slug(meta.get("persona"), meta.get("persona_slug"))

    record: dict = {
        "id": meta.get("benchmark_id"),
        "query_text": query_text,
        "query_type": query_type,
        "persona": meta.get("persona"),
        "persona_slug": slug,
        "person_name": person_name,
        "company": company,
        "nyne_insights": False,
        "nyne_profile_scoring": False,
        "nyne_search_limit": 5,
        "nyne_probability_score": False,
        "pdl_search_size": 5,
    }

    is_verify = bool(_VERIFY_RE.search(query_text))

    if query_type == "enrichment" and person_name:
        record["nyne_endpoint"] = "person/enrichment"
        record["pdl_endpoint"] = "person/enrich"
        record["nyne_enrichment"] = {
            "name": person_name,
            "company": company,
            "ai_enhanced_search": True,
        }
        record["nyne_probability_score"] = is_verify
        if is_verify:
            record["nyne_verification_claims"] = {
                "name": person_name,
                "company": company,
                "title": _infer_title_from_query(query_text),
            }
    else:
        record["nyne_endpoint"] = "person/search"
        record["pdl_endpoint"] = "person/search"
        record["nyne_query"] = query_text

    if for_exa:
        record["category_group"] = PERSONA_TO_EXA_CATEGORY_GROUP.get(
            slug, "talent_sourcing"
        )

    return record


def _infer_title_from_query(query_text: str) -> str:
    m = re.search(r"who works at", query_text, re.I)
    if m:
        return ""
    m = re.search(r",\s*([^,]+?)\s+at\s+", query_text, re.I)
    if m:
        return m.group(1).strip()
    return ""


def scorer_payload_from_provider_result(result: dict, provider: str) -> dict:
    """Normalize provider execute_* output into the scorer payload."""
    summary = result.get("summary") or {}
    people = summary.get("people") or result.get("people") or []
    if summary.get("person") and not people:
        people = [summary["person"]]
    person_count = result.get("person_count")
    if person_count is None:
        person_count = summary.get("person_count")
    if person_count is None:
        person_count = len(people) if isinstance(people, list) else 0

    payload = {
        "provider": provider,
        "people": people,
        "person_count": int(person_count or 0),
        "error": result.get("error"),
        "summary": summary,
        "latency_seconds": result.get("latency_seconds"),
    }
    if provider == "nyne":
        payload["nyne_endpoint"] = result.get("nyne_endpoint")
    if provider == "pdl":
        payload["pdl_endpoint"] = result.get("pdl_endpoint")
    if provider == "exa":
        payload["category_group"] = result.get("category_group")
    return payload
