"""Map full-provider benchmark rows to Nyne / PDL / Exa execution records."""

from __future__ import annotations

import re

from full_provider_eval.config import PERSONA_SLUGS, PERSONA_TO_EXA_CATEGORY_GROUP

_VERIFY_RE = re.compile(r"\bverify\b", re.I)


def query_text_from_row(row: dict) -> str:
    inp = row.get("input")
    if isinstance(inp, dict):
        return (inp.get("query") or "").strip()
    return str(inp or "").strip()


def persona_slug(metadata: dict | None) -> str:
    persona = (metadata or {}).get("persona") or ""
    return PERSONA_SLUGS.get(persona, persona.strip().lower().replace(" ", "_") or "unknown")


def record_from_row(row: dict) -> dict:
    """Build an execution record compatible with people-search-eval clients."""
    meta = row.get("metadata") or {}
    query_text = meta.get("query_text") or query_text_from_row(row)
    query_type = meta.get("query_type", "search")
    person_name = (meta.get("person_name") or "").strip()
    company = (meta.get("company") or "").strip()

    record: dict = {
        "id": row.get("id") or meta.get("benchmark_id"),
        "query_text": query_text,
        "query_type": query_type,
        "persona": meta.get("persona"),
        "persona_slug": persona_slug(meta),
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
        # probability_score only on compliance-style verify enrichments
        record["nyne_probability_score"] = is_verify
        if is_verify:
            title = _infer_title_from_query(query_text)
            record["nyne_verification_claims"] = {
                "name": person_name,
                "company": company,
                "title": title,
            }
    else:
        record["nyne_endpoint"] = "person/search"
        record["pdl_endpoint"] = "person/search"
        record["nyne_query"] = query_text

    return record


def record_for_exa(row: dict) -> dict:
    """Build an execution record for Exa Search (needs category_group)."""
    record = record_from_row(row)
    slug = record.get("persona_slug") or persona_slug(row.get("metadata"))
    record["category_group"] = PERSONA_TO_EXA_CATEGORY_GROUP.get(slug, "talent_sourcing")
    return record


def _infer_title_from_query(query_text: str) -> str:
    m = re.search(r"who works at", query_text, re.I)
    if m:
        return ""
    m = re.search(r",\s*([^,]+?)\s+at\s+", query_text, re.I)
    if m:
        return m.group(1).strip()
    return ""


def nyne_route_label(record: dict) -> str:
    endpoint = record.get("nyne_endpoint") or "person/search"
    if endpoint == "person/enrichment" and record.get("nyne_verification_claims"):
        return "person/enrichment+verify"
    return endpoint


def audit_nyne_routing(rows: list[dict]) -> dict[str, int]:
    """Summarize Nyne endpoint routing for a dataset (no API calls)."""
    counts: dict[str, int] = {}
    for row in rows:
        label = nyne_route_label(record_from_row(row))
        counts[label] = counts.get(label, 0) + 1
    return counts
