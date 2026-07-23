# SCORERS.md — people-search eval

Dataset: `dataset/full_provider_benchmark.json` (240 rows, 6 personas × 40 queries).

## Scorer layers

### Layer 1 — Deterministic (Python, free)

| Scorer | Name | Range | What it measures |
|--------|------|-------|------------------|
| `has_people` | person_count | 0 or 1 | At least one person returned |
| `field_fill` | field_fill | 0–1 | Mean fill ratio across 11 universal fields |
| `persona_field_fill` | persona_field_fill | 0–1 | Same fields, weighted by buyer persona |

**Hard rules:** `error` or `person_count=0` → deterministic scores are **0**.

### Layer 2 — LLM judges (Braintrust UI)

| Slug | Audience |
|------|----------|
| `people-judge-overall` | Cross-persona quality |
| `people-judge-persona` | Persona-switched — one prompt that applies the rubric for the row's `metadata.persona` |

Choice scores (all judges):

| Label | Score |
|-------|-------|
| High Value | 1.0 |
| Useful | 0.7 |
| Low Value | 0.3 |
| Failed | 0.0 |

**Calibration rule:** named-person `enrichment` with zero results → **Failed (0.0)**, not partial credit.

Prompt sources: `scorers/prompts/*.md`

## Setup

```bash
cd data/people-search-eval
pip install -r requirements.txt
pip install -e ../../../people-search-eval
cp .env.example .env
python scorers/publish_scorers.py
```

## Run evals

```bash
python eval/run_nyne.py --local-dataset --limit 3 --no-send-logs --low-credits
python eval/run_pdl.py --local-dataset --limit 3 --no-send-logs
python eval/run_exa.py --local-dataset --limit 3 --no-send-logs
```
