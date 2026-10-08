from pathlib import Path
import sqlite3
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "watch_market.db"

app = FastAPI(
    title="Luxury Watch Market API",
    description="Analytical API for the luxury watch resale market project",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_sql(query: str, params: tuple = ()):
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    return df.to_dict(orient="records")


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Luxury Watch Market API is running"
    }


@app.get("/market-concentration")
def market_concentration(limit: int = 15):
    query = """
    SELECT
        brand,
        COUNT(*) AS listing_count,
        ROUND(AVG(price), 2) AS avg_price,
        ROUND(MEDIAN_PRICE, 2) AS median_price
    FROM (
        SELECT
            brand,
            price,
            PERCENTILE_CONT_50 AS MEDIAN_PRICE
        FROM global_watch_market
        WHERE brand IS NOT NULL
          AND price IS NOT NULL
    )
    GROUP BY brand
    ORDER BY listing_count DESC
    LIMIT ?
    """

    # SQLite has no native median, so use pandas instead
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT brand, price
        FROM global_watch_market
        WHERE brand IS NOT NULL
          AND price IS NOT NULL
        """,
        connection
    )
    connection.close()

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["brand", "price"])

    result = (
        df.groupby("brand", as_index=False)
        .agg(
            listing_count=("price", "count"),
            avg_price=("price", "mean"),
            median_price=("price", "median")
        )
        .sort_values("listing_count", ascending=False)
        .head(limit)
    )

    return result.to_dict(orient="records")


@app.get("/brand-attention")
def brand_attention():
    return read_sql("""
    SELECT
        brand,
        market_segment,
        relative_attention_score,
        trend_score
    FROM google_trends_brand_attention
    ORDER BY relative_attention_score DESC
    """)


@app.get("/ebay-attention-market")
def ebay_attention_market():
    return read_sql("""
    SELECT
        brand,
        market_segment,
        ebay_listing_count,
        ebay_median_price,
        ebay_avg_price,
        relative_attention_score
    FROM ebay_google_attention_market
    ORDER BY ebay_listing_count DESC
    """)


@app.get("/rolex-premium-formation")
def rolex_premium_formation():
    return read_sql("""
    SELECT
        collection,
        material_clean,
        complication_type,
        COUNT(*) AS listing_count,
        ROUND(AVG(premium_pct), 2) AS avg_premium
    FROM rolex_premium_analysis
    WHERE premium_pct IS NOT NULL
    GROUP BY collection, material_clean, complication_type
    ORDER BY listing_count DESC
    LIMIT 100
    """)


@app.get("/speculative-references")
def speculative_references(limit: int = 20):
    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            reference,
            collection,
            premium_pct,
            price
        FROM rolex_premium_analysis
        WHERE reference IS NOT NULL
          AND collection IS NOT NULL
          AND premium_pct IS NOT NULL
          AND price IS NOT NULL
        """,
        connection
    )

    connection.close()

    df["premium_pct"] = pd.to_numeric(df["premium_pct"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    df = df[
        (df["premium_pct"] > -80) &
        (df["premium_pct"] < 300)
    ].copy()

    result = (
        df.groupby(["reference", "collection"], as_index=False)
        .agg(
            listing_count=("premium_pct", "count"),
            median_premium=("premium_pct", "median"),
            median_price=("price", "median")
        )
        .query("listing_count >= 100")
        .sort_values("median_premium", ascending=False)
        .head(limit)
    )

    return result.to_dict(orient="records")



@app.get("/data-sources")
def data_sources():
    return {
        "processed_tables": [
            "global_watch_market",
            "rolex_historical_market",
            "rolex_premium_analysis",
            "rolex_listing_visibility",
            "rolex_visibility_by_collection",
            "rolex_live_market",
            "ebay_market_sample",
            "google_trends_brand_attention",
            "ebay_google_attention_market"
        ],
        "database": str(DB_PATH)
    }

    

@app.get("/ebay-inventory")
def ebay_inventory():
    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            brand,
            market_segment,
            ebay_listing_count,
            ebay_median_price,
            ebay_avg_price,
            relative_attention_score
        FROM ebay_google_attention_market
        ORDER BY ebay_listing_count DESC
        """,
        connection
    )

    connection.close()

    return df.to_dict(orient="records")


@app.post("/refresh-ebay-market")
def refresh_ebay_market():
    collect_script = BASE_DIR / "src" / "collect_ebay.py"
    prepare_script = BASE_DIR / "src" / "prepare_ebay_attention.py"
    store_script = BASE_DIR / "src" / "store.py"

    subprocess.run([sys.executable, str(collect_script)], check=True)
    subprocess.run([sys.executable, str(prepare_script)], check=True)
    subprocess.run([sys.executable, str(store_script)], check=True)

    return {
        "status": "success",
        "message": "eBay API data refreshed and SQLite database updated",
        "refreshed_at": datetime.now().isoformat()
    }