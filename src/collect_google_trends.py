from pathlib import Path
import time

import pandas as pd
from pytrends.request import TrendReq


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_OUTPUT = (
    BASE_DIR
    / "data"
    / "raw"
    / "google_trends"
    / "google_trends_brand_attention.csv"
)

PROCESSED_OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "google_trends_brand_attention.csv"
)

RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# =========================================================
# MARKET SEGMENTATION
# =========================================================

SEGMENT_MAP = {
    "TAG Heuer": "Accessible luxury",
    "Longines": "Accessible luxury",

    "Omega": "Broad premium",
    "Cartier": "Broad premium",

    "Rolex": "High prestige",

    "Patek Philippe": "Collector prestige",
    "Audemars Piguet": "Collector prestige",

    "Richard Mille": "Ultra prestige niche",
}


# =========================================================
# GOOGLE TRENDS GROUPS
# max 5 keywords per request
# Rolex is used as the anchor brand across groups
# =========================================================

TREND_GROUPS = {
    "group_a": [
        "Rolex",
        "Omega",
        "Cartier",
        "Patek Philippe",
        "Audemars Piguet",
    ],
    "group_b": [
        "Rolex",
        "TAG Heuer",
        "Longines",
        "Richard Mille",
    ],
}


# =========================================================
# COLLECT FUNCTION
# =========================================================

def collect_group_trends(pytrends, group_name, keywords):
    print(f"\nCollecting {group_name}: {keywords}")

    pytrends.build_payload(
        kw_list=keywords,
        timeframe="today 12-m",
        geo="",
    )

    df = pytrends.interest_over_time()

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    # Average search interest over the last 12 months
    avg_scores = df.mean().reset_index()
    avg_scores.columns = ["brand", "trend_score"]

    avg_scores["trend_group"] = group_name

    # Rolex is the anchor for cross-group normalization
    rolex_score = avg_scores.loc[
        avg_scores["brand"] == "Rolex",
        "trend_score"
    ].iloc[0]

    avg_scores["anchor_brand"] = "Rolex"
    avg_scores["anchor_score"] = rolex_score

    avg_scores["relative_attention_score"] = (
        avg_scores["trend_score"] / rolex_score
    )

    return avg_scores


# =========================================================
# MAIN
# =========================================================

def main():
    pytrends = TrendReq(
        hl="en-US",
        tz=360
    )

    all_groups = []

    for group_name, keywords in TREND_GROUPS.items():
        group_df = collect_group_trends(
            pytrends=pytrends,
            group_name=group_name,
            keywords=keywords,
        )

        all_groups.append(group_df)

        time.sleep(2)

    trends = pd.concat(
        all_groups,
        ignore_index=True
    )

    # Remove duplicated Rolex row from second group
    # Keep group_a Rolex as the global anchor
    trends = trends[
        ~(
            (trends["brand"] == "Rolex")
            & (trends["trend_group"] != "group_a")
        )
    ].copy()

    trends["market_segment"] = trends["brand"].map(SEGMENT_MAP)

    trends = trends[
        [
            "brand",
            "market_segment",
            "trend_group",
            "trend_score",
            "anchor_brand",
            "anchor_score",
            "relative_attention_score",
        ]
    ]

    trends = trends.sort_values(
        "relative_attention_score",
        ascending=False
    )

    trends.to_csv(
        RAW_OUTPUT,
        index=False
    )

    trends.to_csv(
        PROCESSED_OUTPUT,
        index=False
    )

    print("\nGoogle Trends brand attention collected!")
    print(trends)

    print(f"\nSaved raw file to:\n{RAW_OUTPUT}")
    print(f"\nSaved processed file to:\n{PROCESSED_OUTPUT}")


if __name__ == "__main__":
    main()