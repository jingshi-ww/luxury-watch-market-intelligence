# Luxury Watch Secondary Market Analysis

An analytical project exploring brand-level market presence, Rolex resale-price premiums, reference-level concentration, and differences between public search interest and searchable marketplace inventory.

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
