# Luxury Watch Secondary Market Analysis

An analytical project exploring brand-level market presence, Rolex resale-price premiums, reference-level concentration, and differences between public search interest and searchable marketplace inventory.


## RNCP37827BC01 — technical evidence map

This repository documents a data collection, preparation, storage and exposure workflow developed for the **RNCP37827BC01** assessment. The four-page Streamlit application is the analytical interface; the assessed data-engineering work is primarily in `src/`, `api/` and `tests/`.

| Competency | Evidence in this repository | Scope |
| --- | --- | --- |
| **C1 — Collecte** | `src/collect.py`, `src/collect_ebay.py`, `src/collect_google_trends.py` | Parsing saved Chrono24 HTML, eBay Browse API retrieval and Google Trends collection. The historical Kaggle files are separately sourced. |
| **C2 — Préparation** | `src/prepare.py`, `src/prepare_rolex_premium.py`, `src/prepare_rolex_visibility.py` | Cleaning, matching and preparation of distinct listing datasets. |
| **C3 — Agrégation** | `src/prepare_ebay_attention.py`, preparation scripts, `notebooks/` | Derived market indicators and brand/reference-level comparisons. See methodological limitations below. |
| **C4 — Stockage** | `src/store.py`, `src/sql_check.py` | Local SQLite database populated from available processed files. The database file is not distributed here. |
| **C5 — Mise à disposition** | `api/main.py`, `pages/4_🧩_Data_Pipeline.py` | FastAPI endpoints and auto-generated OpenAPI documentation (`/docs`); Streamlit also reads local CSVs directly. |

**Important:** This evidence map identifies the relevant code; it does not assert that every workflow is fully reproducible from a fresh clone or that the API has authentication enabled. See the setup and data-availability notes below.

## Repository layout

```text
Luxury_Watch_Market.py     Streamlit entry point
pages/                     Four Streamlit analysis/architecture pages
notebooks/                 Five exploratory and dataset-building notebooks
src/                       Collection, preparation, storage and checks
api/main.py                FastAPI application
tests/test_pipeline.py      Lightweight pipeline tests
.streamlit/config.toml     Streamlit appearance settings
.env.example               Environment-variable placeholders (no credentials)
requirements.txt           Python dependencies
```

## Dashboard

1. **Market Concentration** — historical cross-brand listing patterns, Google Trends attention, and a standardized eBay Browse API retrieval sample.
2. **Rolex Premium Formation** — material, dial, production-period and complication comparisons, plus listing visibility patterns.
3. **Speculative References** — historical Rolex reference-level premium concentration and a separate current Chrono24 market cross-check.
4. **Data Pipeline & API Architecture** — data lineage, preparation scripts, SQLite storage and API endpoints.

## Data sources and analytical roles

| Source | Link / collection method | Role |
| --- | --- | --- |
| **Luxury Watch Listings** (Kaggle, philmorekoung11) | https://www.kaggle.com/datasets/philmorekoung11/luxury-watch-listings | Historical cross-brand listings (`Watches.csv`); basis for `global_watch_market.csv` and `rolex_historical_market.csv`. |
| **Rolex Watch Listings** (Kaggle, jaepin) | https://www.kaggle.com/datasets/jaepin/rolex-watch-listings/data | Repeated Rolex listing observations across CSV files; used for feature-level premiums and visibility. |
| **Rolex Retail Prices** (Kaggle, vittoriohaardt) | https://www.kaggle.com/datasets/vittoriohaardt/rolex-retail-prices | Third-party original list-price reference table; matched by Rolex reference to estimate resale premiums. Not presented as an official Rolex feed. |
| **Chrono24** | Locally saved HTML pages parsed by `src/collect.py` | Separate contemporary Rolex market cross-check; not a direct replication of historical reference results. |
| **eBay Browse API** | `src/collect_ebay.py` | Live standardized searchable-inventory sample, capped at 200 returned items per brand query. Not total marketplace inventory or market share. |
| **Google Trends** | `src/collect_google_trends.py` using `pytrends` | Relative public search-interest proxy, not purchase demand or sales volume. |

### Why two historical Rolex datasets?

`rolex_historical_market.csv` is derived from the broad historical marketplace dataset and is used for **Page 3 reference-level comparisons**. `rolex_premium_analysis.csv` is constructed from repeated Rolex listing observations matched with the separate Kaggle retail-price reference and is used for **Page 2 feature-level premium analysis**. These datasets have different observation structures and should not be pooled or treated as interchangeable.

