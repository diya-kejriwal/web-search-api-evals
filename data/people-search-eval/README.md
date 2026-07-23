# People Search Eval

240-query people-search benchmark (6 personas × 40) for Braintrust, with deterministic scorers and LLM judges.

## Contents

| Path | Description |
|------|-------------|
| `full_provider_benchmark.json` | Eval dataset (Braintrust-ready) |
| `scorers/prompts/` | LLM judge prompts (`overall`, `persona`) |
| `src/full_provider_eval/scorers/` | Deterministic scorers (`field_fill`, `persona_field_fill`) |
| `publish_scorers.py` | Publish LLM judges to Braintrust |
| `eval_*_braintrust.py` | Run Nyne / PDL / Exa evals |

See [SCORERS.md](SCORERS.md) for scorer design.

## Setup

```bash
cd data/people-search-eval
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Provider clients (Nyne / PDL / Exa) live in the sibling people-search-eval package
pip install -e ../../../people-search-eval
# or: export PEOPLE_SEARCH_EVAL_SRC=/path/to/people-search-eval/src

cp .env.example .env   # set API keys
python publish_scorers.py
```

## Run

```bash
# Smoke test (local dataset, no Braintrust upload)
python eval_nyne_braintrust.py --local-dataset --limit 3 --no-send-logs --low-credits
python eval_pdl_braintrust.py --local-dataset --limit 3 --no-send-logs
python eval_exa_braintrust.py --local-dataset --limit 3 --no-send-logs

# Full cloud run (dataset must be uploaded to Braintrust as full_provider_benchmark)
python eval_nyne_braintrust.py --project people-data-provider-evals --dataset full_provider_benchmark --low-credits
```
