"""Optional C4 relational layer built from existing processed brand-level tables.

Does not alter the nine existing analytical tables or the Streamlit/API queries.
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / 'data' / 'database' / 'watch_market.db'

DDL = '''
CREATE TABLE dim_brand (
 brand_id INTEGER PRIMARY KEY,
 brand_name TEXT NOT NULL UNIQUE,
 market_segment TEXT NOT NULL
);
CREATE TABLE fact_ebay_market (
 brand_id INTEGER PRIMARY KEY,
 ebay_listing_count INTEGER NOT NULL CHECK (ebay_listing_count >= 0),
 ebay_median_price REAL CHECK (ebay_median_price >= 0),
 ebay_avg_price REAL CHECK (ebay_avg_price >= 0),
 FOREIGN KEY (brand_id) REFERENCES dim_brand(brand_id)
);
CREATE TABLE fact_brand_attention (
 brand_id INTEGER PRIMARY KEY,
 trend_score REAL,
 relative_attention_score REAL,
 FOREIGN KEY (brand_id) REFERENCES dim_brand(brand_id)
);
CREATE INDEX idx_dim_brand_segment ON dim_brand(market_segment);
'''


def build_relational_model(connection: sqlite3.Connection):
    """Build/refresh three dimension/fact tables transactionally, validating grain."""
    connection.execute('PRAGMA foreign_keys=ON')
    ebay = connection.execute('''SELECT brand, market_segment, ebay_listing_count,
        ebay_median_price, ebay_avg_price FROM ebay_google_attention_market''').fetchall()
    trends = connection.execute('''SELECT brand, market_segment, trend_score,
        relative_attention_score FROM google_trends_brand_attention''').fetchall()
    if not ebay or not trends:
        raise ValueError('Source tables must be populated before building C4 model')
    def keyed(rows, source):
        result = {}
        for row in rows:
            brand = row[0]
            if not brand or brand in result:
                raise ValueError(f'{source}: blank or duplicate brand {brand!r}')
            result[brand] = row
        return result
    e = keyed(ebay, 'eBay')
    t = keyed(trends, 'Google Trends')
    if set(e) != set(t):
        raise ValueError(f'Brand mismatch: only eBay={set(e)-set(t)}, only Trends={set(t)-set(e)}')
    for brand in e:
        if e[brand][1] != t[brand][1]:
            raise ValueError(f'Inconsistent market_segment for {brand}')
    # Explicit transaction and rollback preserve existing analytical tables on failure.
    with connection:
        for name in ('fact_ebay_market', 'fact_brand_attention', 'dim_brand'):
            connection.execute(f'DROP TABLE IF EXISTS {name}')
        connection.executescript(DDL)
        for i, brand in enumerate(sorted(e), 1):
            er, tr = e[brand], t[brand]
            connection.execute('INSERT INTO dim_brand VALUES (?, ?, ?)', (i, brand, er[1]))
            connection.execute('INSERT INTO fact_ebay_market VALUES (?, ?, ?, ?)',
                               (i, er[2], er[3], er[4]))
            connection.execute('INSERT INTO fact_brand_attention VALUES (?, ?, ?)',
                               (i, tr[2], tr[3]))
        errors = connection.execute('PRAGMA foreign_key_check').fetchall()
        if errors:
            raise ValueError(f'Foreign key violations: {errors}')
    return len(e)


def main():
    if not DB_PATH.is_file():
        raise FileNotFoundError(f'Database not found: {DB_PATH}. Run python src/store.py first.')
    with sqlite3.connect(DB_PATH) as con:
        count = build_relational_model(con)
    print(f'C4 relational model: {count} brands, 3 tables, foreign keys verified')


if __name__ == '__main__':
    main()
