# UK Company Risk Pipeline

A data engineering project that builds a pipeline on UK Companies House data, working towards
a simple, explainable **payment-risk score**: a way for small businesses to check whether a
customer is likely to pay on time before giving them credit.

The idea comes from my experience in credit control: chasing late payers and reconciling payments.

## What the pipeline does

| Stage | Script | What it does |
|---|---|---|
| Ingest (API) | `src/fetch_companies.py` | Calls the Companies House REST API with retries and rate limiting; saves raw JSON |
| Ingest (bulk) | `src/load_bulk.py` | Loads the monthly snapshot of all live UK companies (5.7m rows) from CSV to Parquet |
| Clean | `src/clean_bulk.py` | Converts types, groups 14 inconsistent status labels into 5, extracts industry and postcode area, derives risk signals |
| Test | `tests/test_clean_quality.py` | Automated data-quality checks: row counts, uniqueness, missing values, valid dates |

## Findings so far (snapshot: 1 October 2026)

- **5,704,711** live companies loaded. Converting the 2.7 GB CSV to Parquet cut it to 411 MB, about 85% smaller.
- **Overdue accounts are a strong warning sign:** only 1.8% of active companies are late filing
  their accounts, compared with 58% of companies facing strike-off and 89% of those in liquidation.
- **Survivorship bias:** the snapshot only contains companies still alive, so older incorporation
  years look smaller because many of their companies have since closed. Trends over time need
  dissolved-company data too.

## Tech stack

Python · SQL · DuckDB · pandas · Parquet · pytest · Git · GitHub Codespaces

## Project structure

    src/      pipeline scripts
    tests/    data-quality tests
    data/     local data (not committed to Git)

## How to run

1. Get a free API key from the Companies House developer hub and store it as `CH_API_KEY`.
2. `pip install -r requirements.txt`
3. Download the monthly snapshot from Companies House into `data/raw/bulk/` and unzip it.
4. Run `python src/load_bulk.py`, then `python src/clean_bulk.py`, then `pytest -v`.

## Data protection

This project uses company-level data only. Personal details of company officers and owners are
not stored in the repository or shown in any outputs, and the API key is kept as a secret,
never in code.

## Roadmap

- [ ] Move storage to Azure Data Lake and processing to Databricks
- [ ] Capture live company changes from the Companies House streaming API
- [ ] Extract key figures from filed accounts
- [ ] Build the payment-risk score and a dashboard
- [ ] Automate tests with GitHub Actions