"""Lightweight, offline checks; no live eBay or Google Trends requests."""

import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "database" / "watch_market.db"
EXPECTED_TABLES = {
    "global_watch_market",
    "rolex_historical_market",
    "rolex_premium_analysis",
    "rolex_listing_visibility",
    "rolex_visibility_by_collection",
    "rolex_live_market",
    "ebay_market_sample",
    "ebay_google_attention_market",
    "google_trends_brand_attention",
}


class PipelineStructureTests(unittest.TestCase):
    def test_required_project_files_exist(self):
        for path in (
            "Luxury_Watch_Market.py", "api/main.py", "src/store.py",
            "src/collect_ebay.py", "src/prepare_ebay_attention.py",
            "README.md", "requirements.txt",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_database_tables_if_database_exists(self):
        if not DB.is_file():
            self.skipTest("Local SQLite database is absent; run python src/store.py")
        with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as connection:
            actual = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertFalse(EXPECTED_TABLES - actual,
                         f"Missing SQLite tables: {sorted(EXPECTED_TABLES - actual)}")


if __name__ == "__main__":
    unittest.main()
