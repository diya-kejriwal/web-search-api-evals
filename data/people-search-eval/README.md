# People Search Eval

240-query people-search benchmark for Braintrust across **Nyne**, **PDL**, and **Exa**.

- **6 personas** × 40 queries each (15 enrichment + 25 search → **90 enrichment / 150 search**)
- **Deterministic scorers** — `has_people`, `field_fill`, `persona_field_fill`
- **LLM judges** — `people-judge-overall`, `people-judge-persona` (see [SCORERS.md](SCORERS.md))

**Results:** [Braintrust experiments (people-data-provider-evals)](https://www.braintrust.dev/app/you.com-staging/p/people-data-provider-evals/experiments)

## Layout

```
data/people-search-eval/
├── dataset/
│   ├── full_provider_benchmark.json   # query set (Braintrust-ready)
│   └── upload_to_braintrust.py        # upload dataset to Braintrust
├── scorers/
│   ├── prompts/                       # LLM judge prompts
│   ├── field_fill_scorer.py
│   ├── persona_field_fill_scorer.py
│   └── publish_scorers.py             # publish judges to Braintrust
├── eval/
│   ├── run_nyne.py
│   ├── run_pdl.py
│   ├── run_exa.py
│   └── lib/                           # shared routing + runner helpers
├── .env.example
├── requirements.txt
└── SCORERS.md
```

## Prerequisites

1. **Python** ≥ 3.10  
2. **Provider client package** — Nyne / PDL / Exa HTTP clients live in a separate checkout of `people-search-eval` (not vendored here). Clone it next to this repo (or anywhere) and install it editable.  
3. **API keys** for the providers you want to run + Braintrust.

Typical sibling layout:

```
Repo Clones/
├── web-search-api-evals/          # this repo
│   └── data/people-search-eval/
└── people-search-eval/            # provider clients
```

## Setup

From the `web-search-api-evals` repo root:

```bash
cd data/people-search-eval
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Install provider clients (adjust path if your checkout differs)
pip install -e ../../../people-search-eval
# Alternative: export PEOPLE_SEARCH_EVAL_SRC=/absolute/path/to/people-search-eval/src

cp .env.example .env
```

Edit `.env` and set at least:

| Variable | Needed for |
|----------|------------|
| `NYNE_API_KEY`, `NYNE_API_SECRET` | Nyne runs |
| `PDL_API_KEY` | PDL runs |
| `EXA_API_KEY` | Exa runs |
| `BRAINTRUST_API_KEY` | Dataset upload, experiments, LLM judges |

Defaults already set for low-cost Nyne runs (`NYNE_INSIGHTS=0`, `NYNE_SEARCH_LIMIT=5`, etc.). See `.env.example` for the full list.

### Publish LLM judges (once per Braintrust project)

```bash
python scorers/publish_scorers.py
# Dry run: python scorers/publish_scorers.py --dry-run
```

This creates / replaces `people-judge-overall` and `people-judge-persona` in the project named by `BRAINTRUST_PROJECT` (default: `people-data-provider-evals`).

## Run evals

All runs use the **Braintrust cloud dataset** (including smoke tests). Do this once first, then run any of the commands below.

```bash
cd data/people-search-eval
source .venv/bin/activate
```

### 1. Upload the dataset to Braintrust

```bash
python dataset/upload_to_braintrust.py
# Dry run: python dataset/upload_to_braintrust.py --dry-run
```

This upserts all 240 rows into project `people-data-provider-evals`, dataset `full_provider_benchmark`.

You can also upload manually in the Braintrust UI: create a dataset named `full_provider_benchmark` in that project and import `dataset/full_provider_benchmark.json`.

### 2. Smoke test (cloud, 3 rows)

```bash
python eval/run_nyne.py --project people-data-provider-evals --dataset full_provider_benchmark --limit 3 --low-credits
python eval/run_pdl.py  --project people-data-provider-evals --dataset full_provider_benchmark --limit 3
python eval/run_exa.py  --project people-data-provider-evals --dataset full_provider_benchmark --limit 3
```

### 3. Full run (cloud, all 240 rows)

```bash
python eval/run_nyne.py --project people-data-provider-evals --dataset full_provider_benchmark --low-credits
python eval/run_pdl.py  --project people-data-provider-evals --dataset full_provider_benchmark
python eval/run_exa.py  --project people-data-provider-evals --dataset full_provider_benchmark
```

Experiments appear here:  
https://www.braintrust.dev/app/you.com-staging/p/people-data-provider-evals/experiments

### Nyne routing audit (no API calls)

Prints how rows map to Nyne endpoints without calling providers. Still reads the cloud dataset metadata path via `--dataset` defaults after upload; for a local file audit only:

```bash
python eval/run_nyne.py --routing-audit --local-dataset
```

## Useful flags

| Flag | Meaning |
|------|---------|
| `--project NAME` | Braintrust project (default: `people-data-provider-evals`) |
| `--dataset NAME` | Braintrust cloud dataset (default: `full_provider_benchmark`) |
| `--limit N` | Run only the first N rows |
| `--no-send-logs` | Do not upload the experiment to Braintrust |
| `--no-llm-judges` | Deterministic scorers only (skip Braintrust LLM judges) |
| `--low-credits` | Nyne only: insights/profile scoring off, search limit 5 |
| `--concurrency N` | Parallel task concurrency |
| `--overall-judge` / `--persona-judge` | Override Braintrust scorer slugs |

## Scorers

Each run scores with:

1. **Deterministic** — `has_people`, `field_fill`, `persona_field_fill`  
2. **LLM judges** (unless `--no-llm-judges`) — overall + persona-switched prompts from `scorers/prompts/`

Details and calibration notes: [SCORERS.md](SCORERS.md).
