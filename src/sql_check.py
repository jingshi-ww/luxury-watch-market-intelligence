from pathlib import Path
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "watch_market.db"
)


connection = sqlite3.connect(DATABASE_PATH)

# Example query
query = """
SELECT
    detected_collection,
    COUNT(*) AS listing_count,
    ROUND(AVG(premium_pct), 2) AS avg_premium
FROM rolex_live_market
WHERE premium_pct IS NOT NULL
GROUP BY detected_collection
ORDER BY avg_premium DESC
"""

df = pd.read_sql_query(query, connection)

print(df)

connection.close()