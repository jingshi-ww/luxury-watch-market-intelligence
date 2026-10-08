import streamlit as st
import pandas as pd
from pathlib import Path
import sqlite3
import requests

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Data Pipeline",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "database" / "watch_market.db"
API_BASE_URL = "http://127.0.0.1:8000"

# =========================
# TITLE
# =========================
st.title("4. Data Pipeline & API Architecture")

st.markdown("""
This page documents how the project data pipeline was built, from raw data collection
to processed analytical datasets, SQLite storage, FastAPI endpoints and Streamlit visualization.
""")

st.info("""
The project combines historical marketplace data, Rolex-specific premium reconstruction,
custom Chrono24 scraping, Google Trends attention data, and an eBay API retrieval layer.
""")

# =========================
# PIPELINE OVERVIEW
# =========================
st.subheader("Pipeline Overview")

st.code("""
Raw data sources
│
├── Kaggle / Luxury Watch Listings
│   └── Historical luxury watch marketplace listings used for cross-brand
│       market structure and Rolex reference-level analysis
│
├── Kaggle / Rolex Watch Listings
│   └── Historical Rolex listing observations used for feature-level
│       premium and listing-visibility analysis
│
├── Kaggle / Rolex Retail Prices
│   └── Retail-price reference table used to estimate listing-price premiums
│
├── Custom Chrono24 scraping
│   └── Current Rolex market cross-check
│
├── eBay Browse API
│   └── Standardized live retrieval sample by brand
│
└── Google Trends
    └── Public attention / search-interest proxy

        ↓

Python collection and preparation scripts
│
├── collect.py
│   └── Chrono24 scraping
│
├── collect_ebay.py
│   └── eBay API OAuth + item search
│
├── collect_google_trends.py
│   └── Google Trends collection
│
├── prepare.py
│   └── General market structure preparation
│
├── prepare_rolex_premium.py
│   └── Rolex daily listings + RRP merge + premium calculation
│
├── prepare_rolex_visibility.py
│   └── Listing persistence / visibility duration analysis
│
├── prepare_ebay_attention.py
│   └── eBay API sample + Google Trends merge
│
└── store.py
    └── Load processed CSVs into SQLite

        ↓

Processed analytical datasets
│
├── global_watch_market.csv
├── rolex_historical_market.csv
├── rolex_premium_analysis.csv
├── rolex_listing_visibility.csv
├── rolex_visibility_by_collection.csv
├── rolex_live_market.csv
├── ebay_market_sample.csv
├── ebay_google_attention_market.csv
└── google_trends_brand_attention.csv

        ↓

SQLite analytical database
│
└── watch_market.db

        ↓

FastAPI analytical layer
│
├── GET  /
├── GET  /market-concentration
├── GET  /brand-attention
├── GET  /ebay-inventory
├── POST /refresh-ebay-market
├── GET  /rolex-premium-formation
├── GET  /speculative-references
└── GET  /data-sources

        ↓

Streamlit dashboard
│
├── Page 1: Market concentration + API retrieval saturation
├── Page 2: Rolex premium formation + visibility persistence
├── Page 3: Speculative reference concentration
└── Page 4: Data pipeline and API architecture
""", language="text")

st.divider()

# =========================
# DATASET ROLES
# =========================
st.subheader("Processed Dataset Inventory")

tables = {
    "global_watch_market.csv": {
        "Layer": "Macro market",
        "Purpose": "Multi-brand luxury watch market structure from historical marketplace listings",
        "Used in": "Page 1"
    },
    "rolex_historical_market.csv": {
        "Layer": "Rolex reference analysis",
        "Purpose": "Reference-level Rolex dataset used for speculative concentration analysis",
        "Used in": "Page 3"
    },
    "rolex_premium_analysis.csv": {
        "Layer": "Rolex premium formation",
        "Purpose": "Daily Rolex listing visibility dataset merged with RRP to compute resale premium",
        "Used in": "Page 2"
    },
    "rolex_listing_visibility.csv": {
        "Layer": "Market persistence",
        "Purpose": "Listing-level visibility duration using URL as listing identity",
        "Used in": "Page 2"
    },
    "rolex_visibility_by_collection.csv": {
        "Layer": "Market persistence",
        "Purpose": "Collection-level summary of average listing visibility duration",
        "Used in": "Page 2"
    },
    "rolex_live_market.csv": {
        "Layer": "Current market cross-check",
        "Purpose": "Current Rolex market cross-check from custom Chrono24 scraping",
        "Used in": "Page 3"
    },
    "ebay_market_sample.csv": {
        "Layer": "API collection",
        "Purpose": "Standardized eBay API retrieval sample aggregated by brand",
        "Used in": "Page 1 / API pipeline"
    },
    "ebay_google_attention_market.csv": {
        "Layer": "API + attention",
        "Purpose": "Merged eBay API retrieval sample with Google Trends attention signal",
        "Used in": "Page 1"
    },
    "google_trends_brand_attention.csv": {
        "Layer": "Attention proxy",
        "Purpose": "Relative public search attention by luxury watch brand",
        "Used in": "Page 1"
    }
}

