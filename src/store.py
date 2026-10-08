from pathlib import Path
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATABASE_DIR = BASE_DIR / "data" / "database"
DATABASE_PATH = DATABASE_DIR / "watch_market.db"


TABLES = {
    "global_watch_market": PROCESSED_DIR / "global_watch_market.csv",
    "rolex_historical_market": PROCESSED_DIR / "rolex_historical_market.csv",
    "rolex_premium_analysis": PROCESSED_DIR / "rolex_premium_analysis.csv",
    "rolex_listing_visibility": PROCESSED_DIR / "rolex_listing_visibility.csv",
    "rolex_visibility_by_collection": PROCESSED_DIR / "rolex_visibility_by_collection.csv",
    "rolex_live_market": PROCESSED_DIR / "rolex_live_market.csv",
    "ebay_market_sample": PROCESSED_DIR / "ebay_market_sample.csv",
    "ebay_google_attention_market": PROCESSED_DIR / "ebay_google_attention_market.csv",
    "google_trends_brand_attention": PROCESSED_DIR / "google_trends_brand_attention.csv",
}

def load_csv_to_sqlite(table_name, csv_path, connection):
    if not csv_path.exists():
        print(f"Skipped {table_name}: file not found -> {csv_path}")
        return

    df = pd.read_csv(csv_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False
    )

    print(f"Loaded {table_name}: {df.shape[0]} rows, {df.shape[1]} columns")


def main():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    for table_name, csv_path in TABLES.items():
        load_csv_to_sqlite(
            table_name,
            csv_path,
            connection
        )

    connection.close()

    print()
    print(f"SQLite database created at: {DATABASE_PATH}")


if __name__ == "__main__":
    main()