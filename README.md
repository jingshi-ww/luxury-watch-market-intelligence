# Luxury Watch Secondary Market Analysis

An analytical and data-engineering project exploring brand-level market presence, Rolex resale-price premiums, reference-level concentration, and differences between public search interest and searchable marketplace inventory.

The project combines historical marketplace datasets, API-based collection, data preparation, SQLite storage, a secured FastAPI refresh endpoint, and an interactive Streamlit dashboard.

## RNCP37827BC01 — Technical Evidence Map

This repository documents a data collection, preparation, aggregation, storage and exposure workflow developed for the **RNCP37827BC01** assessment.

The four-page Streamlit application provides the analytical interface. The assessed data-engineering work is primarily implemented in `src/`, `api/`, `tests/` and `docs/`.

| Competency | Evidence in this repository | Scope |
| --- | --- | --- |
| **C1 — Collecte** | `src/collect.py`, `src/collect_ebay.py`, `src/collect_google_trends.py` | Parsing saved Chrono24 HTML, retrieving eBay Browse API samples and collecting Google Trends data. Historical Kaggle datasets are sourced separately. |
| **C2 — Préparation** | `src/prepare.py`, `src/prepare_rolex_premium.py`, `src/prepare_rolex_visibility.py` | Data cleaning, type conversion, reference matching and preparation of distinct analytical datasets. |
| **C3 — Agrégation** | `src/prepare_ebay_attention.py`, other preparation scripts, `notebooks/` | Brand-level and reference-level aggregations, resale-premium indicators and attention/inventory comparisons. |
| **C4 — Stockage** | `src/store.py`, `src/build_relational_model.py`, `src/sql_check.py`, `docs/C4_modele_relationnel.md`, `tests/test_relational_model.py` | SQLite analytical storage complemented by a relational model with primary keys, foreign keys and integrity checks. |
| **C5 — Mise à disposition** | `api/main.py`, `tests/test_api_security.py`, Streamlit dashboard | FastAPI data endpoints, Swagger/OpenAPI documentation, and API-key protection for the eBay refresh operation. |

**Scope:** The repository provides evidence of the implemented workflow. It does not claim full reproducibility from a fresh clone without the required external datasets, nor production-grade API security.

## Repository Layout

```text
Luxury_Watch_Market.py          Streamlit entry point
pages/                          Four Streamlit analysis/architecture pages
notebooks/                      Exploratory and dataset-building notebooks
src/                            Collection, preparation, storage and validation
src/store.py                    SQLite analytical-table loader
src/build_relational_model.py   C4 relational-model builder
api/main.py                     FastAPI application
docs/C4_modele_relationnel.md   C4 relational-model documentation
tests/                          Pipeline, relational-model and API-security tests
.streamlit/config.toml          Streamlit appearance settings
.env.example                    Environment-variable placeholders
requirements.txt                Python dependencies
README.md                       Project documentation
```

## Dashboard

The Streamlit application contains four analytical pages.

### 1. Market Concentration

The first page distinguishes three analytical scopes:

- **Exploratory historical market overview:** the 15 brands with the highest listing counts in the broad historical dataset.
- **Selected-brand comparative analysis:** eight purposively selected brands representing different analytical market positions.
- **eBay API market sample:** a separately collected, standardized searchable-inventory sample.

The Top 15 historical chart queries FastAPI and SQLite when available, with a full historical CSV fallback. It does not follow the eight-brand sidebar filters.

The selected-brand KPIs and comparative charts respond to the segment, brand and price filters.

The eight brands are:

| Project-defined market segment | Selected brands |
| --- | --- |
| Accessible luxury | TAG Heuer, Longines |
| Broad premium | Omega, Cartier |
| High prestige | Rolex |
| Collector prestige | Patek Philippe, Audemars Piguet |
| Ultra-prestige niche | Richard Mille |

These segments are **analytical categories defined for this project**, not official or universally accepted industry classifications.

The eight-brand comparison is a purposive analytical sample intended to compare different market positions. It should not be interpreted as a statistically representative sample of the global luxury watch market.

### 2. Rolex Premium Formation

Analysis of resale asking-price premiums across selected Rolex characteristics, including materials, dials, production periods and complications.

The page also examines listing visibility using repeated observations.

### 3. Speculative References

Historical Rolex reference-level comparisons, premium concentration and a separate contemporary Chrono24 market cross-check.

Historical and contemporary observations are interpreted separately.

### 4. Data Pipeline & API Architecture

