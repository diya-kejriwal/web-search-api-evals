"""Unit tests for people-search field-fill scorers (no API calls)."""

import json

import pytest

from evals.processing.evaluate_answer import AnswerGrader
from evals.processing.people_search.field_fill import score_people_output


def test_score_people_output_empty():
    scores = score_people_output({"people": [], "person_count": 0}, {"persona_slug": "recruiter"})
    assert scores["has_people"] == 0.0
    assert scores["field_fill"] == 0.0
    assert scores["persona_field_fill"] == 0.0


def test_score_people_output_partial_fill():
    output = {
        "person_count": 1,
        "people": [
            {
                "displayname": "Ada Lovelace",
                "current_title": "Analyst",
                "current_company": "Analytical Engines",
                "location": "London",
                "linkedin_url": "https://example.com/ada",
            }
        ],
    }
    scores = score_people_output(output, {"persona_slug": "recruiter"})
    assert scores["has_people"] == 1.0
    assert scores["person_count"] == 1
    assert 0 < scores["field_fill"] < 1
    assert scores["persona_field_fill"] > 0


@pytest.mark.asyncio
async def test_evaluate_single_people_search_grader():
    grader = AnswerGrader()
    target = json.dumps(
        {
            "benchmark_id": "fp_001",
            "persona_slug": "recruiter",
            "query_type": "enrichment",
            "person_name": "Ada Lovelace",
            "company": "Analytical Engines",
        }
    )
    predicted = json.dumps(
        {
            "provider": "nyne",
            "person_count": 1,
            "people": [
                {
                    "displayname": "Ada Lovelace",
                    "current_title": "Analyst",
                    "current_company": "Analytical Engines",
                }
            ],
        }
    )
    result = await grader.evaluate_single_people_search(
        "Find Ada Lovelace", target, predicted
    )
    assert result["score_name"] == "is_correct"
    assert result["has_people"] == 1.0
    assert "field_fill" in result
    assert "persona_field_fill" in result
