import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ROLEX_DAILY_DIR = RAW_DIR / "kaggle" / "rolex_daily"
RRP_FILE = RAW_DIR / "kaggle" / "Prezzi_Originali_puliti.csv"

OUTPUT_FILE = PROCESSED_DIR / "rolex_premium_analysis.csv"


def extract_reference(text):
    text = str(text)
    match = re.search(r"\b[0-9]{4,6}[A-Z0-9]*\b", text)
    if match:
        return match.group(0)
    return None


def extract_material(text):
    text = str(text).lower()

    if "gold/steel" in text or ("gold" in text and "steel" in text):
        return "Two-tone"
    if "two-tone" in text or "two tone" in text:
        return "Two-tone"
    if "yellow gold" in text:
        return "Yellow Gold"
    if "white gold" in text:
        return "White Gold"
    if "rose gold" in text or "everose" in text:
        return "Rose Gold"
    if "platinum" in text:
        return "Platinum"
    if "steel" in text:
        return "Steel"

    return None


def extract_dial_color(text):
    text = str(text).lower()

    if "green" in text:
        return "Green"
    if "blue" in text:
        return "Blue"
    if "black" in text:
        return "Black"
    if "white" in text:
        return "White"
    if "silver" in text:
        return "Silver"
    if "champagne" in text:
        return "Champagne"
    if "brown" in text:
        return "Brown"

    return "Other"


def extract_collection(text):
    text = str(text).lower()

    collection_map = {
        "GMT-Master II": ["gmt-master ii", "gmt master ii", "gmt"],
        "Submariner": ["submariner"],
        "Cosmograph Daytona": ["cosmograph daytona", "daytona"],
        "Datejust": ["datejust"],
        "Day-Date": ["day-date", "day date"],
        "Oyster Perpetual": ["oyster perpetual"],
        "Sky-Dweller": ["sky-dweller", "sky dweller"],
        "Yacht-Master II": ["yacht-master ii", "yacht master ii"],
        "Yacht-Master": ["yacht-master", "yacht master"],
        "Sea-Dweller": ["sea-dweller", "sea dweller"],
        "Deepsea Sea-Dweller": ["deepsea"],
        "Explorer II": ["explorer ii"],
        "Explorer": ["explorer"],
        "Air King": ["air king", "air-king"],
        "Milgauss": ["milgauss"],
        "Cellini": ["cellini"],
        "Pearlmaster": ["pearlmaster"],
    }

    for collection, keywords in collection_map.items():
        for kw in keywords:
            if kw in text:
                return collection

    return None


def extract_complication(text):
    text = str(text).lower()

    if "gmt" in text:
        return "GMT"
    if "daytona" in text or "chronograph" in text:
        return "Chronograph"
    if "submariner" in text or "sea-dweller" in text or "deepsea" in text:
        return "Diver"
    if "sky-dweller" in text:
        return "Annual Calendar"
    if "datejust" in text or "day-date" in text or "date" in text:
        return "Date"

    return "Simple Time"


def extract_year(text):
    text = str(text)
    match = re.search(r"\b(19[9][0-9]|20[0-2][0-9])\b", text)

    if match:
        year = int(match.group(0))
        if 1990 <= year <= 2026:
            return year

    return None


def make_year_bucket(year):
    if pd.isna(year):
        return None
    if year < 2000:
        return "Before 2000"
    if year < 2005:
        return "2000–2004"
    if year < 2010:
        return "2005–2009"
    if year < 2015:
        return "2010–2014"
    if year < 2020:
        return "2015–2019"
    return "2020+"


def main():
    print("Loading Rolex daily raw files...")

    files = list(ROLEX_DAILY_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(f"No CSV files found in {ROLEX_DAILY_DIR}")

    dfs = []

    for file in files:
        temp = pd.read_csv(file, low_memory=False)
        temp["source_file"] = file.name
        dfs.append(temp)

    df = pd.concat(dfs, ignore_index=True)

    print(f"Loaded Rolex raw rows: {len(df):,}")

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["reference"] = df["name"].apply(extract_reference)

    print("Loading RRP file...")

    rrp = pd.read_csv(RRP_FILE, sep=None, engine="python")

    # Standardize column names
    rrp.columns = [c.strip() for c in rrp.columns]

    # Try to detect reference and RRP columns
    reference_col = None
    rrp_col = None

    for col in rrp.columns:
        if col.lower() in ["reference", "ref"]:
            reference_col = col

    for col in rrp.columns:
        if col.lower() in ["rrp", "rrp_clean", "msrp", "price"]:
            rrp_col = col

    if reference_col is None:
        raise ValueError(f"Could not find reference column in RRP file. Columns: {rrp.columns.tolist()}")

    if rrp_col is None:
        raise ValueError(f"Could not find RRP column in RRP file. Columns: {rrp.columns.tolist()}")

    rrp = rrp[[reference_col, rrp_col]].copy()
    rrp.columns = ["reference", "rrp_clean"]

    rrp["reference"] = rrp["reference"].astype(str).str.strip()
    rrp["rrp_clean"] = pd.to_numeric(rrp["rrp_clean"], errors="coerce")

    df["reference"] = df["reference"].astype(str).str.strip()

    print("Merging Rolex data with RRP...")

    df = df.merge(rrp, on="reference", how="left")

    df["premium_pct"] = ((df["price"] - df["rrp_clean"]) / df["rrp_clean"]) * 100

    df = df.dropna(subset=["price", "rrp_clean", "premium_pct"]).copy()
    df = df[(df["premium_pct"] > -80) & (df["premium_pct"] < 300)].copy()

    print(f"Rows after premium cleaning: {len(df):,}")

    print("Extracting analytical features from name...")
    
    df["collection"] = df["name"].apply(extract_collection)
    df["material_clean"] = df["name"].apply(extract_material)
    df["dial_color_clean"] = df["name"].apply(extract_dial_color)
    df["complication_type"] = df["name"].apply(extract_complication)
    df["production_year"] = df["name"].apply(extract_year)
    df["year_bucket"] = df["production_year"].apply(make_year_bucket)

    sports_collections = [
    "Submariner",
    "GMT-Master II",
    "Cosmograph Daytona",
    "Sea-Dweller",
    "Deepsea Sea-Dweller",
    "Explorer",
    "Explorer II",
    "Yacht-Master",
    "Yacht-Master II",
    "Sky-Dweller",
    "Oyster Perpetual",
    "Air King",
    "Milgauss",
    ]

    classic_collections = [
    "Datejust",
    "Day-Date",
    "Cellini",
    "Pearlmaster",
    ]

    def classify_segment(collection):
        if collection in sports_collections:
            return "Sports"
        elif collection in classic_collections:
            return "Classic"
        else:
            return None

    df["segment"] = df["collection"].apply(classify_segment)

    output_cols = [
        "name",
        "price",
        "reference",
        "rrp_clean",
        "premium_pct",
        "collection",
        "material_clean",
        "dial_color_clean",
        "complication_type",
        "production_year",
        "year_bucket",
        "segment",
        "source_file",
    ]

    df_final = df[output_cols].copy()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved cleaned Rolex premium dataset to: {OUTPUT_FILE}")
    print(f"Final rows: {len(df_final):,}")
    print(df_final.head())


if __name__ == "__main__":
    main()