Overview of data sources, collection and preparation workflows, SQLite storage, FastAPI endpoints and the relationship between the data pipeline and the dashboard.

## Data Sources and Analytical Roles

| Source | Link / collection method | Analytical role |
| --- | --- | --- |
| **Luxury Watch Listings** — Kaggle, philmorekoung11 | https://www.kaggle.com/datasets/philmorekoung11/luxury-watch-listings | Historical cross-brand listings (`Watches.csv`), used for the broad market overview and historical Rolex reference comparisons. |
| **Rolex Watch Listings** — Kaggle, jaepin | https://www.kaggle.com/datasets/jaepin/rolex-watch-listings/data | Repeated Rolex listing observations used for feature-level premium and visibility analysis. |
| **Rolex Retail Prices** — Kaggle, vittoriohaardt | https://www.kaggle.com/datasets/vittoriohaardt/rolex-retail-prices | Third-party original list-price reference table used to estimate resale premiums. Not an official Rolex price feed. |
| **Chrono24** | Locally saved HTML parsed by `src/collect.py` | Separate contemporary Rolex market cross-check. |
| **eBay Browse API** | `src/collect_ebay.py` | Refreshable standardized searchable-inventory sample, capped at 200 retrieved listings per brand query. |
| **Google Trends** | `src/collect_google_trends.py` using `pytrends` | Relative public search-interest indicator, not verified demand or sales volume. |

### Why Two Historical Rolex Datasets?

`rolex_historical_market.csv` is derived from the broad historical marketplace dataset and supports Page 3 reference-level comparisons.

`rolex_premium_analysis.csv` is constructed from repeated Rolex listing observations matched with a separate third-party retail-price reference table. It supports Page 2 feature-level premium analysis.

These datasets have different observation structures and should not be pooled or treated as interchangeable.

Daily listing records may recur across dates. Page 2's daily observations and persistence metrics are therefore **visibility-weighted**, not counts of distinct watches or verified sales.

The resale premium is calculated as:

```text
Premium (%) =
(observed listing price - matched reference list price)
÷ matched reference list price × 100
```

This is an **asking-price premium**, not a realized transaction return or investment performance measure.

## Data Architecture

The main analytical pipeline is:

```text
Historical files / saved HTML / API collection
                    |
                    v
        Collection and preparation
                    |
                    v
           data/processed/*.csv
                    |
                    v
             src/store.py
                    |
                    v
       SQLite analytical tables
                    |
          +---------+---------+
          |                   |
          v                   v
       FastAPI          Streamlit CSV
          |             consumption
          v
       Streamlit
```

A complementary C4 relational model is built from the available processed data and stored in the same SQLite database.

The dashboard uses a hybrid data-access approach:

- Some analytical components read processed CSV files directly.
- Selected components query FastAPI, which reads SQLite.
- The eBay refresh button calls a protected FastAPI endpoint.

The `/speculative-references` API endpoint currently aggregates the daily premium dataset, whereas Page 3 uses the separate historical marketplace dataset. These are not identical analytical outputs.

## C4 — SQLite Storage and Relational Data Model

### Analytical Storage

The main storage script is:

```bash
python src/store.py
```

It loads available processed CSV datasets into a local SQLite database:

```text
data/database/watch_market.db
```

The analytical storage layer contains nine tables created from processed datasets.

These tables support convenient analysis and API access, but the original analytical-table loader does not define primary-key and foreign-key relationships across all nine tables.

### Complementary Relational Model

To demonstrate explicit relational modelling and referential integrity, the project includes:

```bash
python src/build_relational_model.py
```

This script builds three additional relational tables:

| Table | Role |
| --- | --- |
| `dim_brand` | Brand dimension with a primary key |
| `fact_ebay_market` | Brand-level eBay market indicators linked to `dim_brand` |
| `fact_brand_attention` | Brand-level attention indicators linked to `dim_brand` |

The fact tables reference the brand dimension through `brand_id`.

The model supports SQL joins across brand-level eBay and Google Trends indicators while enforcing relational constraints.

The relational model is complementary to the nine analytical tables; it does not replace the existing dashboard data structures.

### C4 Build Sequence

Once the required processed CSV files are available:

```bash
python src/store.py
python src/build_relational_model.py
```

The second command is necessary because `src/store.py` does not automatically rebuild the three complementary relational tables.

The relational model was validated locally with eight brands, three tables and foreign-key checks.

Detailed modelling documentation, including the conceptual and logical models, is available in:

