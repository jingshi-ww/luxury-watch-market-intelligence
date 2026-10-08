from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

EBAY_PATH = PROCESSED_DIR / "ebay_market_sample.csv"
TRENDS_PATH = PROCESSED_DIR / "google_trends_brand_attention.csv"
OUTPUT_PATH = PROCESSED_DIR / "ebay_google_attention_market.csv"


def main():
    ebay = pd.read_csv(EBAY_PATH)
    trends = pd.read_csv(TRENDS_PATH)

    ebay["price"] = pd.to_numeric(ebay["price"], errors="coerce")
    ebay = ebay.dropna(subset=["brand", "price"])

    ebay_summary = (
        ebay
        .groupby("brand", as_index=False)
        .agg(
            ebay_listing_count=("title", "count"),
            ebay_median_price=("price", "median"),
            ebay_avg_price=("price", "mean")
        )
    )

    trends_small = trends[[
        "brand",
        "market_segment",
        "relative_attention_score"
    ]].drop_duplicates()

    final = ebay_summary.merge(
        trends_small,
        on="brand",
        how="left"
    )

    final = final.sort_values(
        "ebay_listing_count",
        ascending=False
    )

    final.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved: {OUTPUT_PATH}")
    print(final)


if __name__ == "__main__":
    main()