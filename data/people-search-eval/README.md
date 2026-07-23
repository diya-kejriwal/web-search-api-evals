# People Search Eval

240-query people-search benchmark (6 personas × 40) for Braintrust.

## Layout

```
data/people-search-eval/
├── dataset/                 # query set
│   └── full_provider_benchmark.json
├── scorers/                 # build / publish judges + deterministic scorers
│   ├── prompts/
│   ├── field_fill_scorer.py
│   ├── persona_field_fill_scorer.py
│   └── publish_scorers.py
└── eval/                    # run evals
    ├── run_nyne.py
    ├── run_pdl.py
    ├── run_exa.py
    └── lib/                 # shared runner helpers
```

See [SCORERS.md](SCORERS.md) for scorer design.

## Setup

```bash
cd data/people-search-eval
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Provider clients (Nyne / PDL / Exa)
pip install -e ../../../people-search-eval
# or: export PEOPLE_SEARCH_EVAL_SRC=/path/to/people-search-eval/src

cp .env.example .env   # set API keys
python scorers/publish_scorers.py
```

## Run

```bash
python eval/run_nyne.py --local-dataset --limit 3 --no-send-logs --low-credits
python eval/run_pdl.py --local-dataset --limit 3 --no-send-logs
python eval/run_exa.py --local-dataset --limit 3 --no-send-logs

python eval/run_nyne.py --project people-data-provider-evals --dataset full_provider_benchmark --low-credits
```