```text
docs/C4_modele_relationnel.md
```

### Why SQLite?

SQLite was selected because the project primarily handles structured, tabular analytical datasets with predictable schemas and brand-level relationships.

It provides SQL querying, joins, primary keys and foreign keys without requiring a separately managed database server.

A relational SQL database is therefore appropriate for this local analytical prototype. A NoSQL database would not offer a clear advantage for the current structured datasets and relational comparison requirements.

SQLite is not presented here as a production-scale distributed data warehouse.

## C5 — FastAPI and API Security

### API Endpoints

FastAPI exposes selected analytical datasets through HTTP endpoints.

When the API is running, interactive Swagger/OpenAPI documentation is available at:

http://127.0.0.1:8000/docs

| Method | Endpoint | Purpose | Authentication |
| --- | --- | --- | --- |
| GET | `/` | API root/status | Public |
| GET | `/market-concentration` | Historical brand-level market indicators | Public |
| GET | `/brand-attention` | Google Trends attention indicators | Public |
| GET | `/ebay-inventory` | Standardized eBay market sample indicators | Public |
| GET | `/rolex-premium-formation` | Rolex premium indicators | Public |
| GET | `/speculative-references` | Reference-level metrics from the API's daily-premium source | Public |
| GET | `/data-sources` | Declared analytical data-source inventory | Public |
| POST | `/refresh-ebay-market` | Refresh eBay collection, preparation and SQLite storage | API key required |

The `/data-sources` endpoint provides a declared list of tables; it does not independently verify the existence or row counts of every SQLite table.

### API-Key Authentication

The refresh endpoint is protected using an API key supplied in the HTTP header:

```http
X-API-Key: <your_api_key>
```

The expected key is configured locally through the environment variable:

```dotenv
WATCH_API_KEY=your_watch_api_key_here
```

The key is required for the state-changing refresh operation.

Read-only GET endpoints remain public within the locally running application.

A missing or invalid key is rejected with HTTP `403 Forbidden`.

The API-key mechanism is intended as a basic access-control measure for the local project. It is **not** presented as complete production security, user-account authentication or a substitute for HTTPS, secret management and operational controls.

### Refresh Workflow

The Streamlit button **Refresh eBay API data** sends an authenticated request to:

```http
POST /refresh-ebay-market
```

The endpoint executes the following workflow:

```text
Authenticated Streamlit request
             |
             v
      FastAPI endpoint
             |
             v
   src/collect_ebay.py
             |
             v
src/prepare_ebay_attention.py
             |
             v
       src/store.py
             |
             v
Updated eBay-related processed data
and reloaded SQLite analytical tables
```

The refresh operation updates the eBay-related data layer. It does not automatically re-download the historical Kaggle datasets or rebuild the complementary C4 relational model.

**After a successful refresh, run:**

```bash
python src/build_relational_model.py
```

This synchronizes the complementary relational tables with the updated processed data.

### Functional Validation

The API-security tests cover missing or invalid keys, correctly configured authorized access, and public read-only endpoint behavior.

The authorized refresh path is tested with mocked collection and preparation commands to avoid external network calls during automated tests.

The project has also been tested manually:

- A refresh request without a valid API key returned HTTP `403 Forbidden`.
- An authenticated refresh from Streamlit completed successfully on 9 October 2026.
- The refreshed eBay sample contained 925 retrieved listings across the eight selected brands, compared with 964 in the preceding snapshot.
- The refreshed dashboard displayed updated brand rankings and attention/inventory indicators.
- The complementary C4 relational model was subsequently rebuilt and its foreign keys verified.

The differences between refresh snapshots are not interpreted as changes in total market size because the eBay dataset is a limited retrieval sample.

## Data Availability and Reproducibility

The public GitHub repository deliberately excludes:

```text
data/raw/
data/processed/
data/database/
.env
```

These exclusions prevent the publication of large third-party datasets, generated local data, SQLite files and private credentials.

The exploratory notebooks are included with their saved analytical outputs.

**A fresh clone does not contain all data required to run every dashboard page or query a populated database immediately.**

To reproduce an analysis, obtain the relevant historical Kaggle datasets from the links above, subject to their licensing and access conditions, and place the source files in the paths expected by the corresponding notebooks or scripts.

Some notebooks and scripts rely on locally prepared inputs and may require path adjustments.

Existing processed CSVs may also be supplied locally when available.

Specific limitations:

