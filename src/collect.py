from pathlib import Path
from datetime import datetime
import json
import re

import pandas as pd
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

HTML_DIR = BASE_DIR / "data" / "raw" / "chrono24"
OUTPUT_PATH = HTML_DIR / "chrono24_rolex_live.csv"


COLLECTION_MAP = {
    "datejust": "Datejust",
    "submariner": "Submariner",
    "gmt_master_ii": "GMT-Master II",
    "oyster_perpetual": "Oyster Perpetual",
    "daytona": "Daytona",
}


def get_search_collection_from_filename(filename):
    filename = filename.lower().strip()

    for key, collection in COLLECTION_MAP.items():
        if key in filename:
            return collection

    return "Unknown"


def extract_collection_from_title(title, fallback_collection):
    text = str(title).lower()

    if "gmt" in text or "gmt-master" in text or "gmt master" in text:
        return "GMT-Master II"

    if "submariner" in text:
        return "Submariner"

    if "daytona" in text or "cosmograph" in text:
        return "Daytona"

    if "oyster perpetual" in text and "datejust" not in text:
        return "Oyster Perpetual"

    if "datejust" in text or "date just" in text:
        return "Datejust"

    return fallback_collection


def extract_reference(text):
    match = re.search(r"\b\d{4,6}[A-Z]*\b", str(text))
    return match.group() if match else None


def extract_year(text):
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(text))
    return int(match.group()) if match else None


def extract_size_mm(text):
    text = str(text).lower()

    common_sizes = [
        26, 28, 31, 34, 36,
        39, 40, 41, 42, 44
    ]

    for size in common_sizes:
        patterns = [
            rf"\b{size}\s?mm\b",
            rf"\b{size}\b"
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                return size

    return None


def extract_dial_color(text):
    text = str(text).lower()

    color_map = {
        "black": ["black", "noir"],
        "blue": ["blue", "bleu"],
        "green": ["green", "vert", "mint"],
        "white": ["white", "blanc"],
        "silver": ["silver", "argent"],
        "grey": ["grey", "gray", "gris"],
        "champagne": ["champagne"],
        "gold": ["gold", "or", "yellow"],
        "rose": ["rose", "everose"],
        "mother_of_pearl": ["mother of pearl", "mop", "nacre"],
        "diamond": ["diamond", "diamonds", "diamant"],
        "wimbledon": ["wimbledon"],
    }

    for color, keywords in color_map.items():
        for keyword in keywords:
            if keyword in text:
                return color

    return None


def is_vintage(text, year):
    text = str(text).lower()

    if "vintage" in text:
        return True

    if year is not None and year < 2000:
        return True

    return False


def extract_offers_from_jsonld(soup):
    script = soup.find("script", type="application/ld+json")

    if script is None:
        return []

    data = json.loads(script.string)

    for item in data.get("@graph", []):
        if item.get("@type") == "AggregateOffer":
            return item.get("offers", [])

    return []

def normalize_url(url):
    if not url:
        return None

    return url.split("?")[0].strip()


def extract_country_by_url(soup):
    country_by_url = {}

    cards = soup.select("div.js-listing-item-container")

    for card in cards:
        link_tag = card.select_one("a[href]")
        country_tag = card.select_one("span.text-uppercase")

        if not link_tag:
            continue

        href = link_tag["href"]

        if href.startswith("/"):
            url = "https://www.chrono24.fr" + href
        else:
            url = href

        country = (
            country_tag.get_text(" ", strip=True)
            if country_tag else None
        )

        country_by_url[normalize_url(url)] = country

    return country_by_url

def parse_html_file(html_file):
    search_collection = get_search_collection_from_filename(html_file.name)

    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    offers = extract_offers_from_jsonld(soup)
    country_by_url = extract_country_by_url(soup)

    listings = []

    for offer in offers:
        title = offer.get("name")
        price = offer.get("price")
        url = offer.get("url")
        seller_country = country_by_url.get(normalize_url(url))

        detected_collection = extract_collection_from_title(
            title,
            search_collection
        )

        reference = extract_reference(title)
        production_year = extract_year(title)
        case_size_mm = extract_size_mm(title)
        dial_color = extract_dial_color(title)

        listings.append({
            "source": "Chrono24",
            "brand": "Rolex",

            # Collection from the file/search page
            "search_collection": search_collection,

            # Collection inferred from title text
            "detected_collection": detected_collection,

            "title": title,
            "price": price,
            "currency": "EUR",
            "seller_country": seller_country,
            "reference": reference,
            "production_year": production_year,
            "case_size_mm": case_size_mm,
            "dial_color": dial_color,
            "is_vintage": is_vintage(title, production_year),
            "url": url,
            "html_file": html_file.name,
            "scraped_at": datetime.now().isoformat(),
        })

    print(
        f"{html_file.name}: "
        f"{len(listings)} listings "
        f"({search_collection})"
    )

    return listings


def main():
    all_listings = []

    html_files = sorted(HTML_DIR.glob("*.html"))

    for html_file in html_files:
        listings = parse_html_file(html_file)
        all_listings.extend(listings)

    df = pd.DataFrame(all_listings)

    df = df.drop_duplicates(subset="url")

    df.to_csv(OUTPUT_PATH, index=False)

    print()
    print(f"Saved {len(df)} unique listings to {OUTPUT_PATH}")

    print()
    print("Listings by search collection:")
    print(df.groupby("search_collection")["url"].count())

    print()
    print("Listings by detected collection:")
    print(df.groupby("detected_collection")["url"].count())

    print()
    print("Case size coverage:")
    print(df["case_size_mm"].notna().mean())

    print()
    print("Reference coverage:")
    print(df["reference"].notna().mean())

    print()
    print("Year coverage:")
    print(df["production_year"].notna().mean())


if __name__ == "__main__":
    main()
