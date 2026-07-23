"""Deterministic field-fill richness scorer for normalized people[] output."""

from __future__ import annotations

TRACKED_FIELDS: tuple[str, ...] = (
    "displayname",
    "current_title",
    "current_company",
    "location",
    "profile_url",
    "highlight",
    "email",
    "phone",
    "skills",
    "insights",
    "confidence",
)

MAX_FIELDS = len(TRACKED_FIELDS)


def _is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        s = value.strip()
        return bool(s) and s not in ("?", "—", "-", "null", "None")
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    if isinstance(value, bool):
        return value
    return True


def _person_field_values(person: dict) -> dict[str, object]:
    skills = person.get("top_skills") or []
    insights = person.get("insights") or {}
    confidence = person.get("confidence")
    if confidence is None and isinstance(person.get("likelihood"), (int, float)):
        confidence = {"likelihood": person["likelihood"]}

    email = person.get("best_work_email") or person.get("best_personal_email")
    if not email and person.get("has_email"):
        email = "present"
    if not email and person.get("altemails"):
        email = person["altemails"][0]

    phones = person.get("phones") or []
    phone = phones[0] if phones else None
    if not phone and person.get("has_phone"):
        phone = "present"

    url = person.get("linkedin_url") or person.get("url")

    return {
        "displayname": person.get("displayname"),
        "current_title": person.get("current_title") or person.get("headline"),
        "current_company": person.get("current_company"),
        "location": person.get("location"),
        "profile_url": url,
        "highlight": person.get("highlight"),
        "email": email,
        "phone": phone,
        "skills": skills if isinstance(skills, list) and skills else None,
        "insights": insights if isinstance(insights, dict) and insights else None,
        "confidence": confidence,
    }


def person_fill_ratio(person: dict) -> tuple[float, int]:
    values = _person_field_values(person)
    filled = sum(1 for key in TRACKED_FIELDS if _is_filled(values.get(key)))
    return filled / MAX_FIELDS, filled


def row_fill_score(people: list | None, *, max_people: int = 5) -> dict:
    if not people:
        return {
            "score": 0.0,
            "avg_ratio": 0.0,
            "avg_fields_per_person": 0.0,
            "people_scored": 0,
            "total_filled": 0,
        }

    ratios: list[float] = []
    counts: list[int] = []
    for person in people[:max_people]:
        if not isinstance(person, dict):
            continue
        ratio, count = person_fill_ratio(person)
        ratios.append(ratio)
        counts.append(count)

    if not ratios:
        return {
            "score": 0.0,
            "avg_ratio": 0.0,
            "avg_fields_per_person": 0.0,
            "people_scored": 0,
            "total_filled": 0,
        }

    avg_ratio = sum(ratios) / len(ratios)
    return {
        "score": round(avg_ratio, 4),
        "avg_ratio": round(avg_ratio, 4),
        "avg_fields_per_person": round(sum(counts) / len(counts), 2),
        "people_scored": len(ratios),
        "total_filled": sum(counts),
    }


def _extract_people(output: dict) -> list:
    people = output.get("people") or []
    if not people and isinstance(output.get("summary"), dict):
        summary = output["summary"]
        people = summary.get("people") or []
        if summary.get("person") and not people:
            people = [summary["person"]]
    return people


def field_fill_scorer(output, expected, input, metadata):
    from braintrust import Score

    if not isinstance(output, dict):
        return Score(name="field_fill", score=0.0)

    if output.get("error"):
        return Score(name="field_fill", score=0.0, metadata={"reason": str(output["error"])[:200]})

    people = _extract_people(output)
    stats = row_fill_score(people)
    return Score(
        name="field_fill",
        score=stats["score"],
        metadata={
            "provider": output.get("provider"),
            "person_count": output.get("person_count") or len(people),
            **stats,
        },
    )
