"""Configuration for people-search-eval."""

import os
from pathlib import Path

# data/people-search-eval/
ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "dataset"
DATASET_JSON = DATASET_DIR / "full_provider_benchmark.json"
DATASET_JSONL = DATASET_DIR / "full_provider_benchmark.jsonl"
BRAINTRUST_DATASET = os.environ.get("BRAINTRUST_DATASET", "full_provider_benchmark")
BRAINTRUST_PROJECT = os.environ.get("BRAINTRUST_PROJECT", "people-data-provider-evals")

PERSONA_SLUGS = {
    "Recruiter / Talent Sourcer": "recruiter",
    "SDR / BDR": "sdr",
    "Background Check / Compliance Analyst": "compliance",
    "Journalist / Investigative Researcher": "journalist",
    "Event Organizer / Community Manager": "events",
    "VC / PE / Investor": "investor",
}

PERSONA_TO_EXA_CATEGORY_GROUP = {
    "recruiter": "talent_sourcing",
    "sdr": "contact_information",
    "compliance": "identity_verification",
    "journalist": "social_media_intelligence",
    "events": "contact_information",
    "investor": "talent_sourcing",
}

PERSONA_JUDGE_SLUG = os.environ.get("BRAINTRUST_PERSONA_SCORER", "people-judge-persona")
OVERALL_JUDGE_SLUG = os.environ.get("BRAINTRUST_OVERALL_SCORER", "people-judge-overall")