Daily listing records can recur across dates. Page 2's daily observations and persistence metrics are therefore **visibility-weighted**, not counts of distinct watches or verified sales. The resale premium is computed as `(observed listing price - matched reference list price) / matched reference list price * 100`; it is an **asking-price premium**, not a realized transaction return.

## Architecture

`raw files / API retrieval → src/ collection and preparation scripts → data/processed/*.csv → src/store.py → data/database/watch_market.db → FastAPI → Streamlit`

The Streamlit dashboard also reads selected processed CSVs directly; its live eBay section calls the local FastAPI server when available. The `/speculative-references` API endpoint currently aggregates the daily premium table, whereas Page 3 uses the separate historical marketplace table. They are not identical analytical outputs.


### Data availability and reproducibility

The public GitHub repository deliberately **excludes** `data/raw/`, `data/processed/` and `data/database/` through `.gitignore`. This keeps large third-party datasets, generated CSVs and the local SQLite file out of version control. The five notebooks are included with their saved analytical outputs.

A fresh clone therefore **does not contain the data required to run every dashboard page or query the populated database immediately**. To reproduce a particular analysis, obtain the relevant historical Kaggle dataset(s) from the links above, subject to their licensing and access conditions, and place the source files in the paths expected by the corresponding notebook or preparation script. Some notebooks/scripts use locally prepared inputs and may require path adjustments. Existing processed CSVs can also be supplied locally if available.

- **Historical Kaggle inputs:** downloaded separately; not automatically fetched by the installation commands.
- **Chrono24:** the collector parses locally saved HTML; this repository does not promise an automated live Chrono24 download.
- **eBay Browse API:** can request a fresh limited sample with valid credentials, but does not recreate the historical marketplace datasets.
- **Google Trends:** collected separately through `pytrends`; results can change with time and service availability.
- **SQLite:** `python src/store.py` loads available processed CSVs; it cannot reconstruct missing historical input data on its own.

Do not publish private credentials or assume that data obtained at different dates is directly comparable.

## Setup

Run these commands **from the `project/` directory** with Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

The repository/archive needs the relevant raw files and/or existing processed CSVs under `data/` for all analyses to work. Kaggle source files are not downloaded automatically by these commands.

For live eBay refresh, create a local `.env` from `.env.example` and set valid eBay production API credentials. **Never commit or share `.env`.** A refresh requires network access and working credentials.

If the processed CSVs already exist, build or update SQLite with:

```bash
python src/store.py
```

In **terminal 1**, start the API:

```bash
python -m uvicorn api.main:app --reload
```

Check http://127.0.0.1:8000/ and interactive docs at http://127.0.0.1:8000/docs . The `/data-sources` endpoint returns a declared table list; it does not itself verify the existence or row counts of each SQLite table.

In **terminal 2**, start the dashboard:

```bash
python -m streamlit run Luxury_Watch_Market.py
```

The Streamlit eBay refresh button invokes `POST /refresh-ebay-market`, which runs `src/collect_ebay.py`, `src/prepare_ebay_attention.py`, then `src/store.py`. This updates the eBay-related CSVs and reloads available processed tables into SQLite. Other historical data is not automatically re-collected.


### API route reference

FastAPI's interactive documentation is available at `http://127.0.0.1:8000/docs` when the server is running. The project defines the following routes (consult `api/main.py` for the precise response schemas and runtime prerequisites):

| Method | Route | Intended purpose |
| --- | --- | --- |
| GET | `/` | API status/root response |
| GET | `/market-concentration` | Brand-level market indicators |
| GET | `/brand-attention` | Google Trends attention indicators |
| GET | `/ebay-inventory` | eBay sample indicators |
| POST | `/refresh-ebay-market` | Refresh the eBay-related collection/preparation/storage workflow |
| GET | `/rolex-premium-formation` | Rolex premium indicators |
| GET | `/speculative-references` | Reference-level metrics from the API's daily-premium source |
| GET | `/data-sources` | Declared data-source/table inventory, not a database integrity check |

The existence of Swagger documentation **does not by itself imply authentication or production-grade API security**. Security controls must be assessed from the actual API implementation.

## Validation

```bash
python -m unittest discover -s tests -v
```

These lightweight checks validate project structure and, when a local SQLite database exists, verify expected tables. They do **not** establish statistical validity, completeness of source data, or live API availability.

## Interpretation limits

- Historical listings, repeated daily observations, and current API/scraped samples are **different populations and periods**.
- Listing counts indicate marketplace presence, not transaction liquidity or sales.
- Retail-price matching depends on reference coverage and the provenance/accuracy of the third-party price table.
- eBay retrieval saturation is relative to a controlled query window, not a brand's total eBay or global market share.
- Google Trends is a relative search-attention signal, not a direct demand measure.
