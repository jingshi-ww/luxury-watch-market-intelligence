from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DAILY_DIR = BASE_DIR / "data" / "raw" / "kaggle" / "rolex_daily"
RRP_FILE = BASE_DIR / "data" / "raw" / "kaggle" / "Prezzi_Originali_puliti.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

LISTING_OUTPUT = PROCESSED_DIR / "rolex_listing_visibility.csv"
COLLECTION_OUTPUT = PROCESSED_DIR / "rolex_visibility_by_collection.csv"


def extract_reference(text):
    match = re.search(r"\b[0-9]{4,6}[A-Z0-9]*\b", str(text))
    return match.group(0) if match else None


def extract_collection(text):
    text = str(text).lower()

    if "gmt" in text:
        return "GMT-Master II"
    if "daytona" in text:
        return "Daytona"
    if "submariner" in text:
        return "Submariner"
    if "datejust" in text:
        return "Datejust"
    if "day-date" in text or "day date" in text:
        return "Day-Date"
    if "explorer" in text:
        return "Explorer"
    if "sea-dweller" in text or "deepsea" in text:
        return "Sea-Dweller"
    if "yacht-master" in text or "yacht master" in text:
        return "Yacht-Master"
    if "oyster perpetual" in text:
        return "Oyster Perpetual"

    return "Other"


def main():
    files = sorted(RAW_DAILY_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(f"No daily Rolex CSV found in {RAW_DAILY_DIR}")

    dfs = []

    for file in files:
        temp = pd.read_csv(file, low_memory=False)
        temp["source_file"] = file.name
        dfs.append(temp)

    df = pd.concat(dfs, ignore_index=True)

    # Clean columns
    df.columns = df.columns.str.lower().str.strip()

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    df = df.dropna(subset=["date", "url", "price"]).copy()

    df["reference"] = df["name"].apply(extract_reference)
    df["collection"] = df["name"].apply(extract_collection)

    # Load official retail price table
    rrp = pd.read_csv(RRP_FILE, sep=None, engine="python")
    rrp.columns = rrp.columns.str.lower().str.strip()

    rrp = rrp.rename(columns={
        "reference": "reference",
        "rrp": "rrp_clean"
    })

    rrp["reference"] = rrp["reference"].astype(str).str.strip()
    rrp["rrp_clean"] = pd.to_numeric(rrp["rrp_clean"], errors="coerce")

    df["reference"] = df["reference"].astype(str).str.strip()

    df = df.merge(
        rrp[["reference", "rrp_clean"]],
        on="reference",
        how="left"
    )

    df["premium_pct"] = (
        (df["price"] - df["rrp_clean"])
        / df["rrp_clean"]
    ) * 100

    # Listing-level visibility analysis
    listing_visibility = (
        df.groupby("url")
        .agg(
            first_seen=("date", "min"),
            last_seen=("date", "max"),
            visibility_days=("date", "nunique"),
            observed_rows=("url", "size"),
            title=("name", "first"),
            reference=("reference", "first"),
            collection=("collection", "first"),
            median_price=("price", "median"),
            median_premium=("premium_pct", "median")
        )
        .reset_index()
    )

    listing_visibility["calendar_span_days"] = (
        listing_visibility["last_seen"] - listing_visibility["first_seen"]
    ).dt.days + 1

    # Collection-level summary
    collection_summary = (
        listing_visibility
        .groupby("collection")
        .agg(
            unique_listings=("url", "nunique"),
            avg_visibility_days=("visibility_days", "mean"),
            median_visibility_days=("visibility_days", "median"),
            avg_calendar_span_days=("calendar_span_days", "mean"),
            median_price=("median_price", "median"),
            median_premium=("median_premium", "median")
        )
        .reset_index()
        .sort_values("unique_listings", ascending=False)
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    listing_visibility.to_csv(LISTING_OUTPUT, index=False)
    collection_summary.to_csv(COLLECTION_OUTPUT, index=False)

    print("Visibility analysis created.")
    print(f"Raw rows: {len(df):,}")
    print(f"Unique listings: {listing_visibility['url'].nunique():,}")
    print(f"Average visibility days: {listing_visibility['visibility_days'].mean():.1f}")
    print(f"Saved listing file to: {LISTING_OUTPUT}")
    print(f"Saved collection summary to: {COLLECTION_OUTPUT}")


if __name__ == "__main__":
    main()