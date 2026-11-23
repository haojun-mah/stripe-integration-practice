from contextlib import redirect_stdout
from copy import deepcopy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app
from mock_server import PNG_SIGNATURE, running_server
from tests.support import ROOT, config, subject


def positions(count):
    return [{"lat": 47.57 + index / 10000, "lon": -122.32 + index / 10000}
            for index in range(count)]


class OverlayTests(unittest.TestCase):
    def assert_complete_route(self, points, group_size):
        payload = subject.build_route_payload(points, config(), group_size)
        paths = payload["paths"]
        expected_groups = (len(points) - 2) // group_size + 1
        self.assertEqual(len(paths), expected_groups)
        reconstructed = [paths[0]["positions"][0]]
        for index, path in enumerate(paths):
            self.assertEqual(path["color"], "blue" if index % 2 == 0 else "brown")
            self.assertGreaterEqual(len(path["positions"]), 2)
            self.assertLessEqual(len(path["positions"]), group_size + 1)
            if index < len(paths) - 1:
                self.assertEqual(len(path["positions"]), group_size + 1)
            self.assertEqual(reconstructed[-1], path["positions"][0])
            reconstructed.extend(path["positions"][1:])
        self.assertEqual(reconstructed, points)
        return payload

    def test_minimum_ride(self):
        self.assert_complete_route(positions(2), 10)

    def test_exactly_ten_segments(self):
        self.assert_complete_route(positions(11), 10)

    def test_exactly_twenty_segments(self):
        self.assert_complete_route(positions(21), 10)

    def test_partial_final_group(self):
        payload = self.assert_complete_route(positions(25), 10)
        self.assertEqual([len(path["positions"]) for path in payload["paths"]], [11, 11, 5])

    def test_custom_group_size(self):
        self.assert_complete_route(positions(9), 3)
        self.assert_complete_route(positions(5), 1)

    def test_markers_and_config(self):
        points = positions(12)
        payload = subject.build_route_payload(points, config())
        for key, value in config().items():
            self.assertEqual(payload[key], value)
        self.assertEqual(payload["markers"], [
            {"color": "white", "label": "Start", "coord": points[0]},
            {"color": "blue", "label": "Stripe", "coord": points[-1]},
        ])

    def test_inputs_not_mutated_or_shared(self):
        points, settings = positions(13), config()
        before = deepcopy((points, settings))
        payload = subject.build_route_payload(points, settings)
        self.assertEqual((points, settings), before)
        payload["center"]["lat"] = 0
        payload["paths"][0]["positions"][0]["lat"] = 0
        self.assertEqual((points, settings), before)

    def test_invalid_group_sizes(self):
        for size in (0, -1, 1.5, True):
            with self.subTest(size=size), self.assertRaises(ValueError):
                subject.build_route_payload(positions(3), config(), size)

    def test_too_few_positions(self):
        for points in ([], positions(1)):
            with self.subTest(points=points), self.assertRaises(ValueError):
                subject.build_route_payload(points, config())

    def test_complete_supplied_ride_and_real_http(self):
        points = subject.load_positions(ROOT / "data" / "ride.json")
        payload = self.assert_complete_route(points, 10)
        self.assertEqual([len(path["positions"]) for path in payload["paths"]], [11, 11, 11, 5])
        with running_server() as (server, base_url):
            with subject.MapClient(base_url) as client:
                image = client.render(payload)
            self.assertTrue(image.startswith(PNG_SIGNATURE))
            self.assertEqual(server.calls[-1]["payload"], payload)

    def test_route_command_end_to_end(self):
        with running_server() as (_, base_url), tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "route.png"
            with patch.object(app, "MapClient", subject.MapClient), \
                 patch.object(app, "load_positions", subject.load_positions), \
                 patch.object(app, "save_image", subject.save_image), \
                 patch.object(app, "build_route_payload", subject.build_route_payload), \
                 redirect_stdout(io.StringIO()):
                status = app.main(["route", "--base-url", base_url, "--output", str(output)])
            self.assertEqual(status, 0)
            self.assertTrue(output.read_bytes().startswith(PNG_SIGNATURE))