summary_rows = []

for filename, meta in tables.items():
    path = DATA_DIR / filename

    if path.exists():
        df = pd.read_csv(path, low_memory=False)
        summary_rows.append({
            "Dataset": filename,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Layer": meta["Layer"],
            "Purpose": meta["Purpose"],
            "Used in": meta["Used in"]
        })
    else:
        summary_rows.append({
            "Dataset": filename,
            "Rows": "Missing",
            "Columns": "Missing",
            "Layer": meta["Layer"],
            "Purpose": meta["Purpose"],
            "Used in": meta["Used in"]
        })

summary_df = pd.DataFrame(summary_rows)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True
)

st.divider()

# =========================
# DATASET METHODOLOGY
# =========================
st.subheader("Key Methodological Choices")

st.markdown("""
### 1. Two Rolex historical datasets serve different analytical purposes

- `rolex_historical_market.csv` is used for reference-level speculative analysis.
- `rolex_premium_analysis.csv` is reconstructed from repeated daily Rolex listings and used for feature-level premium formation.

These datasets are not interchangeable. The marketplace-level dataset supports comparisons between references, whereas repeated daily observations capture feature-level premium patterns with greater weight given to listings visible on more days.

### 2. Rolex daily listings are not unique watch counts

The daily Rolex files contain repeated listings across multiple days.  
This is why Page 2 interprets them as **listing visibility observations**, not as unique watches.

### 3. Data sources were selected to answer different research questions

- **Historical multi-brand listings** establish the broad distribution of listings and asking prices across brands (Page 1).
- **Daily Rolex observations and the retail-price reference table** support feature-level comparisons and listing-visibility analysis (Page 2).
- **Historical reference-level Rolex listings** support exploratory comparisons between selected sports / collector-oriented references and other references (Page 3).
- **Google Trends** provides a relative search-attention proxy, while **eBay Browse API** provides a standardized, refreshable sample of searchable inventory (Page 1).
- **Custom Chrono24 scraping** offers a current-market cross-check, not an independent validation of historical reference-level rankings (Page 3).

These sources differ in platform coverage, observation period, and unit of analysis. Their metrics are therefore interpreted within each dataset rather than combined into a single representative market estimate.

### 4. eBay API results are standardized retrieval samples

The eBay Browse API collection uses a controlled retrieval limit of 200 items per brand query.  
Therefore, the output is not total eBay market size.  
It is used as a standardized, platform-specific retrieval signal and to demonstrate automated API ingestion. Retrieval saturation measures the share of the predefined query cap filled, not global inventory share.

### 5. Premiums represent asking prices, not realized investment returns

The project calculates resale premium from observed listing prices relative to the available retail-price reference table. These are **asking-price premiums**, not confirmed transaction premiums or realized returns. The retail-price reference is used as supplied; this pipeline alone does not independently establish its official provenance or historical price alignment.

The selected sports / hype reference group is a researcher-defined exploratory segment, not an official Rolex classification or a statistically validated measure of market hype.
""")

st.divider()

