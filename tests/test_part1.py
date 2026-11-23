from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import app
from bikemap.client import MapAPIError
from bikemap.track import TrackFormatError
from mock_server import PNG_SIGNATURE, running_server
from tests.support import ROOT, config, load_document, subject, track_document


class TrackTests(unittest.TestCase):
    def test_supplied_ride_and_coordinate_order(self):
        positions = subject.load_positions(ROOT / "data" / "ride.json")
        self.assertEqual(len(positions), 35)
        self.assertEqual(positions[0], {"lat": 47.569, "lon": -122.323})
        self.assertTrue(all(set(point) == {"lat", "lon"} for point in positions))

    def test_altitude_ignored_and_repeated_points_preserved(self):
        self.assertEqual(load_document(track_document([[1, 2, 900], [1, 2], [3, 4]])), [
            {"lat": 2, "lon": 1}, {"lat": 2, "lon": 1}, {"lat": 4, "lon": 3},
        ])

    def test_invalid_structure_raises_track_format_error(self):
        for document in ({}, [], {"type": "FeatureCollection", "features": []},
                         {"type": "FeatureCollection", "features": [{"geometry": {"type": "Point"}}]}):
            with self.subTest(document=document), self.assertRaises(TrackFormatError):
                load_document(document)

    def test_invalid_coordinates_and_short_tracks(self):
        bad_tracks = [[], [[1, 2]], [[1], [3, 4]], [[1, 2, 3, 4], [3, 4]],
                      [[181, 2], [3, 4]], [[1, -91], [3, 4]],
                      [[True, 2], [3, 4]], [["1", 2], [3, 4]],
                      [[float("nan"), 2], [3, 4]], [[1, float("inf")], [3, 4]]]
        for coordinates in bad_tracks:
            with self.subTest(coordinates=coordinates), self.assertRaises(TrackFormatError):
                load_document(track_document(coordinates))

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(TrackFormatError):
                subject.load_positions(path)

    def test_other_features_are_ignored(self):
        document = track_document([[1, 2], [3, 4]])
        document["features"].append({"geometry": {"type": "Point", "coordinates": [9, 9]}})
        self.assertEqual(len(load_document(document)), 2)


class ClientTests(unittest.TestCase):
    def test_real_http_json_in_binary_out(self):
        payload = config()
        with running_server() as (server, base_url):
            with subject.MapClient(base_url) as client:
                image = client.render(payload)
            self.assertIsInstance(image, bytes)
            self.assertTrue(image.startswith(PNG_SIGNATURE))
            self.assertEqual(struct.unpack("!II", image[16:24]), (400, 600))
            self.assertEqual(server.calls[-1]["payload"], payload)

    def test_400_is_an_error_not_an_image(self):
        with running_server() as (_, base_url), subject.MapClient(base_url) as client:
            payload = config()
            payload["width"] = 0
            with self.assertRaises(MapAPIError) as caught:
                client.render(payload)
            self.assertEqual(caught.exception.status_code, 400)
            self.assertIn("width", str(caught.exception))

    def test_bad_credentials(self):
        with running_server() as (_, base_url):
            with subject.MapClient(base_url, api_key="wrong-key") as client:
                with self.assertRaises(MapAPIError) as caught:
                    client.render(config())
            self.assertEqual(caught.exception.status_code, 401)

    def test_transport_timeout_is_wrapped_and_timeout_is_passed(self):
        session = Mock(spec=requests.Session)
        session.post.side_effect = requests.Timeout("practice timeout")
        with subject.MapClient(timeout=0.25, session=session) as client:
            with self.assertRaises(MapAPIError) as caught:
                client.render(config())
        self.assertIsNone(caught.exception.status_code)
        self.assertEqual(session.post.call_args.kwargs["timeout"], 0.25)

    def test_503_preserves_status_and_error_body(self):
        response = requests.Response()
        response.status_code = 503
        response.url = "http://practice.invalid/map.png"
        response._content = b'{"error":{"message":"renderer unavailable"}}'
        response.headers["Content-Type"] = "application/json"
        session = Mock(spec=requests.Session)
        session.post.return_value = response
        with subject.MapClient(session=session) as client:
            with self.assertRaises(MapAPIError) as caught:
                client.render(config())
        self.assertEqual(caught.exception.status_code, 503)
        self.assertIn("renderer unavailable", str(caught.exception))
        self.assertEqual(session.post.call_count, 1)

    def test_success_with_wrong_media_type_is_rejected(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"not":"an image"}'
        response.headers["Content-Type"] = "application/json"
        session = Mock(spec=requests.Session)
        session.post.return_value = response
        with subject.MapClient(session=session) as client:
            with self.assertRaises(MapAPIError) as caught:
                client.render(config())
        self.assertEqual(caught.exception.status_code, 200)


class FileAndCommandTests(unittest.TestCase):
    def test_save_exact_bytes_and_create_parents(self):
        image = PNG_SIGNATURE + b"\x00\xff\x80\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new" / "nested" / "map.png"
            result = subject.save_image(image, path)
            self.assertIsInstance(result, Path)
            self.assertEqual(result, path)
            self.assertEqual(path.read_bytes(), image)

    def test_base_command_end_to_end(self):
        with running_server() as (_, base_url), tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "base.png"
            with patch.object(app, "MapClient", subject.MapClient), \
                 patch.object(app, "save_image", subject.save_image), redirect_stdout(io.StringIO()):
                status = app.main(["base", "--base-url", base_url, "--output", str(path)])
            self.assertEqual(status, 0)
            self.assertTrue(path.read_bytes().startswith(PNG_SIGNATURE))

    def test_http_failure_does_not_replace_existing_output(self):
        with running_server() as (_, base_url), tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "base.png"
            path.write_bytes(b"previous image")
            with patch.object(app, "MapClient", subject.MapClient), \
                 patch.object(app, "save_image", subject.save_image), redirect_stderr(io.StringIO()):
                status = app.main(["base", "--base-url", base_url, "--api-key", "wrong",
                                   "--output", str(path)])
            self.assertEqual(status, 1)
            self.assertEqual(path.read_bytes(), b"previous image")
