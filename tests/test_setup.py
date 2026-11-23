import json
import unittest

import requests

from mock_server import PNG_SIGNATURE, running_server
from tests.support import ROOT, config


class SetupTests(unittest.TestCase):
    def test_two_input_documents_are_readable(self):
        inputs = sorted((ROOT / "data").glob("*.json"))
        self.assertEqual([path.name for path in inputs], ["map_config.json", "ride.json"])
        self.assertEqual(config()["width"], 400)
        ride = json.loads((ROOT / "data" / "ride.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ride["features"][0]["geometry"]["coordinates"]), 35)

    def test_health_endpoint(self):
        with running_server() as (_, base_url):
            response = requests.get(base_url + "/health", timeout=3)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["service"], "practice-staticmap")

    def test_provided_service_renders_png(self):
        with running_server() as (_, base_url):
            response = requests.post(
                base_url + "/map.png", json=config(), timeout=3,
                headers={"Authorization": "Bearer practice-map-key", "Accept": "image/png"},
            )
            self.assertEqual(response.status_code, 200, response.text[:100])
            self.assertTrue(response.content.startswith(PNG_SIGNATURE))

    def test_provided_service_rejects_form_encoding(self):
        with running_server() as (_, base_url):
            response = requests.post(
                base_url + "/map.png", data=config(), timeout=3,
                headers={"Authorization": "Bearer practice-map-key", "Accept": "image/png"},
            )
            self.assertEqual(response.status_code, 415)

    def test_provided_service_rejects_double_encoded_json(self):
        with running_server() as (_, base_url):
            response = requests.post(
                base_url + "/map.png", json=json.dumps(config()), timeout=3,
                headers={"Authorization": "Bearer practice-map-key", "Accept": "image/png"},
            )
            self.assertEqual(response.status_code, 400)