# =========================
# API COMPONENTS
# =========================
st.subheader("API Components")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### eBay Browse API

    **Role:** live searchable inventory signal.

    **Used for**
    - API authentication and retrieval
    - Standardized brand-level retrieval sample
    - Retrieval saturation analysis
    - Refreshable sample used by the Streamlit / FastAPI workflow

    **Limitation**
    - Capped at 200 retrievable listings per brand query
    """)

with col2:
    st.markdown("""
    ### Google Trends

    **Role:** public attention proxy.

    **Used for**
    - Brand-level search interest
    - Attention vs price positioning
    - Attention / inventory mismatch index
    """)

with col3:
    st.markdown("""
    ### FastAPI

    **Role:** programmatic access layer.

    **Used for**
    - Querying SQLite summaries
    - Refreshing eBay API data
    - Demonstrating backend API architecture
    """)

st.divider()

# =========================
# SQLITE CHECK
# =========================
st.subheader("SQLite Database Status")

if DB_PATH.exists():
    connection = sqlite3.connect(DB_PATH)

    db_tables = pd.read_sql_query(
        """
        SELECT name AS table_name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """,
        connection
    )

    db_rows = []

    for table in db_tables["table_name"]:
        row_count = pd.read_sql_query(
            f"SELECT COUNT(*) AS rows FROM {table}",
            connection
        )["rows"].iloc[0]

        db_rows.append({
            "SQLite table": table,
            "Rows": row_count
        })

    connection.close()

    db_summary = pd.DataFrame(db_rows)

    st.success("SQLite database found.")
    st.dataframe(
        db_summary,
        use_container_width=True,
        hide_index=True
    )

    expected_tables = [
        "global_watch_market",
        "rolex_historical_market",
        "rolex_premium_analysis",
        "rolex_listing_visibility",
        "rolex_visibility_by_collection",
        "rolex_live_market",
        "ebay_market_sample",
        "ebay_google_attention_market",
        "google_trends_brand_attention"
    ]

    missing_tables = [
        table for table in expected_tables
        if table not in db_tables["table_name"].tolist()
    ]

    if missing_tables:
        st.warning(
            "Some expected SQLite tables are missing: "
            + ", ".join(missing_tables)
        )

        st.code(
            "python src/store.py",
            language="bash"
        )
    else:
        st.success("All expected SQLite tables are available.")

else:
    st.warning("SQLite database was not found.")
    st.code(
        "python src/store.py",
        language="bash"
    )

st.divider()

# =========================
# FASTAPI CHECK
# =========================
st.subheader("FastAPI Demonstration")

st.markdown("""
The FastAPI layer provides programmatic access to analytical data stored in SQLite.
The Streamlit dashboard can also request an eBay sample refresh through a dedicated FastAPI endpoint. The historical charts are not automatically live market feeds.
""")

try:
    response = requests.get(f"{API_BASE_URL}/", timeout=3)

    if response.status_code == 200:
        st.success("FastAPI is running.")
        st.json(response.json())
    else:
        st.warning("FastAPI responded but returned a non-200 status.")

except Exception:
    st.warning("FastAPI is not currently running. Start it with:")
    st.code(
        "uvicorn api.main:app --reload",
        language="bash"
    )

# Endpoint list
st.markdown("""
### FastAPI endpoints used in this project

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | API health check |
| `/market-concentration` | GET | Brand-level listing concentration |
| `/brand-attention` | GET | Google Trends attention data |
| `/ebay-inventory` | GET | eBay API retrieval sample from SQLite |
| `/refresh-ebay-market` | POST | Refresh eBay API data and update SQLite |
| `/rolex-premium-formation` | GET | Rolex feature-level premium summary |
| `/speculative-references` | GET | Rolex reference-level premium concentration |
| `/data-sources` | GET | List available processed data sources |
""")

st.divider()

# =========================
# PROJECT ARCHITECTURE
# =========================
with st.expander("View project file structure", expanded=False):
    st.code(
        """
project/
│
├── Luxury_Watch_Market.py
├── requirements.txt
├── README.md
├── .env
│
├── .streamlit/
│   └── config.toml
│
├── api/
│   └── main.py
│
├── pages/
│   ├── 1_📊_Market_Concentration.py
│   ├── 2_⌚_Rolex_Premium.py
│   ├── 3_📈_Speculative_References.py
│   └── 4_🧩_Data_Pipeline.py
│
├── data/
│   ├── raw/
│   │   ├── kaggle/
│   │   │   ├── Watches.csv
│   │   │   ├── Prezzi_Originali_puliti.csv
│   │   │   └── rolex_daily/*.csv
│   │   │
│   │   ├── chrono24/
│   │   │   ├── chrono24_rolex_live.csv
│   │   │   └── *.html
│   │   │
│   │   ├── ebay/
│   │   │   └── ebay_market_sample.csv
│   │   │
│   │   └── google_trends/
│   │       └── google_trends_brand_attention.csv
│   │
│   ├── processed/
│   │   ├── global_watch_market.csv
│   │   ├── rolex_historical_market.csv
│   │   ├── rolex_premium_analysis.csv
│   │   ├── rolex_listing_visibility.csv
│   │   ├── rolex_visibility_by_collection.csv
│   │   ├── rolex_live_market.csv
│   │   ├── ebay_market_sample.csv
│   │   ├── ebay_google_attention_market.csv
│   │   └── google_trends_brand_attention.csv
│   │
│   └── database/
│       └── watch_market.db
│
├── src/
│   ├── collect.py
│   ├── collect_ebay.py
│   ├── collect_google_trends.py
│   ├── prepare.py
│   ├── prepare_rolex_premium.py
│   ├── prepare_rolex_visibility.py
│   ├── prepare_ebay_attention.py
│   ├── store.py
│   ├── sql_check.py
│   └── utils.py
│
├── notebooks/
│   ├── 01_market_structure.ipynb
│   ├── 02_rolex_historical_analysis.ipynb
│   ├── 03_rolex_live_analysis.ipynb
│   ├── 04_final_dataset_build.ipynb
│   └── google.ipynb
│
└── tests/
    └── test_pipeline.py
""", language="text")