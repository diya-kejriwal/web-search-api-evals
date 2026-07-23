# People Search Eval

240-query people-search benchmark for Braintrust across **Nyne**, **PDL**, and **Exa**.

- **6 personas** × 40 queries each (15 enrichment + 25 search → **90 enrichment / 150 search**)
- **Deterministic scorers** — `has_people`, `field_fill`, `persona_field_fill`
- **LLM judges** — `people-judge-overall`, `people-judge-persona` (see [SCORERS.md](SCORERS.md))

## Layout

```
data/people-search-eval/
├── dataset/
│   └── full_provider_benchmark.json   # query set (Braintrust-ready)
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
3. **API keys** for the providers you want to run + Braintrust (for cloud logging / LLM judges).

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
| `BRAINTRUST_API_KEY` | Uploading experiments + LLM judges |

Defaults already set for low-cost Nyne runs (`NYNE_INSIGHTS=0`, `NYNE_SEARCH_LIMIT=5`, etc.). See `.env.example` for the full list.

### Publish LLM judges (once per Braintrust project)

```bash
python scorers/publish_scorers.py
# Dry run: python scorers/publish_scorers.py --dry-run
```

This creates / replaces `people-judge-overall` and `people-judge-persona` in the project named by `BRAINTRUST_PROJECT` (default: `people-data-provider-evals`).

## Run evals

All commands below assume:

```bash
cd data/people-search-eval
source .venv/bin/activate
```

### Smoke test (local dataset, no Braintrust upload)

Uses `dataset/full_provider_benchmark.json` directly:

```bash
python eval/run_nyne.py --local-dataset --limit 3 --no-send-logs --low-credits
python eval/run_pdl.py  --local-dataset --limit 3 --no-send-logs
python eval/run_exa.py  --local-dataset --limit 3 --no-send-logs
```

### Full local run (all 240 rows, upload to Braintrust)

```bash
python eval/run_nyne.py --local-dataset --low-credits
python eval/run_pdl.py  --local-dataset
python eval/run_exa.py  --local-dataset
```

### Full cloud run (dataset already in Braintrust)

Requires the dataset `full_provider_benchmark` to exist in project `people-data-provider-evals` (upload once via Braintrust UI or your existing upload tooling):

```bash
python eval/run_nyne.py --project people-data-provider-evals --dataset full_provider_benchmark --low-credits
python eval/run_pdl.py  --project people-data-provider-evals --dataset full_provider_benchmark
python eval/run_exa.py  --project people-data-provider-evals --dataset full_provider_benchmark
```

### Nyne routing audit (no API calls)

```bash
python eval/run_nyne.py --routing-audit --local-dataset
```

## Useful flags

| Flag | Meaning |
|------|---------|
| `--local-dataset` | Load `dataset/full_provider_benchmark.json` instead of a Braintrust dataset |
| `--dataset NAME` | Use a Braintrust cloud dataset |
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
