# UK Company Risk Pipeline

![Tests](https://github.com/TinkerAILab/uk-company-risk-pipeline/actions/workflows/tests.yml/badge.svg)

A data engineering project that builds a pipeline on UK Companies House data, working towards
a simple, explainable **payment-risk score**: a way for small businesses to check whether a
customer is likely to pay on time before giving them credit.

The idea comes from my experience in credit control: chasing late payers and reconciling payments.

## What the pipeline does

| Stage | Where | What it does |
|---|---|---|
| Ingest (API) | `src/fetch_companies.py` | Calls the Companies House REST API with retries and rate limiting; saves raw JSON |
| Ingest (bulk) | `src/load_bulk.py` | Loads the monthly snapshot of all live UK companies (5.7m rows) from CSV to Parquet |
| Clean (local) | `src/clean_bulk.py` | Converts types, groups 14 inconsistent status labels into 5, extracts industry and postcode area, derives risk signals |
| Test | `tests/test_clean_quality.py` | Automated data-quality checks: row counts, uniqueness, missing values, valid dates |
| Upload | `scripts/upload_to_lake.sh` | Uploads the raw and clean snapshots to Azure Data Lake Storage |
| Bronze → silver → gold | `databricks/` | PySpark notebooks that build Delta tables and the risk score in Azure Databricks |

## Cloud pipeline (Azure + Databricks)

    Companies House  →  Codespace (Python ingest)  →  Azure Data Lake (raw / clean)
                                                           ↓
                                    Azure Databricks: bronze → silver → gold (Delta tables)

- **Azure Data Lake Storage Gen2**: `raw` and `clean` containers, uploaded by `scripts/upload_to_lake.sh`
  using a time-limited, least-privilege SAS token stored as a secret
- **Azure Databricks (serverless)** reads the lake through Unity Catalog, using an Access Connector
  (managed identity) with no keys or passwords in code
- **Bronze** (`01_explore_lake`): raw snapshot plus lineage columns (`_source_file`, `_ingested_at`)
- **Silver** (`02_silver_companies`): the cleaning logic rebuilt in PySpark; results match the DuckDB version exactly
- **Gold** (`03_gold_risk`): `company_risk` (one row per company, with score, band and reasons) and `risk_by_industry`

## Findings so far (snapshot: 1 October 2026)

- **5,704,711** live companies loaded. Converting the 2.7 GB CSV to Parquet cut it to 411 MB, about 85% smaller.
- **Overdue accounts are a strong warning sign:** only 1.8% of active companies are late filing
  their accounts, compared with 58% of companies facing strike-off and 89% of those in liquidation.
- **Survivorship bias:** the snapshot only contains companies still alive, so older incorporation
  years look smaller because many of their companies have since closed. Trends over time need
  dissolved-company data too.
- **Industry differences are small:** among industries with at least 1,000 active companies, the
  share rated Medium or High ranges from about 7% to 11.5%, so the data does not show any one
  sector as clearly riskier.

## Risk score

Each company gets a score from 0 to 100 with plain-language reasons, based on its status,
overdue accounts, overdue confirmation statement, dormancy and age.
Bands: Low (0–19), Medium (20–49), High (50+).

| Signal | Points |
|---|---|
| In liquidation or administration | 80 |
| Proposal to strike off | 50 |
| Voluntary arrangement with creditors | 40 |
| Accounts overdue | 25 |
| Confirmation statement overdue | 15 |
| Under 1 year old / 1–3 years old (only with another warning) | 15 / 8 |
| Filed as dormant | 10 |

**Version 1 → version 2:** in the first version, 1.74 million active companies were flagged
just for being under 3 years old, so the score was largely measuring newness rather than risk.
In version 2, age only adds points when another warning sign is present, which cut age flags
by 87% to 221,346.

**Limitations:** the weights are a reasoned starting point, not yet validated. The next step
is to backtest them against which companies actually close in later monthly snapshots.

## Change data capture (live updates)

`src/stream_companies.py` reads the Companies House streaming API and saves each company change
as JSON Lines, recording its timepoint so the next run resumes with no gaps. The events are
uploaded to the lake, and `databricks/04_cdc_merge` merges them into the silver table:

- **Latest event wins**: each company's newest change is applied with a Delta `MERGE`
- **Idempotent**: rerunning on the same events changes nothing
- **Full history**: every event is also kept in `silver.company_changes` for auditing and backtesting

First run (8 October 2026): 129 events covering 91 companies, with 79 existing companies
updated (including 2 that moved to proposal to strike off) and 12 newly formed companies added.

## Tech stack

Python · SQL · DuckDB · pandas · Parquet · pytest · PySpark · Delta Lake ·
Azure Data Lake Storage · Azure Databricks · Unity Catalog · Git · GitHub Codespaces

## Project structure

    src/         pipeline scripts
    scripts/     cloud upload script
    databricks/  Databricks notebooks (bronze, silver, gold)
    tests/       data-quality tests
    data/        local data (not committed to Git)

## How to run

1. Get a free API key from the Companies House developer hub and store it as `CH_API_KEY`.
2. `pip install -r requirements.txt`
3. Download the monthly snapshot from Companies House into `data/raw/bulk/` and unzip it.
4. Run `python src/load_bulk.py`, then `python src/clean_bulk.py`, then `pytest -v`.
5. Store a SAS token for the storage account as `AZ_SAS_TOKEN`, then run
   `scripts/upload_to_lake.sh 2026-10-01`.
6. In Azure Databricks, run the notebooks in `databricks/` in order.

## Data protection

This project uses company-level data only. Personal details of company officers and owners are
not stored in the repository or shown in any outputs. API keys and tokens are kept as secrets,
never in code.

## Roadmap

- [x] Move storage to Azure Data Lake and processing to Databricks
- [x] Capture live company changes from the Companies House streaming API
- [x] Extract key figures from filed accounts
- [x] Backtest the risk score against next month's snapshot
- [x] Build a dashboard on the gold tables
- [x] Automate tests with GitHub Actions