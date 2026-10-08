import re
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw" / "kaggle"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

WATCHES_PATH = RAW_DIR / "Watches.csv"
MSRP_PATH = RAW_DIR / "Prezzi_Originali_puliti.csv"

ALL_WATCHES_OUTPUT = PROCESSED_DIR / "all_watches_clean.csv"
ROLEX_OUTPUT = PROCESSED_DIR / "rolex_enriched_market.csv"
COLLECTION_SUMMARY_PATH = PROCESSED_DIR / "collection_summary.csv"

#for chrono24 live market ---
CHRONO24_PATH = BASE_DIR / "data" / "raw" / "chrono24" / "chrono24_rolex_live.csv"

ROLEX_LIVE_OUTPUT = PROCESSED_DIR / "rolex_live_market.csv"
#----

def load_data():
    watches = pd.read_csv(WATCHES_PATH, low_memory=False)
    msrp = pd.read_csv(MSRP_PATH, sep=";", on_bad_lines="skip")
    return watches, msrp


def clean_price(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(r"[^0-9.]", "", regex=True),
        errors="coerce"
    )


def clean_watches(watches):
    watches = watches.copy()
    watches.columns = watches.columns.str.lower().str.strip()

    watches["price"] = clean_price(watches["price"])

    watches["reference"] = (
        watches["ref"]
        .astype(str)
        .str.strip()
        .replace("nan", None)
    )

    return watches


def clean_msrp(msrp):
    msrp = msrp.copy()
    msrp.columns = msrp.columns.str.lower().str.strip()

    msrp["reference"] = (
        msrp["reference"]
        .astype(str)
        .str.strip()
    )

    msrp["rrp"] = pd.to_numeric(msrp["rrp"], errors="coerce")

    return msrp


def create_rolex_enriched_market(watches, msrp):
    rolex = watches[
        watches["brand"].astype(str).str.lower() == "rolex"
    ].copy()

    print("Rolex reference check:")
    print(rolex[["brand", "model", "ref", "reference", "price"]].head(20))

    rolex_enriched = rolex.merge(
        msrp,
        on="reference",
        how="left"
    )

    rolex_enriched["rrp_clean"] = pd.to_numeric(
        rolex_enriched["rrp"],
        errors="coerce"
    )

    rolex_enriched["premium_pct"] = (
        (rolex_enriched["price"] - rolex_enriched["rrp_clean"])
        / rolex_enriched["rrp_clean"]
    ) * 100

    return rolex_enriched


def filter_mainstream_market(df):
    return df[
        (df["premium_pct"] > -80) &
        (df["premium_pct"] < 300)
    ].copy()


def create_collection_summary(df):
    collection_summary = (
        df
        .groupby("collection")
        .agg({
            "premium_pct": "median",
            "price": "count",
            "rrp_clean": "median"
        })
        .rename(columns={
            "premium_pct": "median_premium_pct",
            "price": "listing_count",
            "rrp_clean": "median_rrp"
        })
        .reset_index()
        .sort_values("listing_count", ascending=False)
    )

    return collection_summary

def clean_chrono24(chrono):
    chrono = chrono.copy()

    chrono.columns = chrono.columns.str.lower().str.strip()

    chrono["price"] = pd.to_numeric(
        chrono["price"],
        errors="coerce"
    )

    chrono["reference"] = (
        chrono["reference"]
        .astype(str)
        .str.strip()
        .replace("nan", None)
    )

    chrono["production_year"] = pd.to_numeric(
        chrono["production_year"],
        errors="coerce"
    )

    chrono["case_size_mm"] = pd.to_numeric(
        chrono["case_size_mm"],
        errors="coerce"
    )

    return chrono


def create_rolex_live_market(chrono, msrp):
    chrono_live = chrono.merge(
        msrp,
        on="reference",
        how="left"
    )

    chrono_live["rrp_clean"] = pd.to_numeric(
        chrono_live["rrp"],
        errors="coerce"
    )

    chrono_live["premium_pct"] = (
        (chrono_live["price"] - chrono_live["rrp_clean"])
        / chrono_live["rrp_clean"]
    ) * 100

    chrono_live["dataset_source"] = "chrono24_live"

    return chrono_live


def main():
    watches, msrp = load_data()

    all_watches_clean = clean_watches(watches)
    msrp_clean = clean_msrp(msrp)

    # =========================
    # Chrono24 live market
    # =========================

    chrono24 = pd.read_csv(CHRONO24_PATH)

    chrono24_clean = clean_chrono24(chrono24)

    rolex_live_market = create_rolex_live_market(
        chrono24_clean,
        msrp_clean
    )

    live_match_rate = rolex_live_market["rrp_clean"].notna().mean()

    print("Chrono24 live shape:", rolex_live_market.shape)
    print("Chrono24 MSRP match rate:", live_match_rate)

    rolex_live_market.to_csv(
        ROLEX_LIVE_OUTPUT,
        index=False
    )

    print(f"Saved Rolex live market dataset to: {ROLEX_LIVE_OUTPUT}")

    # =========================
    # Existing Kaggle merge
    # =========================

    rolex_enriched = create_rolex_enriched_market(
        all_watches_clean,
        msrp_clean
    )

    match_rate = rolex_enriched["rrp_clean"].notna().mean()

    print("All watches shape:", all_watches_clean.shape)
    print("MSRP shape:", msrp_clean.shape)
    print("Rolex enriched shape:", rolex_enriched.shape)
    print("Rolex MSRP match rate:", match_rate)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_watches_clean.to_csv(ALL_WATCHES_OUTPUT, index=False)
    rolex_enriched.to_csv(ROLEX_OUTPUT, index=False)

    collection_summary = create_collection_summary(
        filter_mainstream_market(rolex_enriched)
    )

    collection_summary.to_csv(COLLECTION_SUMMARY_PATH, index=False)

    print(f"Saved all market dataset to: {ALL_WATCHES_OUTPUT}")
    print(f"Saved Rolex enriched dataset to: {ROLEX_OUTPUT}")
    print(f"Saved collection summary to: {COLLECTION_SUMMARY_PATH}")


if __name__ == "__main__":
    main()