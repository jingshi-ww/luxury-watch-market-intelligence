# RNCP37827BC01 — Technical Evidence Index

This document supplements the French-language PDF assessment report submitted separately to the evaluation panel. It maps competencies C1–C5 to the repository's technical implementation, summarizes previous local data-validation results, and identifies reproducibility and methodological limitations.

## Competency Mapping

| Competency | Repository evidence | Technical implementation |
| --- | --- | --- |
| **C1 — Automated Data Collection** | `src/collect_ebay.py`, `src/collect_google_trends.py`, `src/collect.py` | eBay Browse API collection using OAuth credentials, Google Trends retrieval through `pytrends`, and parsing of locally saved Chrono24 HTML files. |
| **C2 — Data Preparation** | `src/prepare.py`, `src/prepare_ebay_attention.py`, `src/prepare_rolex_premium.py`, `src/prepare_rolex_visibility.py` | Column standardization, numeric price conversion, missing-value handling, reference extraction, data enrichment, and preparation of analytical datasets. |
| **C3 — Data Aggregation** | `src/prepare_ebay_attention.py`, Rolex preparation scripts, `notebooks/` | Brand-level inventory aggregation, price statistics, Google Trends attention comparisons, Rolex premium calculations, and listing-visibility summaries. |
| **C4 — Database Creation** | `src/store.py`, `src/build_relational_model.py`, `src/sql_check.py`, `docs/C4_modele_relationnel.md`, `sql_queries.sql` | SQLite analytical storage and a complementary three-table relational model using primary keys, foreign keys, constraints, and integrity checks. |
| **C5 — Data Access via API** | `api/main.py`, `tests/test_api_security.py`, `tests/test_relational_model.py` | FastAPI analytical GET endpoints, Swagger/OpenAPI documentation at `/docs`, and an eBay refresh POST endpoint protected by an `X-API-Key` header. |

## Local Data Validation Results

The following figures originate from previous checks performed on local datasets and database snapshots. They are not recalculated automatically from a fresh public repository clone.

- **Historical dataset (`Watches.csv`):** 284,491 rows before and after preparation; 14,665 missing or non-convertible prices after conversion (5.15%); 43,152 missing references.
- **Archived eBay CSV sample:** 964 rows retained in the documented validation, with no duplicate `item_url` within that snapshot.
- **Separate eBay refresh on October 9, 2026:** 925 listings. These two eBay figures represent separate collection runs.
- **Historical SQLite validation (`global_watch_market`):** Rolex — 68,798; Omega — 38,909; Seiko — 18,887; Breitling — 17,019; Cartier — 15,877 records with valid prices.
- **Archive comparison:** Historical CSV files and preparation scripts were identical in the October 7 and October 9, 2026 working archives, while the SQLite database files differed.

The SQL queries used for historical market checks are provided in [`sql_queries.sql`](sql_queries.sql). Their execution requires the relevant local database tables and data.

## Relational Model and Data Scope

The main SQLite database stores nine analytical tables generated from processed CSV datasets.

A separate relational layer is implemented through `src/build_relational_model.py`, containing:

- `dim_brand`: brand identifiers, names, and market segments.
- `fact_ebay_market`: brand-level eBay listing counts and price statistics.
- `fact_brand_attention`: brand-level Google Trends attention indicators.

The relational layer uses a one-record-per-brand snapshot structure, with primary and foreign key constraints. The implementation checks for duplicate brands, mismatched brand sets, inconsistent market segments, and foreign key violations.

This supplementary relational model is not automatically rebuilt by the eBay refresh endpoint. After updating the source tables, `python src/build_relational_model.py` must be executed separately.

## Methodological Limitations

- Marketplace listings represent advertised offers, not completed sales.
- The historical 15-brand ranking and the eight-brand eBay/Google Trends analysis use different analytical populations.
- eBay API results are limited by the collection window and query configuration; listing counts do not represent total marketplace inventory or market share.
- Google Trends provides relative search-attention indicators rather than sales or verified purchase demand.
- Repeated Rolex listing URLs across different dates may represent valid temporal observations rather than duplicate records.
- Rolex retail-price matching relies on a third-party reference-price table that may contain multiple entries per reference. Premium estimates are therefore exploratory and may be affected by one-to-many matching.
- The relational model represents an aggregated brand snapshot, not a transaction-level or multi-date relational warehouse.

## Execution and Reproducibility

From the repository root, after installing dependencies and supplying the required local input datasets:

```bash
python src/store.py
python src/build_relational_model.py
python -m unittest discover -s tests -v
python -m uvicorn api.main:app --reload
```

The public repository does not include the large raw datasets, generated CSV files, or local SQLite database needed to reproduce every analytical result.

The API security implementation requires the `WATCH_API_KEY` environment variable for authorization of `POST /refresh-ebay-market`. Requests with a missing or invalid `X-API-Key` are rejected with HTTP 403.

The repository includes automated tests covering API authorization and relational-model integrity. A previous local validation reported 11 passing tests; this result has not been independently rerun as part of the present repository review.

Never commit `.env`, eBay client credentials, API keys, or the local SQLite database to the public repository.