- **Historical Kaggle datasets:** downloaded separately, not automatically retrieved during installation.
- **Chrono24:** the collector parses locally saved HTML; automated live downloading is not provided.
- **eBay Browse API:** can retrieve a new limited sample with valid credentials but cannot recreate the historical marketplace datasets.
- **Google Trends:** collected separately through `pytrends`; results depend on collection time and service availability.
- **SQLite:** `src/store.py` loads available processed files but cannot reconstruct missing source data.
- **Relational model:** `src/build_relational_model.py` requires the corresponding prepared datasets.

Do not publish private credentials or assume that datasets collected on different dates represent identical populations.

## Installation and Local Execution

Run the following commands from the `project/` directory.

Python 3.10 or later is recommended.

### 1. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`.

On macOS or Linux:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```dotenv
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
WATCH_API_KEY=your_watch_api_key_here
```

The eBay credentials must be valid for the relevant Browse API environment.

`WATCH_API_KEY` is a separate locally configured secret used to authorize the protected FastAPI refresh endpoint.

**Never commit or share `.env` or real API credentials.**

### 4. Prepare the Required Data

The installation commands do not automatically download the historical datasets.

Ensure that the required raw and/or processed files are available under `data/` before attempting to build the database or run the full dashboard.

### 5. Build SQLite

If the required processed CSV files already exist:

```bash
python src/store.py
python src/build_relational_model.py
```

The first command loads the analytical tables.

The second command creates or updates the complementary relational model.

### 6. Start FastAPI

In terminal 1:

```bash
python -m uvicorn api.main:app --reload
```

API root:

http://127.0.0.1:8000/

Swagger/OpenAPI documentation:

http://127.0.0.1:8000/docs

### 7. Start Streamlit

In terminal 2:

```bash
python -m streamlit run Luxury_Watch_Market.py
```

Open the local Streamlit URL displayed in the terminal.

### 8. Refresh eBay Data (Optional)

With FastAPI running and the required credentials configured, open the Market Concentration page and click:

**Refresh eBay API data**

The dashboard sends the configured `WATCH_API_KEY` in the `X-API-Key` header.

The operation requires network access and may fail if external API credentials, access rights, rate limits or network availability change.

After a successful refresh, rebuild the relational model:

```bash
python src/build_relational_model.py
```

## Automated Tests

Run the test suite from the project directory:

```bash
python -m unittest discover -s tests -v
```

The current test suite covers:

- Basic pipeline/project structure checks.
- Relational-model creation and integrity checks.
- API-key validation for the protected refresh endpoint.
- Authorized refresh behavior using mocked external commands.
- Public API health behavior.

At the time of the latest local validation, **11 automated tests passed**.

These tests provide implementation evidence but do not establish statistical validity, completeness of source data or continued availability of external APIs.

## Methodological Limitations

The project is designed for exploratory market intelligence rather than verified transaction-market measurement.

Key limitations include:

1. **Different source populations:** historical marketplace listings, repeated daily Rolex observations, Chrono24 snapshots and eBay API samples represent different populations and collection periods.
2. **Listings are not sales:** listing counts indicate observable marketplace presence, not transaction volume, liquidity or completed sales.
3. **Repeated observations:** daily Rolex records may represent repeated visibility of the same listing rather than distinct watches.
4. **Retail reference provenance:** premium estimates depend on reference matching and the quality of a third-party original-price dataset.
5. **API retrieval cap:** eBay saturation is measured relative to a standardized maximum of 200 retrieved listings per brand query, not total brand inventory or market share.
6. **Search interest:** Google Trends is a relative attention indicator, not a direct measure of purchasing demand.
7. **Purposive brand selection:** the eight selected brands cover project-defined market positions but do not constitute a statistically representative sample of the global market.
8. **Temporal comparability:** refreshed API results may differ from earlier snapshots because marketplace availability and collection conditions change.
9. **Local prototype:** the API and SQLite implementation demonstrate a functional analytical workflow, not a production-ready distributed platform.

## Conclusion

The project combines broad historical market exploration, selected-brand comparisons and focused Rolex analysis within a documented data-engineering workflow.

Its principal technical components include data collection from heterogeneous sources, data cleaning and aggregation, SQLite analytical storage, a complementary relational model, FastAPI data endpoints, basic API-key protection and an interactive Streamlit interface.

The resulting indicators support exploratory comparisons of listing visibility, asking-price premiums and public attention while preserving the methodological distinction between historical listings, repeated observations and limited live API samples.