"""Persona-weighted field-fill scorer — what each buyer persona cares about."""

from __future__ import annotations

from lib.people_preview import judge_persona_from_metadata
from scorers.field_fill_scorer import (
    TRACKED_FIELDS,
    _extract_people,
    _is_filled,
    _person_field_values,
)

# Weight per field for each persona slug (higher = more important to that buyer).
PERSONA_FIELD_WEIGHTS: dict[str, dict[str, float]] = {
    "recruiter": {
        "displayname": 1.0,
        "current_title": 2.5,
        "current_company": 2.5,
        "location": 1.5,
        "profile_url": 1.0,
        "highlight": 1.0,
        "email": 0.5,
        "phone": 0.5,
        "skills": 2.0,
        "insights": 1.5,
        "confidence": 1.0,
    },
    "sdr": {
        "displayname": 2.0,
        "current_title": 1.5,
        "current_company": 2.0,
        "location": 0.5,
        "profile_url": 1.5,
        "highlight": 0.5,
        "email": 3.0,
        "phone": 3.0,
        "skills": 0.5,
        "insights": 0.5,
        "confidence": 1.5,
    },
    "compliance": {
        "displayname": 3.0,
        "current_title": 2.5,
        "current_company": 3.0,
        "location": 1.0,
        "profile_url": 2.0,
        "highlight": 1.0,
        "email": 0.5,
        "phone": 0.5,
        "skills": 0.5,
        "insights": 1.0,
        "confidence": 2.5,
    },
    "journalist": {
        "displayname": 2.0,
        "current_title": 2.0,
        "current_company": 2.0,
        "location": 1.0,
        "profile_url": 2.0,
        "highlight": 2.5,
        "email": 0.5,
        "phone": 0.5,
        "skills": 0.5,
        "insights": 2.0,
        "confidence": 1.0,
    },
    "events": {
        "displayname": 2.0,
        "current_title": 1.5,
        "current_company": 2.0,
        "location": 1.5,
        "profile_url": 1.5,
        "highlight": 1.0,
        "email": 2.5,
        "phone": 2.5,
        "skills": 0.5,
        "insights": 0.5,
        "confidence": 1.0,
    },
    "investor": {
        "displayname": 2.0,
        "current_title": 2.5,
        "current_company": 2.5,
        "location": 1.0,
        "profile_url": 2.0,
        "highlight": 2.0,
        "email": 0.5,
        "phone": 0.5,
        "skills": 1.0,
        "insights": 2.0,
        "confidence": 1.5,
    },
}

DEFAULT_WEIGHTS = {field: 1.0 for field in TRACKED_FIELDS}


def persona_weighted_fill_ratio(person: dict, persona: str) -> float:
    weights = PERSONA_FIELD_WEIGHTS.get(persona, DEFAULT_WEIGHTS)
    values = _person_field_values(person)
    total_weight = sum(weights.get(f, 1.0) for f in TRACKED_FIELDS)
    earned = sum(weights.get(f, 1.0) for f in TRACKED_FIELDS if _is_filled(values.get(f)))
    return earned / total_weight if total_weight else 0.0


def row_persona_fill_score(people: list | None, persona: str, *, max_people: int = 5) -> dict:
    if not people:
        return {"score": 0.0, "persona": persona, "people_scored": 0}

    ratios = [
        persona_weighted_fill_ratio(p, persona)
        for p in people[:max_people]
        if isinstance(p, dict)
    ]
    if not ratios:
        return {"score": 0.0, "persona": persona, "people_scored": 0}

    avg = sum(ratios) / len(ratios)
    return {
        "score": round(avg, 4),
        "persona": persona,
        "people_scored": len(ratios),
    }


def persona_field_fill_scorer(output, expected, input, metadata):
    from braintrust import Score

    if not isinstance(output, dict):
        return Score(name="persona_field_fill", score=0.0)

    if output.get("error"):
        return Score(name="persona_field_fill", score=0.0, metadata={"reason": str(output["error"])[:200]})

    persona = judge_persona_from_metadata(metadata)
    people = _extract_people(output)
    stats = row_persona_fill_score(people, persona)
    return Score(
        name="persona_field_fill",
        score=stats["score"],
        metadata={
            "provider": output.get("provider"),
            "person_count": output.get("person_count") or len(people),
            **stats,
        },
    )
