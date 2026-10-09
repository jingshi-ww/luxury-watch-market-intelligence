"""Small regression checks; do not run the real eBay collection."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

class RefreshSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_missing_key_is_rejected(self):
        with patch.dict(os.environ, {"WATCH_API_KEY": "test-secret"}):
            response = self.client.post("/refresh-ebay-market")
        self.assertEqual(response.status_code, 403)

    def test_wrong_key_is_rejected(self):
        with patch.dict(os.environ, {"WATCH_API_KEY": "test-secret"}):
            response = self.client.post("/refresh-ebay-market", headers={"X-API-Key": "wrong"})
        self.assertEqual(response.status_code, 403)

    def test_unconfigured_server_is_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post("/refresh-ebay-market", headers={"X-API-Key": "anything"})
        self.assertEqual(response.status_code, 403)

    @patch("api.main.subprocess.run")
    def test_valid_key_calls_three_scripts_without_executing_them(self, mock_run):
        with patch.dict(os.environ, {"WATCH_API_KEY": "test-secret"}):
            response = self.client.post("/refresh-ebay-market", headers={"X-API-Key": "test-secret"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_run.call_count, 3)

    def test_public_health_endpoint(self):
        self.assertEqual(self.client.get("/").status_code, 200)

if __name__ == "__main__":
    unittest.main()
