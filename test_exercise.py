"""Provided acceptance checks. Candidates can add their own tests here."""

from copy import deepcopy
import inspect
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests

import exercise
from service.server import PNG_SIGNATURE, render_png, running_server

ROOT = Path(__file__).resolve().parent


def config():
    return json.loads((ROOT / "data" / "map_config.json").read_text(encoding="utf-8"))


def points(count):
    return [{"lat": 47.57 + index / 10000, "lon": -122.32 + index / 10000}
            for index in range(count)]


class SetupTests(unittest.TestCase):
    def test_two_input_files(self):
        self.assertEqual(len(list((ROOT / "data").glob("*.json"))), 2)
        self.assertEqual(set(config()), {"center", "width", "height", "zoom"})
        ride = json.loads((ROOT / "data" / "ride.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ride["features"][0]["geometry"]["coordinates"]), 35)

    def test_provided_service(self):
        with running_server() as (_, base_url):
            response = requests.get(base_url + "/health", timeout=3)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["service"], "practice-staticmap")


class Part1Tests(unittest.TestCase):
    def test_json_request_and_exact_image_bytes(self):
        payload = config()
        payload.update(width=240, height=180)
        with running_server() as (server, base_url), tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "base.png"
            result = exercise.render_map(payload, output, base_url=base_url)
            self.assertEqual(result, output)
            self.assertEqual(output.read_bytes(), render_png(payload))
            self.assertEqual(server.calls[-1]["payload"], payload)

    def test_http_error_does_not_replace_image(self):
        payload = config()
        payload["width"] = 0
        with running_server() as (_, base_url), tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "base.png"
            output.write_bytes(b"previous image")
            with self.assertRaises(requests.HTTPError):
                exercise.render_map(payload, output, base_url=base_url)
            self.assertEqual(output.read_bytes(), b"previous image")

    def test_timeout_is_set_and_transport_error_propagates(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "base.png"
            with patch("requests.sessions.Session.request", side_effect=requests.Timeout("slow API")) as call:
                with self.assertRaises(requests.Timeout):
                    exercise.render_map(config(), output)
            timeout = call.call_args.kwargs.get("timeout")
            self.assertIsInstance(timeout, (int, float))
            self.assertTrue(math.isfinite(timeout) and timeout > 0)
            self.assertFalse(output.exists())


class Part2Tests(unittest.TestCase):
    def capture_payload(self, positions):
        """Run file parsing and request construction without calling the API."""
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ride_path, config_path = directory / "ride.json", directory / "map_config.json"
            document = {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "properties": {}, "geometry": {
                    "type": "LineString",
                    "coordinates": [[point["lon"], point["lat"]] for point in positions],
                }}],
            }
            ride_path.write_text(json.dumps(document), encoding="utf-8")
            config_path.write_text(json.dumps(config()), encoding="utf-8")
            output = directory / "ride.png"
            with patch.object(exercise, "render_map", return_value=output) as render:
                result = exercise.render_ride(ride_path, config_path, output,
                                              base_url="http://127.0.0.1:9999")
            self.assertEqual(result, output)
            render.assert_called_once()
            arguments = inspect.signature(exercise.render_map).bind(*render.call_args.args,
                                                                   **render.call_args.kwargs)
            self.assertEqual(arguments.arguments["base_url"], "http://127.0.0.1:9999")
            self.assertEqual(Path(arguments.arguments["output_path"]), output)
            return deepcopy(arguments.arguments["payload"])

    def test_markers_coordinate_order_and_map_settings(self):
        positions = points(3)
        payload = self.capture_payload(positions)
        for key, value in config().items():
            self.assertEqual(payload[key], value)
        self.assertEqual(payload["markers"], [
            {"color": "white", "label": "Start", "coord": positions[0]},
            {"color": "blue", "label": "Stripe", "coord": positions[-1]},
        ])

    def test_colors_and_complete_track_coverage(self):
        positions = points(35)
        payload = self.capture_payload(positions)
        self.assertEqual([path["color"] for path in payload["paths"]],
                         ["blue", "brown", "blue", "brown"])
        self.assertEqual([len(path["positions"]) for path in payload["paths"]], [11, 11, 11, 5])
        reconstructed = [payload["paths"][0]["positions"][0]]
        for path in payload["paths"]:
            self.assertEqual(reconstructed[-1], path["positions"][0])
            reconstructed.extend(path["positions"][1:])
        self.assertEqual(reconstructed, positions)

    def test_short_exact_boundary_and_remainder_rides(self):
        for count, sizes in ((2, [2]), (11, [11]), (21, [11, 11]), (25, [11, 11, 5])):
            with self.subTest(position_count=count):
                positions = points(count)
                payload = self.capture_payload(positions)
                paths = payload["paths"]
                self.assertEqual([len(path["positions"]) for path in paths], sizes)
                reconstructed = [paths[0]["positions"][0]]
                for path in paths:
                    self.assertEqual(reconstructed[-1], path["positions"][0])
                    reconstructed.extend(path["positions"][1:])
                self.assertEqual(reconstructed, positions)

    def test_supplied_files_end_to_end_over_http(self):
        with running_server() as (server, base_url), tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ride.png"
            result = exercise.render_ride(ROOT / "data" / "ride.json",
                                          ROOT / "data" / "map_config.json",
                                          output, base_url=base_url)
            self.assertEqual(result, output)
            self.assertTrue(output.read_bytes().startswith(PNG_SIGNATURE))
            self.assertEqual(len(server.calls[-1]["payload"]["paths"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
