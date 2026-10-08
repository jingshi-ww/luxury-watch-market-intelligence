from pathlib import Path
import requests
import pandas as pd
import re
from dotenv import load_dotenv
import os

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_OUTPUT = (
    BASE_DIR
    / "data"
    / "raw"
    / "ebay"
    / "ebay_market_sample.csv"
)

PROCESSED_OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "ebay_market_sample.csv"
)

RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# =========================================================
# SEARCH QUERIES
# =========================================================

BRAND_QUERIES = [
    "Rolex watch",
    "Omega watch",
    "Cartier watch",
    "Patek Philippe watch",
    "Audemars Piguet watch",
    "TAG Heuer watch",
    "Longines watch",
    "Richard Mille watch",
]

# =========================================================
# GET EBAY TOKEN
# =========================================================

auth_url = "https://api.ebay.com/identity/v1/oauth2/token"

auth_response = requests.post(
    auth_url,
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    },
    data={
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    },
    auth=(CLIENT_ID, CLIENT_SECRET)
)

access_token = auth_response.json()["access_token"]

print("Token OK")

# =========================================================
# EBAY SEARCH FUNCTION
# =========================================================

def search_ebay(query, limit=200):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    params = {
        "q": query,
        "limit": limit
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    data = response.json()

    items = data.get("itemSummaries", [])

    results = []

    for item in items:

        title = item.get("title")

        price_info = item.get("price", {})

        price = price_info.get("value")
        currency = price_info.get("currency")

        condition = item.get("condition")

        item_url = item.get("itemWebUrl")

        results.append({
            "source": "ebay",
            "query": query,
            "title": title,
            "price": price,
            "currency": currency,
            "condition": condition,
            "item_url": item_url
        })

    return results

# =========================================================
# COLLECTION PARSING
# =========================================================

collections = [
    "Submariner",
    "Daytona",
    "GMT-Master",
    "Datejust",
    "Day-Date",
    "Explorer",
    "Speedmaster",
    "Seamaster",
    "Royal Oak",
    "Nautilus",
    "Aquanaut",
    "Tank",
    "Santos",
    "Monaco",
    "Carrera",
]

def extract_collection(title):

    if pd.isna(title):
        return None

    for c in collections:

        if c.lower() in title.lower():
            return c

    return "Other"

# =========================================================
# REFERENCE PARSING
# =========================================================

def extract_reference(title):

    if pd.isna(title):
        return None

    patterns = [

        # Rolex style
        r"\b\d{5,6}[A-Z]{0,3}\b",

        # AP style
        r"\b\d{4,6}\.[A-Z0-9]+\b",

        # Generic alphanumeric references
        r"\b[A-Z0-9]{5,15}\b"
    ]

    for pattern in patterns:

        match = re.search(pattern, title)

        if match:
            return match.group()

    return None

# =========================================================
# YEAR PARSING
# =========================================================

def extract_year(title):

    if pd.isna(title):
        return None

    match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        title
    )

    if match:
        return int(match.group())

    return None

# =========================================================
# SEGMENTATION
# =========================================================

SEGMENT_MAP = {

    "TAG Heuer": "Accessible luxury",
    "Longines": "Accessible luxury",

    "Omega": "Broad premium",
    "Cartier": "Broad premium",

    "Rolex": "High prestige",

    "Audemars Piguet": "Collector prestige",
    "Patek Philippe": "Collector prestige",

    "Richard Mille": "Ultra prestige niche"
}

def extract_brand(query):

    brand = query.replace(" watch", "")

    return brand

# =========================================================
# MAIN COLLECTION LOOP
# =========================================================

all_results = []

for query in BRAND_QUERIES:

    print(f"Collecting: {query}")

    results = search_ebay(query)

    all_results.extend(results)

# =========================================================
# DATAFRAME
# =========================================================

df = pd.DataFrame(all_results)

# =========================================================
# ENRICHMENT
# =========================================================

if "query" not in df.columns:
    print("Available columns:", df.columns.tolist())
    raise ValueError("Missing query column. Check all_results / dataframe creation.")

df["brand"] = df["query"].apply(extract_brand)

df["collection"] = (
    df["title"]
    .apply(extract_collection)
)

df["reference"] = (
    df["title"]
    .apply(extract_reference)
)

df["year"] = (
    df["title"]
    .apply(extract_year)
)

df["market_segment"] = (
    df["brand"]
    .map(SEGMENT_MAP)
)

# =========================================================
# CLEANING
# =========================================================

df["price"] = pd.to_numeric(
    df["price"],
    errors="coerce"
)

df = df.dropna(subset=["price"])

df = df[
    df["price"] > 500
]

# =========================================================
# SAVE FILES
# =========================================================

df.to_csv(
    RAW_OUTPUT,
    index=False
)

df.to_csv(
    PROCESSED_OUTPUT,
    index=False
)

# =========================================================
# PREVIEW
# =========================================================

print(df.head())

print("\nCSV saved!")

print(f"\nRows: {len(df)}")

print(f"\nSaved to:\n{RAW_OUTPUT}")