"""Offline C4 tests; no API credentials or live data required."""
import sqlite3
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_relational_model import build_relational_model


class RelationalModelTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(':memory:')
        self.con.execute('CREATE TABLE ebay_google_attention_market (brand TEXT, market_segment TEXT, ebay_listing_count INTEGER, ebay_median_price REAL, ebay_avg_price REAL)')
        self.con.execute('CREATE TABLE google_trends_brand_attention (brand TEXT, market_segment TEXT, trend_score REAL, relative_attention_score REAL)')
        self.con.executemany('INSERT INTO ebay_google_attention_market VALUES (?,?,?,?,?)', [('Rolex','High prestige',200,12000,13000),('Omega','Broad premium',100,4000,4200)])
        self.con.executemany('INSERT INTO google_trends_brand_attention VALUES (?,?,?,?)', [('Rolex','High prestige',80,90),('Omega','Broad premium',40,45)])
        self.con.commit()

    def tearDown(self):
        self.con.close()

    def test_join_and_foreign_keys(self):
        self.assertEqual(build_relational_model(self.con), 2)
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM dim_brand b JOIN fact_ebay_market e USING (brand_id) JOIN fact_brand_attention t USING (brand_id)').fetchone()[0], 2)
        self.assertEqual(self.con.execute('PRAGMA foreign_key_check').fetchall(), [])
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('INSERT INTO fact_ebay_market VALUES (999,1,1,1)')

    def test_rebuild(self):
        build_relational_model(self.con)
        self.assertEqual(build_relational_model(self.con), 2)

    def test_reject_duplicate_brand(self):
        self.con.execute("INSERT INTO google_trends_brand_attention VALUES ('Rolex','High prestige',50,60)")
        with self.assertRaises(ValueError):
            build_relational_model(self.con)

    def test_reject_unmatched_brand(self):
        self.con.execute("DELETE FROM google_trends_brand_attention WHERE brand='Omega'")
        with self.assertRaises(ValueError):
            build_relational_model(self.con)


if __name__ == '__main__':
    unittest.main()
